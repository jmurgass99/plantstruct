"""
Silos cilíndricos — EN 1991-4:2006 §5.

Calcula presiones de descarga (Janssen) y de llenado para silos
cilíndricos esbeltos (h/dc > 1.0 categoría AAC).
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, pi
from typing import Any


@dataclass(frozen=True)
class SiloInput:
    diameter_m: float
    height_filled_m: float
    bulk_density_kN_m3: float        # γ del material
    friction_angle_wall_deg: float = 25.0   # φ_w (granular vs metal liso)
    K_lateral: float = 0.40                  # K_v (Eurocode default trigo)


@dataclass(frozen=True)
class SiloResult:
    z_max_m: float
    p_horizontal_max_kPa: float       # ph,max
    p_vertical_max_kPa: float         # pv,max
    p_wall_friction_max_kPa: float    # pw,max (Janssen)


def janssen_pressures(inp: SiloInput) -> SiloResult:
    """Presiones de llenado según EN 1991-4 §5.2.1 (Janssen).

        z_o = D/(4·μ·K)                      profundidad característica
        p_h(z) = γ·K·z_o·(1 − exp(−z/z_o))   = γ·D/(4·μ)·(1 − exp(−z/z_o))
        p_v(z) = p_h(z)/K
        p_w(z) = μ·p_h(z)

    Hasta 2026-11-01 la presión horizontal se calculaba como γ·z_o·(1 − e^(−z/z_o)),
    sin el factor K: era la presión VERTICAL (1/K ≈ 1,9–2,5 veces mayor), y p_v y
    p_w arrastraban el error. `ec1_silos.janssen_pressure` siempre fue correcta.
    """
    from math import tan, radians
    D = inp.diameter_m
    K = inp.K_lateral
    mu = tan(radians(inp.friction_angle_wall_deg))
    gamma = inp.bulk_density_kN_m3
    z = inp.height_filled_m

    z_o = D / (4.0 * mu * K)
    ph = gamma * K * z_o * (1.0 - exp(-z / z_o))
    pv = ph / K
    pw = mu * ph

    return SiloResult(
        z_max_m=z, p_horizontal_max_kPa=ph,
        p_vertical_max_kPa=pv, p_wall_friction_max_kPa=pw,
    )


__all__ = ["SiloInput", "SiloResult", "janssen_pressures"]
