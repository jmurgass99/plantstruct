"""Bases de columna - diseno placa base por Salmon & Johnson.

Considera carga axial + momento, dimensiona placa, anclajes y rigidizadores.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class BaseColumnaInput:
    P_kN: float
    M_kNm: float = 0.0
    bf_mm: float = 200.0
    d_mm: float = 250.0
    fy_MPa: float = 250.0
    fc_MPa: float = 25.0
    fyb_MPa: float = 420.0
    n_anchors: int = 4
    db_anchor_mm: float = 25.0
    code: str = "US"


@dataclass(frozen=True)
class BaseColumnaResult:
    N_mm: float
    B_mm: float
    t_mm: float
    Tu_anchor_kN: float
    e_mm: float
    cumple: bool
    code: str


def disenar_base(inp: BaseColumnaInput) -> BaseColumnaResult:
    if inp.code not in {"EU", "AU", "SG", "US", "CO"}:
        raise ValueError(f"code invalido: {inp.code}")
    phi_c = 0.65 if inp.code == "US" else 0.6
    fp_max = phi_c * 0.85 * inp.fc_MPa
    # dimensionar segun P
    A_req = inp.P_kN * 1000 / fp_max
    side = sqrt(A_req)
    N = max(side, inp.d_mm + 100)
    B = max(side, inp.bf_mm + 100)
    e_mm = inp.M_kNm * 1000.0 / max(inp.P_kN, 1e-6)
    # caso pequena excentricidad
    if e_mm <= N / 6.0:
        fp = inp.P_kN * 1000 / (N * B) + 6 * inp.M_kNm * 1e6 / (B * N ** 2)
        m = (N - 0.95 * inp.d_mm) / 2.0
        n = (B - 0.8 * inp.bf_mm) / 2.0
        l_crit = max(m, n)
        t = l_crit * sqrt(2 * fp / (0.9 * inp.fy_MPa))
        Tu = 0.0
    else:
        # gran excentricidad - tension en anclajes
        Tu = max(inp.M_kNm * 1000.0 / (N - 100.0) - inp.P_kN / 2.0, 0.0)
        m = (N - 0.95 * inp.d_mm) / 2.0
        n = (B - 0.8 * inp.bf_mm) / 2.0
        l_crit = max(m, n)
        t = l_crit * sqrt(2 * fp_max / (0.9 * inp.fy_MPa))
    A_anchor = 3.141592 * inp.db_anchor_mm ** 2 / 4
    cap_anchor = inp.n_anchors / 2 * A_anchor * inp.fyb_MPa / 1000.0
    cumple = Tu <= cap_anchor and t > 0
    return BaseColumnaResult(N, B, t, Tu, e_mm, cumple, inp.code)


__all__ = ["BaseColumnaInput", "BaseColumnaResult", "disenar_base"]
