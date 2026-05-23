"""Pipe rack industrial - cargas + verificacion preliminar."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PipeRackInput:
    n_niveles: int
    L_tramo_m: float
    B_rack_m: float
    H_nivel_m: float = 5.0
    w_tuberias_kN_m: float = 8.0      # carga lineal tipica
    w_cable_tray_kN_m: float = 2.0
    pisarse_pct: float = 0.5
    incluir_thermal: bool = True
    code: str = "US"


@dataclass(frozen=True)
class PipeRackResult:
    W_total_kN: float
    W_por_columna_kN: float
    M_termico_kNm: float
    cortante_basal_kN: float
    code: str


def evaluar_pipe_rack(inp: PipeRackInput) -> PipeRackResult:
    if inp.code not in {"EU", "AU", "SG", "US", "CO"}:
        raise ValueError(f"code invalido: {inp.code}")
    w_nivel = (inp.w_tuberias_kN_m + inp.w_cable_tray_kN_m) * inp.B_rack_m
    W_total = w_nivel * inp.L_tramo_m * inp.n_niveles
    n_col = 4
    W_col = W_total / n_col
    M_th = 0.0
    if inp.incluir_thermal:
        # estimacion sencilla momento friccional por dilatacion
        M_th = 0.3 * inp.w_tuberias_kN_m * inp.L_tramo_m * inp.H_nivel_m
    Cs = 0.15 if inp.code in {"US", "CO"} else 0.10
    V_b = Cs * W_total
    return PipeRackResult(W_total, W_col, M_th, V_b, inp.code)


__all__ = ["PipeRackInput", "PipeRackResult", "evaluar_pipe_rack"]
