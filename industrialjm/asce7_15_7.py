"""ASCE 7-22 capitulo 15.7 - tanques siismicos (impulsivo + convectivo)."""
from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt, tanh


@dataclass(frozen=True)
class TankASCEInput:
    D_m: float
    H_l_m: float
    rho_l_kg_m3: float = 1000.0
    Sds: float = 1.0
    Sd1: float = 0.6
    Ie: float = 1.5
    Ri: float = 3.0
    Rc: float = 1.5
    code: str = "US"


@dataclass(frozen=True)
class TankASCEResult:
    Wi_kN: float
    Wc_kN: float
    Ti_s: float
    Tc_s: float
    Vi_kN: float
    Vc_kN: float
    V_total_kN: float
    code: str


def asce_15_7(inp: TankASCEInput) -> TankASCEResult:
    if inp.code not in {"US", "CO"}:
        raise ValueError(f"ASCE 7-15.7 solo aplica a code US/CO; recibio {inp.code}")
    D, Hl = inp.D_m, inp.H_l_m
    R = D / 2.0
    Wl = pi * R ** 2 * Hl * inp.rho_l_kg_m3 * 9.81 / 1000.0
    aspect = D / Hl
    # ACI 350.3 / ASCE 7 fracciones
    Wi_W = tanh(0.866 * aspect) / (0.866 * aspect) if aspect > 0 else 1.0
    Wc_W = 0.230 / aspect * tanh(3.68 / aspect) if aspect > 0 else 0.0
    Wi = Wi_W * Wl
    Wc = Wc_W * Wl
    # periodos
    Ti = 0.0  # rigido para AWWA D100 esbeltos pequenos
    Tc = 2 * pi * sqrt(D / (3.68 * 9.81 * tanh(3.68 * Hl / D))) if Hl > 0 else 0.0
    Cs_i = inp.Sds * inp.Ie / inp.Ri
    Cs_c = (inp.Sd1 / max(Tc, 0.01)) * inp.Ie / inp.Rc
    Vi = Cs_i * Wi
    Vc = Cs_c * Wc
    V = sqrt(Vi ** 2 + Vc ** 2)
    return TankASCEResult(Wi, Wc, Ti, Tc, Vi, Vc, V, inp.code)


__all__ = ["TankASCEInput", "TankASCEResult", "asce_15_7"]
