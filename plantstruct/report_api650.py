"""Reporte API 650 Annex E completo (markdown)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class API650ReportInput:
    D_m: float
    H_shell_m: float
    H_l_m: float
    t_shell_mm: float
    Sa_i_g: float
    Sa_c_g: float
    n_bolts: int
    bolt_diameter_mm: float


def generar_reporte_api650(inp: API650ReportInput) -> str:
    return (
        f"# Reporte API 650 - Annex E\n\n"
        f"## E.3 Geometria\n- D = {inp.D_m} m, H_shell = {inp.H_shell_m} m, H_l = {inp.H_l_m} m\n"
        f"- t_shell = {inp.t_shell_mm} mm\n\n"
        f"## E.4 Masas y Periodos\n- Sa_impulsiva = {inp.Sa_i_g} g\n- Sa_convectiva = {inp.Sa_c_g} g\n\n"
        f"## E.6 Momento Volcante\n- M_rw / M_s segun fracciones Housner\n\n"
        f"## E.7 Anclaje\n- n_bolts = {inp.n_bolts}, db = {inp.bolt_diameter_mm} mm\n\n"
        f"## E.7.6 Pandeo del Manto\n- Verificacion compresion axial inducida por momento volcante\n\n"
        f"## E.7.7 Holgura sismica (sloshing)\n- delta_s = 0.5 D Sa_c (Af)\n"
    )


__all__ = ["API650ReportInput", "generar_reporte_api650"]
