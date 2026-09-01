"""Bases de columna - diseno placa base por Salmon & Johnson.

Considera carga axial + momento, dimensiona placa, anclajes y rigidizadores.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class BaseColumnaInput:
    """Entradas para diseño de placa base según Salmon & Johnson y AISC DG1.

    Reacciones en la base ingresadas como ENTRADA:
        P_kN: Reacción axial (+ compresión, - tracción).
        V_kN: Reacción cortante horizontal.
        M_kNm: Reacción momento flector.
    """
    P_kN: float
    V_kN: float = 0.0
    M_kNm: float = 0.0
    bf_mm: float = 200.0
    d_mm: float = 250.0
    fy_MPa: float = 250.0
    fc_MPa: float = 25.0
    fyb_MPa: float = 420.0
    n_anchors: int = 4
    db_anchor_mm: float = 25.0
    mu_friction: float = 0.40
    code: str = "US"


@dataclass(frozen=True)
class ShearLugResult:
    """Resultado del dimensionado de la llave de cortante (shear lug)."""
    required: bool
    shear_demand_kN: float
    shear_friction_capacity_kN: float
    lug_width_mm: float
    lug_height_mm: float
    lug_thickness_mm: float
    bearing_capacity_kN: float
    shear_capacity_kN: float
    is_ok: bool


@dataclass(frozen=True)
class BaseColumnaResult:
    N_mm: float
    B_mm: float
    t_mm: float
    Tu_anchor_kN: float
    e_mm: float
    shear_lug: ShearLugResult
    reactions: dict
    cumple: bool
    code: str

    def to_dict(self) -> dict:
        return {
            "N_mm": round(self.N_mm, 1),
            "B_mm": round(self.B_mm, 1),
            "t_mm": round(self.t_mm, 1),
            "Tu_anchor_kN": round(self.Tu_anchor_kN, 2),
            "e_mm": round(self.e_mm, 1),
            "shear_lug": {
                "required": self.shear_lug.required,
                "shear_demand_kN": self.shear_lug.shear_demand_kN,
                "lug_width_mm": self.shear_lug.lug_width_mm,
                "lug_height_mm": self.shear_lug.lug_height_mm,
                "lug_thickness_mm": self.shear_lug.lug_thickness_mm,
                "bearing_capacity_kN": round(self.shear_lug.bearing_capacity_kN, 2),
                "is_ok": self.shear_lug.is_ok,
            },
            "reactions": self.reactions,
            "cumple": self.cumple,
            "code": self.code,
        }


def disenar_base(inp: BaseColumnaInput) -> BaseColumnaResult:
    """Diseña placa base, pernos y llave de cortante según Salmon & Johnson (1996) / AISC Design Guide 1."""
    if inp.code not in {"EU", "AU", "SG", "US", "CO"}:
        raise ValueError(f"code invalido: {inp.code}")
    phi_c = 0.65 if inp.code in ("US", "CO") else 0.60
    phi_b = 0.90
    phi_v = 0.75

    fp_max = phi_c * 0.85 * inp.fc_MPa
    # Dimensiones mínimas en planta según carga axial P
    P_comp = max(inp.P_kN, 1.0)
    A_req = P_comp * 1000.0 / fp_max
    side = sqrt(A_req)
    N = max(side, inp.d_mm + 100.0)
    B = max(side, inp.bf_mm + 100.0)
    e_mm = abs(inp.M_kNm) * 1000.0 / P_comp

    # Caso pequeña vs gran excentricidad (Salmon & Johnson §14)
    if e_mm <= N / 6.0:
        fp = (P_comp * 1000.0 / (N * B)) + (6.0 * abs(inp.M_kNm) * 1e6 / (B * (N ** 2)))
        m = (N - 0.95 * inp.d_mm) / 2.0
        n = (B - 0.80 * inp.bf_mm) / 2.0
        l_crit = max(m, n, 1.0)
        t = l_crit * sqrt(2.0 * fp / (0.90 * inp.fy_MPa))
        Tu = 0.0
    else:
        # Gran excentricidad - tensión en anclajes
        lever_arm = max(N - 100.0, 50.0)
        Tu = max(abs(inp.M_kNm) * 1000.0 / lever_arm - P_comp / 2.0, 0.0)
        m = (N - 0.95 * inp.d_mm) / 2.0
        n = (B - 0.80 * inp.bf_mm) / 2.0
        l_crit = max(m, n, 1.0)
        t = l_crit * sqrt(2.0 * fp_max / (0.90 * inp.fy_MPa))

    # Capacidad anclajes a tracción
    import math
    A_anchor = math.pi * (inp.db_anchor_mm ** 2) / 4.0
    cap_anchor = (inp.n_anchors / 2.0) * A_anchor * inp.fyb_MPa / 1000.0
    anchors_ok = Tu <= cap_anchor

    # Llave de cortante (Shear Lug) - AISC Design Guide 1 / Salmon & Johnson
    V_demand = abs(inp.V_kN)
    V_friction = inp.mu_friction * P_comp
    lug_req = V_demand > V_friction

    lug_w = min(B - 100.0, inp.bf_mm)
    lug_h = 75.0   # mm
    lug_t = 25.0   # mm
    # Capacidad por aplastamiento del hormigón contra el shear lug: φ_c · 0.85 · f'c · (w · h)
    A_bearing_lug = lug_w * lug_h
    lug_bearing_cap = (phi_c * 0.85 * inp.fc_MPa * A_bearing_lug) / 1000.0
    lug_shear_cap = (phi_v * 0.60 * inp.fy_MPa * (lug_w * lug_t)) / 1000.0
    lug_ok = (lug_bearing_cap >= V_demand) and (lug_shear_cap >= V_demand) if lug_req else True

    shear_lug_res = ShearLugResult(
        required=lug_req,
        shear_demand_kN=V_demand,
        shear_friction_capacity_kN=V_friction,
        lug_width_mm=lug_w if lug_req else 0.0,
        lug_height_mm=lug_h if lug_req else 0.0,
        lug_thickness_mm=lug_t if lug_req else 0.0,
        bearing_capacity_kN=lug_bearing_cap if lug_req else 0.0,
        shear_capacity_kN=lug_shear_cap if lug_req else 0.0,
        is_ok=lug_ok,
    )

    reactions = {"P_kN": inp.P_kN, "V_kN": inp.V_kN, "M_kNm": inp.M_kNm}
    cumple = anchors_ok and (t > 0) and lug_ok

    return BaseColumnaResult(
        N_mm=N,
        B_mm=B,
        t_mm=t,
        Tu_anchor_kN=Tu,
        e_mm=e_mm,
        shear_lug=shear_lug_res,
        reactions=reactions,
        cumple=cumple,
        code=inp.code,
    )


__all__ = [
    "BaseColumnaInput",
    "BaseColumnaResult",
    "ShearLugResult",
    "disenar_base",
]

