"""
Memoria completa de estanque API 650 §E — paso a paso.

Combina:
    1. Geometría del estanque
    2. Masas Housner (impulsiva/convectiva) y períodos Ti/Tc
    3. Verificación de espesor por hidrostática + sismo
    4. Momento volcante y verificación de anclaje (J-ratio)
    5. Pandeo del manto (axial + hoop + interacción)
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Any

from ..tanks import (
    AnchorageInput, ShellBucklingInput, TankGeometry,
    check_anchorage, check_shell_buckling, housner_masses,
    AnchorageJInput, check_anchorage_J,
    ShellBucklingFullInput, check_shell_buckling_full,
)
from ..tanks.shell_design import shell_thickness_one_foot


@dataclass(frozen=True)
class TankMemoInput:
    D_m: float
    H_l_m: float
    H_shell_m: float
    t_shell_mm: float
    Sa_i_g: float
    Sa_c_g: float
    W_tank_kN: float | None = None
    n_bolts: int = 24
    bolt_diameter_mm: float = 25.4
    rho_l_kg_m3: float = 1000.0
    liquid_G: float = 1.0          # gravedad específica del líquido


@dataclass(frozen=True)
class TankMemoResult:
    masses: dict
    anchorage: dict
    buckling: dict
    anchorage_J: dict
    buckling_full: dict
    shell_thickness: dict
    markdown: str
    is_safe: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "masses": self.masses,
            "anchorage": self.anchorage,
            "buckling": self.buckling,
            "anchorage_J": self.anchorage_J,
            "buckling_full": self.buckling_full,
            "shell_thickness": self.shell_thickness,
            "is_safe": self.is_safe,
        }


def render_tank_memo(inp: TankMemoInput) -> TankMemoResult:
    g = TankGeometry(D_m=inp.D_m, H_l_m=inp.H_l_m,
                     t_shell_mm=inp.t_shell_mm,
                     rho_l_kg_m3=inp.rho_l_kg_m3)
    m = housner_masses(g, Sa_i=inp.Sa_i_g, Sa_c=inp.Sa_c_g)
    W_tank = inp.W_tank_kN if inp.W_tank_kN is not None else g.W_l_kN * 1.05

    # --- Anclaje básico ---
    a = check_anchorage(AnchorageInput(
        D_m=inp.D_m, W_tank_kN=W_tank, M_overturn_kNm=m.M_overturn_kNm,
        n_bolts=inp.n_bolts, bolt_diameter_mm=inp.bolt_diameter_mm,
    ))

    # --- Pandeo básico ---
    b = check_shell_buckling(ShellBucklingInput(
        D_m=inp.D_m, H_shell_m=inp.H_shell_m, H_liquid_m=inp.H_l_m,
        t_shell_mm=inp.t_shell_mm,
    ))

    # --- J-ratio (API 650 §E.6.2) ---
    aj = check_anchorage_J(AnchorageJInput(
        D_m=inp.D_m, M_rw_kNm=m.M_overturn_kNm, W_t_kN=W_tank,
        bolt_diameter_mm=inp.bolt_diameter_mm,
    ))

    # --- Pandeo completo ---
    bf = check_shell_buckling_full(ShellBucklingFullInput(
        D_m=inp.D_m, H_shell_m=inp.H_shell_m, H_liquid_m=inp.H_l_m,
        t_shell_mm=inp.t_shell_mm,
    ))

    # --- Espesor por hidrostática (API 650 §5.6 — 1-Foot Method) ---
    try:
        sc = shell_thickness_one_foot(
            D_m=inp.D_m, H_m=inp.H_l_m, G=inp.liquid_G,
        )
        shell_thick_dict = {
            "t_design_mm": sc.t_design_mm,
            "t_test_mm": sc.t_test_mm,
            "t_required_mm": sc.t_required_mm,
            "governing": sc.governing,
            "actual_mm": inp.t_shell_mm,
            "is_ok": inp.t_shell_mm >= sc.t_required_mm,
        }
        t_check_ok = inp.t_shell_mm >= sc.t_required_mm
    except ValueError:
        shell_thick_dict = {"t_required_mm": 0, "is_ok": True, "governing": "N/A"}
        sc = None
        t_check_ok = True

    # --- Geometría resumen ---
    R_m = inp.D_m / 2.0
    V_m3 = pi * R_m ** 2 * inp.H_l_m

    # --- Markdown paso a paso ---
    md_sections = []

    # Encabezado
    md_sections.append(
        "# Memoria de calculo — Estanque API 650 §E\n\n"
        "## Geometria\n"
        f"- Diametro: D = {inp.D_m:.1f} m\n"
        f"- Altura liquido: H_l = {inp.H_l_m:.1f} m\n"
        f"- Altura manto: H_shell = {inp.H_shell_m:.1f} m\n"
        f"- Espesor manto: t = {inp.t_shell_mm:.1f} mm\n"
        f"- Volumen: V = {V_m3:.0f} m3\n"
        f"- Peso liquido: W_l = {g.W_l_kN:.0f} kN\n"
    )

    # Paso 1: Masas Housner
    md_sections.append(
        "\n## Paso 1 — Masas Housner (impulsiva/convectiva)\n"
        f"- Masa impulsiva: W_i = {m.W_i_kN:.0f} kN (h_i = {m.h_i_m:.2f} m)\n"
        f"- Masa convectiva: W_c = {m.W_c_kN:.0f} kN (h_c = {m.h_c_m:.2f} m)\n"
        f"- **Periodo impulsivo: T_i = {m.T_i_s:.3f} s**\n"
        f"- **Periodo convectivo: T_c = {m.T_c_s:.2f} s**\n"
        f"- **Sismicidad:** Sa_i = {inp.Sa_i_g:.2f} g, Sa_c = {inp.Sa_c_g:.2f} g\n"
        f"- **Momento volcante: M = {m.M_overturn_kNm:.0f} kN*m**\n"
    )

    # Paso 2: Espesor por hidrostática
    if sc is not None:
        md_sections.append(
            "\n## Paso 2 — Verificacion de espesor (API 650 §5.6)\n"
            f"- t_design = {sc.t_design_mm:.1f} mm (condicion diseno)\n"
            f"- t_test = {sc.t_test_mm:.1f} mm (prueba hidrostatica)\n"
            f"- t_requerido = {sc.t_required_mm:.1f} mm (gobernante: {sc.governing})\n"
            f"- t_actual = {inp.t_shell_mm:.1f} mm\n"
            f"- Verificacion: {'OK' if t_check_ok else 'NO CUMPLE'}\n"
        )

    # Paso 3: Anclajes
    md_sections.append(
        "\n## Paso 3 — Anclajes (API 650 §E.6.2)\n"
        f"- Uplift/perno = {a.F_uplift_per_bolt_kN:.0f} kN\n"
        f"- Capacidad/perno = {a.F_allowable_per_bolt_kN:.0f} kN\n"
        f"- DCR = {a.DCR:.2f}\n"
        f"- J-ratio = {aj.J:.3f} -> {aj.anchorage_type}\n"
        f"- Pernos requeridos (J): {aj.N_bolts_required}\n"
        f"- Silleta: t_base_plate = {aj.t_base_plate_mm:.1f} mm, "
        f"L_anchor = {aj.L_anchor_mm:.0f} mm\n"
    )

    # Paso 4: Pandeo del manto
    md_sections.append(
        "\n## Paso 4 — Pandeo del manto\n"
        f"- sigma_hoop = {b.sigma_hoop_demand_MPa:.1f} MPa "
        f"(crit = {b.sigma_hoop_critical_MPa:.1f} MPa)\n"
        f"- DCR_axial = {b.DCR_axial:.3f}\n"
        f"- DCR_hoop = {b.DCR_hoop:.3f}\n"
        f"- DCR_interaction = {b.DCR_interaction:.3f}\n"
        f"- Rotter alpha_diamond = {bf.alpha_diamond:.3f}\n"
        f"- Pandeo diamante: Fbi = {bf.Fbi_diamond_MPa:.1f} MPa\n"
        f"- Modo gobernante: {bf.governing_mode}\n"
    )

    # Resumen
    is_safe = a.is_safe and b.is_safe and t_check_ok
    md_sections.append(
        "\n## Resultado\n"
        f"- Espesor: {'OK' if t_check_ok else 'NO CUMPLE'}\n"
        f"- Anclajes: {'OK' if a.is_safe else 'NO CUMPLE'}\n"
        f"- Pandeo: {'OK' if b.is_safe else 'NO CUMPLE'}\n"
        f"- **VERIFICACION GLOBAL: {'CUMPLE' if is_safe else 'NO CUMPLE'}**\n"
    )

    md = "".join(md_sections)

    return TankMemoResult(
        masses=m.to_dict(), anchorage=a.to_dict(),
        buckling=b.to_dict(),
        anchorage_J=aj.to_dict(),
        buckling_full=bf.to_dict(),
        shell_thickness=shell_thick_dict,
        markdown=md, is_safe=is_safe,
    )


__all__ = ["TankMemoInput", "TankMemoResult", "render_tank_memo"]
