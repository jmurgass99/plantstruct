"""plantstruct.silo_buckling
===========================
Cálculo de pandeo meridional de láminas cilíndricas en silos y depósitos (EN 1993-1-6).
Consolidado desde SiloBucklingJm.
"""
from __future__ import annotations
import math
from typing import Literal

_C_MERIDIONAL = 0.605

QUALITY_Q = {
    "A": 40.0,
    "B": 25.0,
    "C": 16.0,
    "Q40": 40.0,
    "Q25": 25.0,
    "Q16": 16.0,
}


def meridional_critical_stress(E: float, t: float, r: float) -> float:
    """Tensión crítica elástica meridional sigma_cr = 0.605 * E * t / r."""
    if E <= 0.0:
        raise ValueError("E must be positive")
    if t <= 0.0:
        raise ValueError("t must be positive")
    if r <= 0.0:
        raise ValueError("r must be positive")
    return _C_MERIDIONAL * E * t / r


def imperfection_alpha(r: float, t: float, quality_class: str) -> float:
    """Factor de reducción por imperfecciones alpha (EN 1993-1-6 Anexo D)."""
    q_key = quality_class.upper() if isinstance(quality_class, str) else quality_class
    if q_key not in QUALITY_Q:
        raise ValueError(f"unknown quality_class {quality_class!r}; use one of {sorted(QUALITY_Q)}")
    if r <= 0.0 or t <= 0.0:
        raise ValueError("r and t must be positive")
    Q = QUALITY_Q[q_key]
    dwk_over_t = (1.0 / Q) * math.sqrt(r / t)
    return 0.62 / (1.0 + 1.91 * dwk_over_t ** 1.44)


def buckling_resistance(E: float, t: float, r: float, quality_class: str | None = None, alpha: float | None = None) -> dict[str, float]:
    """Resistencia característica de pandeo sigma_Rk = alpha * sigma_cr.

    Requiere quality_class o alpha explícito. No asume una calidad de fabricación por defecto
    (asumir 'B' en silencio infla la capacidad 1.513x respecto a calidad normal 'C').
    """
    sigma_cr = meridional_critical_stress(E=E, t=t, r=r)
    if alpha is None:
        if quality_class is None:
            raise ValueError(
                "quality_class or alpha must be provided explicitly (no default fabrication quality assumed; "
                f"use one of {sorted(QUALITY_Q)})"
            )
        alpha = imperfection_alpha(r=r, t=t, quality_class=quality_class)
    sigma_Rk = alpha * sigma_cr
    return {
        "sigma_cr": sigma_cr,
        "alpha": alpha,
        "sigma_Rk": sigma_Rk,
    }


__all__ = [
    "meridional_critical_stress",
    "imperfection_alpha",
    "buckling_resistance",
    "QUALITY_Q",
]
