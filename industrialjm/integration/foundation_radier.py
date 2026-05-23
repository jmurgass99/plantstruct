"""Bridge IndustrialJm -> FoundationDesignJm: radier (mat) bajo tanque/chimenea."""
from __future__ import annotations

import warnings
from dataclasses import dataclass


@dataclass(frozen=True)
class RadierInput:
    D_radier_m: float
    espesor_m: float
    Q_kN: float                # carga total tanque + liquido
    M_kNm: float = 0.0
    ks_kN_m3: float = 30000.0  # subgrade reaction


@dataclass(frozen=True)
class RadierResult:
    q_max_kPa: float
    q_min_kPa: float
    asentamiento_mm: float
    espesor_recomendado_m: float


def disenar_radier(inp: RadierInput) -> RadierResult:
    import math
    A = math.pi * (inp.D_radier_m / 2.0) ** 2
    I = math.pi * (inp.D_radier_m / 2.0) ** 4 / 4.0
    q_avg = inp.Q_kN / A
    q_max = q_avg + inp.M_kNm * (inp.D_radier_m / 2.0) / I
    q_min = q_avg - inp.M_kNm * (inp.D_radier_m / 2.0) / I
    s_mm = q_avg / inp.ks_kN_m3 * 1000.0
    try:
        from foundationdesignjm.analysis.mat_foundation import suggest_thickness
        t_rec = suggest_thickness(A, inp.Q_kN)
    except Exception:
        warnings.warn("FoundationDesignJm.mat_foundation no disponible - usando heuristica")
        t_rec = max(inp.espesor_m, 0.05 * inp.D_radier_m)
    return RadierResult(q_max, q_min, s_mm, t_rec)


__all__ = ["RadierInput", "RadierResult", "disenar_radier"]
