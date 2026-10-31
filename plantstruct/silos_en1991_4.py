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
    """Presiones según EN 1991-4 §5.2 (filling).

    p_h(z) = γ·D/(4·μ·K)·(1 - exp(-z·4·μ·K/D))
    p_v(z) = p_h(z) / K
    p_w(z) = μ · p_h(z)
    """
    from math import tan, radians
    D = inp.diameter_m
    K = inp.K_lateral
    mu = tan(radians(inp.friction_angle_wall_deg))
    gamma = inp.bulk_density_kN_m3
    z = inp.height_filled_m

    A = D / (4.0 * mu * K)
    ph = gamma * A * (1.0 - exp(-z / A))
    pv = ph / K
    pw = mu * ph

    return SiloResult(
        z_max_m=z, p_horizontal_max_kPa=ph,
        p_vertical_max_kPa=pv, p_wall_friction_max_kPa=pw,
    )


__all__ = ["SiloInput", "SiloResult", "janssen_pressures"]
