"""
Pandeo del manto de estanques cilíndricos verticales — API 650 §5.10
y modelo Timoshenko-Donnell para interacción axial + flexión circunferencial.

Esfuerzos:
    σ_axial = (W_tank + 0.4·γ·H_l·D)/(π·D·t)     [API 650 §3.4.2]
    σ_hoop = γ·H_l·D / (2·t)                       (presión hidrostática)
    σ_cr_axial = 0.6·E·t/R · α_imp                 [API 650 §5.10.3]
    σ_cr_hoop = 0.92·E·(t/R)·(R/L)^(0.5)·factor    [DASt 017]
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Any


@dataclass(frozen=True)
class ShellBucklingInput:
    D_m: float
    H_shell_m: float
    H_liquid_m: float
    t_shell_mm: float
    sigma_axial_imposed_MPa: float = 0.0   # tributario de techo etc.
    E_MPa: float = 200_000.0
    gamma_l_kN_m3: float = 9.81            # peso específico líquido


@dataclass(frozen=True)
class ShellBucklingResult:
    sigma_axial_demand_MPa: float
    sigma_hoop_demand_MPa: float
    sigma_axial_critical_MPa: float
    sigma_hoop_critical_MPa: float
    DCR_axial: float
    DCR_hoop: float
    DCR_interaction: float
    is_safe: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "sigma_axial_demand_MPa": self.sigma_axial_demand_MPa,
            "sigma_hoop_demand_MPa": self.sigma_hoop_demand_MPa,
            "sigma_axial_critical_MPa": self.sigma_axial_critical_MPa,
            "sigma_hoop_critical_MPa": self.sigma_hoop_critical_MPa,
            "DCR_axial": self.DCR_axial,
            "DCR_hoop": self.DCR_hoop,
            "DCR_interaction": self.DCR_interaction,
            "is_safe": self.is_safe,
        }


def check_shell_buckling(inp: ShellBucklingInput,
                          alpha_imperfection: float = 0.6
                          ) -> ShellBucklingResult:
    R_mm = inp.D_m * 1000.0 / 2.0
    t = inp.t_shell_mm
    H_l_mm = inp.H_liquid_m * 1000.0

    # Presión hidrostática y esfuerzos
    sigma_hoop = inp.gamma_l_kN_m3 * inp.H_liquid_m * inp.D_m / (
        2.0 * t / 1000.0
    ) / 1000.0  # MPa
    sigma_axial = inp.sigma_axial_imposed_MPa

    # Esfuerzos críticos
    sigma_cr_ax = alpha_imperfection * inp.E_MPa * t / R_mm
    # Hoop: Donnell para tubo corto a presión externa
    L_mm = inp.H_shell_m * 1000.0
    sigma_cr_hoop = 0.92 * inp.E_MPa * (t / R_mm) ** 1.5 * (R_mm / max(L_mm, 1.0))

    DCR_ax = sigma_axial / sigma_cr_ax if sigma_cr_ax > 0 else float("inf")
    DCR_hoop = sigma_hoop / sigma_cr_hoop if sigma_cr_hoop > 0 else float("inf")
    # Interacción cuadrática (Donnell)
    DCR_inter = DCR_ax ** 2 + DCR_hoop ** 2

    is_safe = DCR_ax <= 1.0 and DCR_hoop <= 1.0 and DCR_inter <= 1.0

    return ShellBucklingResult(
        sigma_axial_demand_MPa=sigma_axial,
        sigma_hoop_demand_MPa=sigma_hoop,
        sigma_axial_critical_MPa=sigma_cr_ax,
        sigma_hoop_critical_MPa=sigma_cr_hoop,
        DCR_axial=DCR_ax, DCR_hoop=DCR_hoop, DCR_interaction=DCR_inter,
        is_safe=is_safe,
    )



# ===========================================================================
# Pandeo completo: axial + circunferencial + flexión + interacción + Rotter
# ===========================================================================

@dataclass(frozen=True)
class ShellBucklingFullInput:
    """Entrada para verificación completa de pandeo del manto.

    Args:
        D_m: diámetro del estanque [m].
        H_shell_m: altura total del manto [m].
        H_liquid_m: altura del líquido [m].
        t_shell_mm: espesor del manto [mm].
        sigma_axial_imposed_MPa: esfuerzo axial impuesto (techo, cargas externas) [MPa].
        sigma_bending_MPa: esfuerzo de flexión por momento volcante sísmico [MPa].
        E_MPa: módulo de elasticidad del acero [MPa].
        gamma_l_kN_m3: peso específico del líquido [kN/m³].
        alpha_imperfection: factor de imperfección API 650 §5.10.3 (0.6 típico).
    """
    D_m: float
    H_shell_m: float
    H_liquid_m: float
    t_shell_mm: float
    sigma_axial_imposed_MPa: float = 0.0
    sigma_bending_MPa: float = 0.0
    E_MPa: float = 200_000.0
    gamma_l_kN_m3: float = 9.81
    alpha_imperfection: float = 0.6


@dataclass(frozen=True)
class ShellBucklingFullResult:
    """Resultado completo de pandeo del manto."""
    # Demandas
    sigma_axial_demand_MPa: float
    sigma_hoop_demand_MPa: float
    sigma_bending_demand_MPa: float

    # Capacidades críticas
    Fbi_axial_MPa: float          # pandeo axial API 650 §E.6.2.1.1
    Fc_hoop_MPa: float            # pandeo circunferencial (membrana)
    Fb_bending_MPa: float         # pandeo por flexión (esbeltos)

    # Ratios individuales
    DCR_axial: float
    DCR_hoop: float
    DCR_bending: float

    #: DCR axial si gobernase el knockdown de Rotter en vez del factor de
    #: imperfección de entrada. NO interviene en `is_safe`; se publica porque el
    #: resultado ya traía las dos capacidades y ninguna pista de cuál mandaba.
    #: La brecha es 0.6·(1 + 0.005·R/t): 2.4x a R/t=600, 8.1x a R/t=2500.
    DCR_axial_diamond: float

    # Interacción cuadrática: (fa/Fa)² + (fb/Fb)² ≤ 1.0
    DCR_interaction: float

    # Rotter diamond knockdown
    alpha_diamond: float
    Fbi_diamond_MPa: float

    is_safe: bool
    governing_mode: str           # "axial" | "hoop" | "bending" | "interaction"

    #: Qué capacidad axial sostiene el veredicto. Publicar dos capacidades y un
    #: solo `is_safe` sin decir cuál gobierna es lo que hacía invisible un
    #: factor de hasta 8.
    axial_basis: str = "API650_alpha_imperfection"

    def to_dict(self) -> dict[str, Any]:
        return {
            "sigma_axial_demand_MPa": self.sigma_axial_demand_MPa,
            "sigma_hoop_demand_MPa": self.sigma_hoop_demand_MPa,
            "sigma_bending_demand_MPa": self.sigma_bending_demand_MPa,
            "Fbi_axial_MPa": self.Fbi_axial_MPa,
            "Fc_hoop_MPa": self.Fc_hoop_MPa,
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


def _validar_geometria(D_m: float, t_shell_mm: float, quien: str) -> None:
    """Rechaza geometrías imposibles antes de que la aritmética las disfrace.

    Con espesor negativo, ``(t/R)**1.5`` devuelve un COMPLEJO y la comparación
    ``Fc_hoop > 0`` estalla en ``TypeError: '>' not supported between instances
    of 'complex' and 'int'``: un error real, pero que no dice nada del problema
    y aparece cincuenta líneas más abajo del sitio donde se puede arreglar.
    Un espesor o un diámetro no positivos son datos malos (una extracción mal
    parseada, unas unidades equivocadas), y merecen decirlo así.
    """
    if not D_m > 0:
        raise ValueError(f"{quien}: D_m={D_m:g} m debe ser > 0")
    if not t_shell_mm > 0:
        raise ValueError(
            f"{quien}: t_shell_mm={t_shell_mm:g} mm debe ser > 0. Un espesor no "
            "positivo no es un manto delgado, es un dato mal leído."
        )


def _rotter_diamond_knockdown(R_mm: float, t_mm: float) -> float:
    """Factor knockdown de Rotter para pandeo diamante (imperfecciones).

    Rotter (1997): α = 1 / (1 + 0.005 · R/t)
    Para R/t grandes → α tiende a 0 (muy sensible a imperfecciones).
    Para R/t pequeños → α tiende a ~1.
    """
    Rt = R_mm / t_mm if t_mm > 0 else float("inf")
    return 1.0 / (1.0 + 0.005 * Rt)


def check_shell_buckling_full(inp: ShellBucklingFullInput
                               ) -> ShellBucklingFullResult:
    """Verificación completa de pandeo del manto.

    Modos:
        1. Pandeo axial (API 650 §E.6.2.1.1): Fbi = α·E·t/R
        2. Pandeo circunferencial (membrana): Fc = (t/R)·E para membrana
        3. Pandeo por flexión: Fb = (t²·E)/(R·H) para esbeltos
        4. Interacción: (fa/Fa)² + (fb/Fb)² ≤ 1.0
        5. Pandeo diamante (Rotter): factor knockdown

    QUÉ CAPACIDAD SOSTIENE EL VEREDICTO
    -----------------------------------
    `is_safe`, `DCR_axial` y `governing_mode` van por la ruta 1, con el
    `alpha_imperfection` de entrada (0.6 por defecto).  El resultado publica
    ADEMÁS `Fbi_diamond_MPa` (ruta 5) y ahora `DCR_axial_diamond`, porque las dos
    capacidades convivían en la salida sin ninguna pista de cuál mandaba.  La
    brecha entre ambas es la forma cerrada ``α·(1 + 0.005·R/t)``, que con
    α = 0.6 da 2.4x a R/t = 600 y 8.1x a R/t = 2500 — crece con la esbeltez, no
    es una constante.  Medido en un tanque de 30 m × 6 mm: DCR publicado 0.104,
    DCR por Rotter 0.844.

    Cuál debe gobernar es una decisión de norma y NO se toma aquí: se deja donde
    estaba y se hace visible la otra.  `axial_basis` lo declara en la salida.
    """
    _validar_geometria(inp.D_m, inp.t_shell_mm, "check_shell_buckling_full")
    R_mm = inp.D_m * 1000.0 / 2.0
    t = inp.t_shell_mm
    H_l_mm = inp.H_liquid_m * 1000.0
    L_mm = inp.H_shell_m * 1000.0
    E = inp.E_MPa

    # --- Demandas ---
    sigma_axial = inp.sigma_axial_imposed_MPa
    sigma_bending = inp.sigma_bending_MPa
    # Presión hidrostática → hoop
    sigma_hoop = (inp.gamma_l_kN_m3 * inp.H_liquid_m * inp.D_m
                  / (2.0 * t / 1000.0) / 1000.0)  # MPa

    # --- Capacidades críticas ---
    # 1. Pandeo axial: Fbi = α_imp · E · t / R  (API 650 §E.6.2.1.1)
    Fbi_axial = inp.alpha_imperfection * E * t / R_mm

    # 2. Pandeo circunferencial (membrana Donnell):
    #    Fc = 0.92 · E · (t/R)^1.5 · (R/L)
    Fc_hoop = 0.92 * E * (t / R_mm) ** 1.5 * (R_mm / max(L_mm, 1.0))

    # 3. Pandeo por flexión (para mantos esbeltos H/D >> 1):
    #    Fb = E · t² / (R · H_shell)    [Timoshenko aprox.]
    Fb_bending = E * t ** 2 / (R_mm * max(L_mm, 1.0))

    # --- DCR individuales ---
    # Capacidad <= 0 -> infinito, NO cero. Cero es el valor de "sobra margen": un
    # manto sin capacidad salía por la API como seguro (medido: con E=0 los tres
    # DCR daban 0.0 e is_safe True, con 134.9 MPa de demanda circunferencial).
    # `check_shell_buckling`, veinte líneas más arriba en este mismo fichero, ya
    # usaba float("inf") para la misma magnitud; esto solo restaura la coherencia.
    DCR_axial = sigma_axial / Fbi_axial if Fbi_axial > 0 else float("inf")
    DCR_hoop = sigma_hoop / Fc_hoop if Fc_hoop > 0 else float("inf")
    DCR_bending = sigma_bending / Fb_bending if Fb_bending > 0 else float("inf")

    # --- Interacción cuadrática: (fa/Fa)² + (fb/Fb)² ≤ 1.0 ---
    DCR_interaction = DCR_axial ** 2 + DCR_bending ** 2

    # --- Rotter diamond knockdown ---
    alpha_diamond = _rotter_diamond_knockdown(R_mm, t)
    Fbi_diamond = alpha_diamond * E * t / R_mm
    # El resultado ya publicaba esta capacidad sin decir qué DCR implicaba, así
    # que la brecha contra la ruta API 650 solo se veía recalculándola a mano.
    DCR_axial_diamond = (sigma_axial / Fbi_diamond if Fbi_diamond > 0
                         else float("inf"))

    # --- Governing mode ---
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
        Fc_hoop_MPa=Fc_hoop,
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
    )


__all__ = [
    "ShellBucklingInput", "ShellBucklingResult", "check_shell_buckling",
    "ShellBucklingFullInput", "ShellBucklingFullResult", "check_shell_buckling_full",
]
