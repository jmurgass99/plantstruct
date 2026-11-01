"""
Pandeo del manto de estanques cilíndricos verticales — API 650 §5.10 / §E.6.2.2
y comprobación de la tracción anular hidrostática.

Esfuerzos:
    σ_axial  = compresión longitudinal impuesta (techo, cargas, momento sísmico)   [entrada]
    σ_hoop   = γ·H_l·D/(2·t)   tracción anular por la presión hidrostática
    σ_cr,ax  = α·E·t/R        pandeo axial, α = 0,6 (API 650 §5.10.3)
    σ_b      = flexión por momento volcante (solo en la verificación completa)   [entrada]

QUÉ ES CADA COMPROBACIÓN
------------------------
La tracción anular NO pandea: se compara con la tensión admisible del material
S_d (API 650 Tabla 5-2a; para la combinación sísmica §E.6.1.4 admite 1,333·S_d,
que el usuario pasa en ``Sd_MPa``). Hasta 2026-11-01 ambas funciones comparaban
esa tracción con la tensión crítica de Donnell a presión EXTERIOR
(0,92·E·(t/R)^1,5·R/L, del orden de 2–4 MPa en un tanque de 20 m), de modo que
cualquier tanque lleno salía con DCR_hoop de 40 a 150 y «NO CUMPLE» por pandeo.
El pandeo circunferencial por vacío sí existe y lo cubre
``plantstruct.external_pressure`` (ASME VIII UG-28 / API 650 §5.9.7).
"""
from __future__ import annotations

from dataclasses import dataclass
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
        Sd_MPa: tensión admisible del manto para la tracción anular [MPa].
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
    Sd_MPa: float = 160.0


@dataclass(frozen=True)
class ShellBucklingFullResult:
    """Resultado completo de pandeo del manto."""
    # Demandas
    sigma_axial_demand_MPa: float
    sigma_hoop_demand_MPa: float
    sigma_bending_demand_MPa: float

    # Capacidades
    Fbi_axial_MPa: float          # pandeo axial API 650 §E.6.2.2.3 (α·E·t/R)
    Fh_hoop_allowable_MPa: float  # tracción anular admisible S_d
    Fb_bending_MPa: float         # pandeo por flexión (esbeltos)

    # Ratios individuales
    DCR_axial: float
    DCR_hoop: float               # utilización a TRACCIÓN anular
    DCR_bending: float

    #: DCR axial si gobernase el knockdown de Rotter en vez del factor de
    #: imperfección de entrada. NO interviene en `is_safe`; se publica porque el
    #: resultado ya traía las dos capacidades y ninguna pista de cuál mandaba.
    #: La brecha es 0.6·(1 + 0.005·R/t): 2.4x a R/t=600, 8.1x a R/t=2500.
    DCR_axial_diamond: float

    # Interacción cuadrática de compresiones: (fa/Fa)² + (fb/Fb)² ≤ 1.0
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


def _validar_geometria(D_m: float, t_shell_mm: float, quien: str) -> None:
    """Rechaza geometrías imposibles antes de que la aritmética las disfrace.

    Con espesor negativo, ``(t/R)**1.5`` devuelve un COMPLEJO y la comparación
    ``> 0`` estalla en ``TypeError`` cincuenta líneas más abajo del sitio donde se
    puede arreglar. Un espesor o un diámetro no positivos son datos malos (una
    extracción mal parseada, unas unidades equivocadas), y merecen decirlo así.
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
    """Verificación completa del manto.

    Modos:
        1. Pandeo axial (API 650 §E.6.2.2.3 simplificado): Fbi = α·E·t/R
        2. Tracción anular hidrostática: σ_hoop ≤ S_d  (no es pandeo)
        3. Pandeo por flexión: Fb = (t²·E)/(R·H) para esbeltos
        4. Interacción de compresiones: (fa/Fa)² + (fb/Fb)² ≤ 1.0
        5. Pandeo diamante (Rotter): factor knockdown, publicado como DCR_axial_diamond

    QUÉ CAPACIDAD SOSTIENE EL VEREDICTO
    -----------------------------------
    `is_safe`, `DCR_axial` y `governing_mode` van por la ruta 1, con el
    `alpha_imperfection` de entrada (0.6 por defecto).  El resultado publica
    ADEMÁS `Fbi_diamond_MPa` (ruta 5) y `DCR_axial_diamond`, porque las dos
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
    L_mm = inp.H_shell_m * 1000.0
    E = inp.E_MPa

    # --- Demandas ---
    sigma_axial = inp.sigma_axial_imposed_MPa
    sigma_bending = inp.sigma_bending_MPa
    sigma_hoop = _hoop_stress_MPa(inp.gamma_l_kN_m3, inp.H_liquid_m, inp.D_m, t)

    # --- Capacidades ---
    # 1. Pandeo axial: Fbi = α_imp · E · t / R
    Fbi_axial = inp.alpha_imperfection * E * t / R_mm
    # 2. Tracción anular: admisible S_d
    Fh_hoop = inp.Sd_MPa
    # 3. Pandeo por flexión (mantos esbeltos H/D >> 1): Fb = E·t²/(R·H_shell) [Timoshenko aprox.]
    Fb_bending = E * t ** 2 / (R_mm * max(L_mm, 1.0))

    # --- DCR individuales ---
    # Capacidad <= 0 -> infinito, NO cero. Cero es el valor de "sobra margen": un
    # manto sin capacidad salía por la API como seguro (medido: con E=0 los DCR
    # daban 0.0 e is_safe True, con 134.9 MPa de demanda circunferencial).
    DCR_axial = sigma_axial / Fbi_axial if Fbi_axial > 0 else float("inf")
    DCR_hoop = sigma_hoop / Fh_hoop if Fh_hoop > 0 else float("inf")
    DCR_bending = sigma_bending / Fb_bending if Fb_bending > 0 else float("inf")

    # --- Interacción cuadrática de compresiones: (fa/Fa)² + (fb/Fb)² ≤ 1.0 ---
    DCR_interaction = DCR_axial ** 2 + DCR_bending ** 2

    # --- Rotter diamond knockdown ---
    alpha_diamond = _rotter_diamond_knockdown(R_mm, t)
    Fbi_diamond = alpha_diamond * E * t / R_mm
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
    )


__all__ = [
    "ShellBucklingInput", "ShellBucklingResult", "check_shell_buckling",
    "ShellBucklingFullInput", "ShellBucklingFullResult", "check_shell_buckling_full",
]
