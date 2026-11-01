"""
Pandeo del manto de estanques cilíndricos verticales — API 650 §5.10 / §E.6.2.2
y comprobación de la tracción anular hidrostática.

Esfuerzos:
    σ_axial  = compresión longitudinal impuesta (techo, cargas, momento sísmico)   [entrada]
    σ_hoop   = γ·H_l·D/(2·t)   tracción anular por la presión hidrostática
    σ_cr,ax  = α·E·t/R        pandeo axial, α = 0,6 (API 650 §5.10.3)
    σ_b      = flexión por momento volcante (solo en la verificación completa)   [entrada]
    F_C      = pandeo admisible sísmico API 650 §E.6.2.2.3 (estabilizado por presión interna)
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class ShellBucklingInput:
    D_m: float
    H_shell_m: float
    H_liquid_m: float
    t_shell_mm: float
    sigma_axial_imposed_MPa: float = 0.0   # tributario de techo, momento sísmico, etc.
    E_MPa: float = 200_000.0
    gamma_l_kN_m3: float = 9.81            # peso específico líquido
    Sd_MPa: float = 160.0                  # tensión admisible de diseño del manto (A36: 160 MPa)


@dataclass(frozen=True)
class ShellBucklingResult:
    sigma_axial_demand_MPa: float
    sigma_hoop_demand_MPa: float
    sigma_axial_critical_MPa: float
    sigma_hoop_allowable_MPa: float   # S_d: la tracción anular se compara con la admisible
    DCR_axial: float
    DCR_hoop: float                   # utilización a TRACCIÓN anular
    DCR_interaction: float            # = DCR_axial (la tracción anular no interacciona desfavorablemente)
    is_safe: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "sigma_axial_demand_MPa": self.sigma_axial_demand_MPa,
            "sigma_hoop_demand_MPa": self.sigma_hoop_demand_MPa,
            "sigma_axial_critical_MPa": self.sigma_axial_critical_MPa,
            "sigma_hoop_allowable_MPa": self.sigma_hoop_allowable_MPa,
            "DCR_axial": self.DCR_axial,
            "DCR_hoop": self.DCR_hoop,
            "DCR_interaction": self.DCR_interaction,
            "is_safe": self.is_safe,
        }


def _hoop_stress_MPa(gamma_l_kN_m3: float, H_liquid_m: float, D_m: float, t_mm: float) -> float:
    return gamma_l_kN_m3 * H_liquid_m * D_m / (2.0 * t_mm / 1000.0) / 1000.0


def api650_allowable_shell_buckling_stress_fc(
    D_m: float,
    t_mm: float,
    H_liquid_m: float,
    Fy_MPa: float,
    G: float = 1.0,
) -> float:
    """Esfuerzo admisible de compresión longitudinal F_C según API 650 §E.6.2.2.3 (unidades SI).

    Parámetro de esbeltez hidrostática:
        g_hd = G · H · D² / t²   (con H y D en m, t en mm)
      - Si g_hd >= 44:  F_C = 83 · t / D <= 0.5 · F_ty
      - Si g_hd <  44:  F_C = 83 · t / (2.5 · D) + 7.5 · sqrt(G · H) <= 0.5 · F_ty
    """
    _validar_geometria(D_m, t_mm, "api650_allowable_shell_buckling_stress_fc")
    if Fy_MPa <= 0:
        raise ValueError("Fy_MPa debe ser > 0")
    if H_liquid_m < 0 or G <= 0:
        raise ValueError("H_liquid_m >= 0 y G > 0 requeridos")
    ghd = G * H_liquid_m * (D_m ** 2) / (t_mm ** 2)
    if ghd >= 44.0:
        fc = 83.0 * t_mm / D_m
    else:
        fc = 83.0 * t_mm / (2.5 * D_m) + 7.5 * math.sqrt(G * H_liquid_m)
    return min(fc, 0.5 * Fy_MPa)


def check_shell_buckling(inp: ShellBucklingInput,
                          alpha_imperfection: float = 0.6
                          ) -> ShellBucklingResult:
    """Pandeo axial con α de imperfecciones + tracción anular frente a S_d."""
    _validar_geometria(inp.D_m, inp.t_shell_mm, "check_shell_buckling")
    R_mm = inp.D_m * 1000.0 / 2.0
    t = inp.t_shell_mm

    sigma_hoop = _hoop_stress_MPa(inp.gamma_l_kN_m3, inp.H_liquid_m, inp.D_m, t)
    sigma_axial = inp.sigma_axial_imposed_MPa

    sigma_cr_ax = alpha_imperfection * inp.E_MPa * t / R_mm

    DCR_ax = sigma_axial / sigma_cr_ax if sigma_cr_ax > 0 else float("inf")
    DCR_hoop = sigma_hoop / inp.Sd_MPa if inp.Sd_MPa > 0 else float("inf")
    DCR_inter = DCR_ax

    is_safe = DCR_ax <= 1.0 and DCR_hoop <= 1.0

    return ShellBucklingResult(
        sigma_axial_demand_MPa=sigma_axial,
        sigma_hoop_demand_MPa=sigma_hoop,
        sigma_axial_critical_MPa=sigma_cr_ax,
        sigma_hoop_allowable_MPa=inp.Sd_MPa,
        DCR_axial=DCR_ax, DCR_hoop=DCR_hoop, DCR_interaction=DCR_inter,
        is_safe=is_safe,
    )


# ===========================================================================
# Verificación completa: axial + tracción anular + flexión + interacción + Rotter
# ===========================================================================

@dataclass(frozen=True)
class ShellBucklingFullInput:
    """Entrada para verificación completa de pandeo del manto."""
    D_m: float
    H_shell_m: float
    H_liquid_m: float
    t_shell_mm: float
    sigma_axial_imposed_MPa: float = 0.0
    sigma_bending_MPa: float = 0.0
    E_MPa: float = 200_000.0
    gamma_l_kN_m3: float = 9.81
    alpha_imperfection: float = 0.6
    Sd_MPa: float = 160.0
    Fy_MPa: float | None = None


@dataclass(frozen=True)
class ShellBucklingFullResult:
    """Resultado completo de pandeo del manto."""
    sigma_axial_demand_MPa: float
    sigma_hoop_demand_MPa: float
    sigma_bending_demand_MPa: float

    Fbi_axial_MPa: float
    Fh_hoop_allowable_MPa: float
    Fb_bending_MPa: float

    DCR_axial: float
    DCR_hoop: float
    DCR_bending: float
    DCR_axial_diamond: float
    DCR_interaction: float

    alpha_diamond: float
    Fbi_diamond_MPa: float

    is_safe: bool
    governing_mode: str

    axial_basis: str = "API650_alpha_imperfection"
    Fc_api650_e6223_MPa: float | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "sigma_axial_demand_MPa": self.sigma_axial_demand_MPa,
            "sigma_hoop_demand_MPa": self.sigma_hoop_demand_MPa,
            "sigma_bending_demand_MPa": self.sigma_bending_demand_MPa,
            "Fbi_axial_MPa": self.Fbi_axial_MPa,
            "Fh_hoop_allowable_MPa": self.Fh_hoop_allowable_MPa,
            "Fb_bending_MPa": self.Fb_bending_MPa,
            "DCR_axial": self.DCR_axial,
            "DCR_hoop": self.DCR_hoop,
            "DCR_bending": self.DCR_bending,
            "DCR_axial_diamond": self.DCR_axial_diamond,
            "DCR_interaction": self.DCR_interaction,
            "alpha_diamond": self.alpha_diamond,
            "Fbi_diamond_MPa": self.Fbi_diamond_MPa,
            "is_safe": self.is_safe,
            "governing_mode": self.governing_mode,
            "axial_basis": self.axial_basis,
        }
        if self.Fc_api650_e6223_MPa is not None:
            d["Fc_api650_e6223_MPa"] = self.Fc_api650_e6223_MPa
        return d


def _validar_geometria(D_m: float, t_shell_mm: float, quien: str) -> None:
    if not D_m > 0:
        raise ValueError(f"{quien}: D_m={D_m:g} m debe ser > 0")
    if not t_shell_mm > 0:
        raise ValueError(
            f"{quien}: t_shell_mm={t_shell_mm:g} mm debe ser > 0. Un espesor no "
            "positivo no es un manto delgado, es un dato mal leído."
        )


def _rotter_diamond_knockdown(R_mm: float, t_mm: float) -> float:
    Rt = R_mm / t_mm if t_mm > 0 else float("inf")
    return 1.0 / (1.0 + 0.005 * Rt)


def check_shell_buckling_full(inp: ShellBucklingFullInput
                               ) -> ShellBucklingFullResult:
    """Verificación completa del manto."""
    _validar_geometria(inp.D_m, inp.t_shell_mm, "check_shell_buckling_full")
    R_mm = inp.D_m * 1000.0 / 2.0
    t = inp.t_shell_mm
    L_mm = inp.H_shell_m * 1000.0
    E = inp.E_MPa

    sigma_axial = inp.sigma_axial_imposed_MPa
    sigma_bending = inp.sigma_bending_MPa
    sigma_hoop = _hoop_stress_MPa(inp.gamma_l_kN_m3, inp.H_liquid_m, inp.D_m, t)

    Fbi_axial = inp.alpha_imperfection * E * t / R_mm
    Fh_hoop = inp.Sd_MPa
    Fb_bending = E * t ** 2 / (R_mm * max(L_mm, 1.0))

    DCR_axial = sigma_axial / Fbi_axial if Fbi_axial > 0 else float("inf")
    DCR_hoop = sigma_hoop / Fh_hoop if Fh_hoop > 0 else float("inf")
    DCR_bending = sigma_bending / Fb_bending if Fb_bending > 0 else float("inf")

    DCR_interaction = DCR_axial ** 2 + DCR_bending ** 2

    alpha_diamond = _rotter_diamond_knockdown(R_mm, t)
    Fbi_diamond = alpha_diamond * E * t / R_mm
    DCR_axial_diamond = (sigma_axial / Fbi_diamond if Fbi_diamond > 0
                         else float("inf"))

    fc_e6223 = None
    if inp.Fy_MPa is not None and inp.Fy_MPa > 0 and inp.H_liquid_m >= 0:
        G_rel = max(inp.gamma_l_kN_m3 / 9.81, 0.1)
        fc_e6223 = api650_allowable_shell_buckling_stress_fc(
            inp.D_m, t, inp.H_liquid_m, inp.Fy_MPa, G=G_rel
        )

    dcr_max = max(DCR_axial, DCR_hoop, DCR_bending)
    if DCR_interaction > 1.0:
        governing = "interaction"
    elif dcr_max == DCR_axial:
        governing = "axial"
    elif dcr_max == DCR_hoop:
        governing = "hoop"
    else:
        governing = "bending"

    is_safe = (DCR_axial <= 1.0 and DCR_hoop <= 1.0
               and DCR_bending <= 1.0 and DCR_interaction <= 1.0)

    return ShellBucklingFullResult(
        sigma_axial_demand_MPa=sigma_axial,
        sigma_hoop_demand_MPa=sigma_hoop,
        sigma_bending_demand_MPa=sigma_bending,
        Fbi_axial_MPa=Fbi_axial,
        Fh_hoop_allowable_MPa=Fh_hoop,
        Fb_bending_MPa=Fb_bending,
        DCR_axial=DCR_axial,
        DCR_hoop=DCR_hoop,
        DCR_bending=DCR_bending,
        DCR_axial_diamond=DCR_axial_diamond,
        DCR_interaction=DCR_interaction,
        alpha_diamond=alpha_diamond,
        Fbi_diamond_MPa=Fbi_diamond,
        is_safe=is_safe,
        governing_mode=governing,
        Fc_api650_e6223_MPa=fc_e6223,
    )


__all__ = [
    "ShellBucklingInput", "ShellBucklingResult", "check_shell_buckling",
    "ShellBucklingFullInput", "ShellBucklingFullResult", "check_shell_buckling_full",
    "api650_allowable_shell_buckling_stress_fc",
]
