"""
Chimeneas metálicas — EN 1991-1-4 §7.13 + ASCE 7-22 §29.

Acoplamiento crítico viento-vibración:
    v_crit_vortex = D · f1 / St
    Verificación: v_crit dentro de banda 0.5·V_b a 1.25·V_b
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt


@dataclass(frozen=True)
class ChimneyInput:
    D_outer_m: float
    H_m: float
    t_shell_mm: float
    Vb_m_per_s: float
    rho_steel_kg_m3: float = 7850.0
    E_MPa: float = 200_000.0


@dataclass(frozen=True)
class ChimneyResult:
    f1_Hz: float
    T1_s: float
    v_critical_m_per_s: float
    in_vortex_band: bool
    aspect_ratio: float
    self_weight_kN_per_m: float


def evaluate_chimney(inp: ChimneyInput) -> ChimneyResult:
    D = inp.D_outer_m
    t = inp.t_shell_mm / 1000.0
    H = inp.H_m

    # Frecuencia natural (cantilever uniform tube — modo 1)
    # f1 = (1.875²/2π) · √(EI / (m·H⁴))
    A = pi * D * t   # área de sección anular (delgada)
    I = pi * D ** 3 * t / 8.0
    m_per_m = A * inp.rho_steel_kg_m3
    f1 = (1.875 ** 2 / (2 * pi)) * sqrt(inp.E_MPa * 1e6 * I / (m_per_m * H ** 4))

    St = 0.18
    v_crit = D * f1 / St
    in_band = 0.5 * inp.Vb_m_per_s <= v_crit <= 1.25 * inp.Vb_m_per_s

    return ChimneyResult(
        f1_Hz=f1, T1_s=1.0 / f1 if f1 > 0 else float("inf"),
        v_critical_m_per_s=v_crit,
        in_vortex_band=in_band,
        aspect_ratio=H / D,
        self_weight_kN_per_m=m_per_m * 9.80665 / 1000.0,
    )


__all__ = ["ChimneyInput", "ChimneyResult", "evaluate_chimney"]
