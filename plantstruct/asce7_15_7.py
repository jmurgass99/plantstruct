"""ASCE 7-22 §15.7.6 — tanques y depósitos de líquidos: cortante basal impulsivo + convectivo.

    V_i = (S_ai · I_e / R_i) · (W_s + W_r + W_i)          §15.7.6.1
    V_c = (S_ac · I_e / R_c) · W_c
    S_ai = S_DS (meseta; con T_i > T_s = S_D1/S_DS, S_ai = S_D1/T_i <= S_DS)
    S_ac = 1,5·S_D1/T_c <= 1,5·S_DS      (T_c <= T_L)     ec. 15.7-10
    S_ac = 1,5·S_D1·T_L/T_c²             (T_c >  T_L)     ec. 15.7-11
    T_c  = 2π·sqrt(D/(3,68·g·tanh(3,68·H/D)))               ec. 15.7-13
    V    = sqrt(V_i² + V_c²)

Las fracciones de peso impulsiva y convectiva y sus ramas son las de ACI 350.3 /
API 650 Anexo E (Housner). El periodo impulsivo T_i lo remite ASCE 7 al documento
de referencia del tanque: aquí se usa API 650 §E.4.5.1 si se da el espesor del
manto; sin espesor se toma T_i = 0 (impulsivo rígido, S_ai = S_DS).

Hasta 2026-10-31 la fracción convectiva tenía D/H invertido (0,230·H/D en vez de
0,230·D/H: 0,171 frente a 0,304 para D/H = 1,33), faltaba la rama de tanque
esbelto (D/H < 1,333) y S_ac no llevaba el factor 1,5 ni el tope 1,5·S_DS.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt, tanh

from .tanks.api650 import G_M_S2, impulsive_period_s


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
    TL_s: float | None = None        # periodo de transición de periodo largo (Fig. 22-14…); None = T_c <= T_L
    t_shell_mm: float | None = None  # espesor uniforme del manto para T_i (API 650 §E.4.5.1); None = rígido
    E_MPa: float = 200_000.0
    W_s_kN: float = 0.0              # peso del manto (entra en V_i)
    W_r_kN: float = 0.0              # peso del techo (entra en V_i)


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
    Sai_g: float = 0.0
    Sac_g: float = 0.0


def asce_15_7(inp: TankASCEInput) -> TankASCEResult:
    if inp.code not in {"US", "CO"}:
        raise ValueError(f"ASCE 7-15.7 solo aplica a code US/CO; recibio {inp.code}")
    if inp.D_m <= 0 or inp.H_l_m <= 0:
        raise ValueError("D_m y H_l_m deben ser > 0")
    D, Hl = inp.D_m, inp.H_l_m
    R = D / 2.0
    Wl = pi * R ** 2 * Hl * inp.rho_l_kg_m3 * G_M_S2 / 1000.0
    r = D / Hl
    # Fracciones de Housner (ACI 350.3 §9.3 / API 650 §E.6.1.1)
    if r >= 1.333:
        Wi_W = tanh(0.866 * r) / (0.866 * r)
    else:
        Wi_W = 1.0 - 0.218 * r
    Wc_W = 0.230 * r * tanh(3.68 / r)
    Wi = Wi_W * Wl
    Wc = Wc_W * Wl

    # Periodos
    Tc = 2.0 * pi * sqrt(D / (3.68 * G_M_S2 * tanh(3.68 * Hl / D)))
    Ti = (impulsive_period_s(D, Hl, inp.t_shell_mm, inp.rho_l_kg_m3, inp.E_MPa)
          if inp.t_shell_mm is not None else 0.0)

    # Aceleraciones espectrales de diseño
    Ts = inp.Sd1 / inp.Sds if inp.Sds > 0 else 0.0
    Sai = inp.Sds
    if Ti > Ts and Ti > 0:
        Sai = min(inp.Sd1 / Ti, inp.Sds)
    if inp.TL_s is not None and Tc > inp.TL_s:
        Sac = 1.5 * inp.Sd1 * inp.TL_s / Tc ** 2
    else:
        Sac = min(1.5 * inp.Sd1 / Tc, 1.5 * inp.Sds)

    Vi = (Sai * inp.Ie / inp.Ri) * (inp.W_s_kN + inp.W_r_kN + Wi)
    Vc = (Sac * inp.Ie / inp.Rc) * Wc
    V = sqrt(Vi ** 2 + Vc ** 2)
    return TankASCEResult(Wi, Wc, Ti, Tc, Vi, Vc, V, inp.code, Sai, Sac)


__all__ = ["TankASCEInput", "TankASCEResult", "asce_15_7"]
