"""Esferas de GLP/GNL - verificacion preliminar ASME VIII Div 1/2.

Espesor minimo del casco esferico, columnas de apoyo, sismo.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi


@dataclass(frozen=True)
class EsferaGLPInput:
    D_m: float
    P_design_bar: float
    rho_liquido_kg_m3: float = 580.0   # propano
    fill_pct: float = 0.85
    S_allow_MPa: float = 138.0          # SA-516 Gr.70 a 38C
    E_joint: float = 1.0
    n_columnas: int = 8
    code: str = "US"


@dataclass(frozen=True)
class EsferaGLPResult:
    t_min_mm: float
    W_total_kN: float
    P_col_kN: float
    V_basal_kN: float
    code: str


def disenar_esfera(inp: EsferaGLPInput) -> EsferaGLPResult:
    if inp.code not in {"EU", "AU", "SG", "US", "CO"}:
        raise ValueError(f"code invalido: {inp.code}")
    P = inp.P_design_bar * 0.1   # MPa
    R = inp.D_m / 2.0 * 1000.0   # mm
    # ASME VIII Div 1, UG-32 esfera
    t_min = P * R / (2 * inp.S_allow_MPa * inp.E_joint - 0.2 * P)
    V = (4.0 / 3.0) * pi * (inp.D_m / 2.0) ** 3
    W_liq = V * inp.fill_pct * inp.rho_liquido_kg_m3 * 9.81 / 1000.0   # kN
    W_acero = pi * inp.D_m ** 2 * (t_min / 1000.0) * 7850 * 9.81 / 1000.0
    W_total = W_liq + W_acero
    P_col = W_total / inp.n_columnas
    Cs = 0.20 if inp.code in {"US", "CO"} else 0.15
    V_b = Cs * W_total
    return EsferaGLPResult(t_min, W_total, P_col, V_b, inp.code)


__all__ = ["EsferaGLPInput", "EsferaGLPResult", "disenar_esfera"]
