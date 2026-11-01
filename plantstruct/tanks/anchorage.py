"""
Anclajes de estanques API 650 §E.6.2 — relación de anclaje J, pernos y silleta.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, pi, sqrt
from typing import Any


@dataclass(frozen=True)
class AnchorageInput:
    D_m: float
    W_tank_kN: float
    M_overturn_kNm: float
    n_bolts: int = 12
    bolt_diameter_mm: float = 25.4
    bolt_Fy_MPa: float = 250.0


@dataclass(frozen=True)
class AnchorageResult:
    F_uplift_per_bolt_kN: float
    F_allowable_per_bolt_kN: float
    DCR: float
    is_safe: bool
    n_bolts_required_min: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "F_uplift_per_bolt_kN": self.F_uplift_per_bolt_kN,
            "F_allowable_per_bolt_kN": self.F_allowable_per_bolt_kN,
            "DCR": self.DCR,
            "is_safe": self.is_safe,
            "n_bolts_required_min": self.n_bolts_required_min,
        }


# ---------------------------------------------------------------------------
# §E.6.2.1.1.1 — fuerza resistente del anillo de fondo y longitud L (§E.6.2.1.1.2)
# ---------------------------------------------------------------------------

def annulus_resisting_force_kN_m(t_a_mm: float, Fy_MPa: float, H_m: float,
                                 G_e: float = 1.0, D_m: float | None = None) -> float:
    """Fuerza resistente del anillo de fondo w_a por unidad de perímetro (API 650 §E.6.2.1.1.1).

        w_a = 99 · t_a · sqrt(F_y · H · G_e)   [N/m]    <=  201,1 · H · D · G_e   [N/m]
    """
    if min(t_a_mm, Fy_MPa, H_m, G_e) <= 0:
        raise ValueError("t_a, F_y, H y G_e deben ser > 0")
    w_a = 99.0 * t_a_mm * sqrt(Fy_MPa * H_m * G_e)
    if D_m is not None:
        if D_m <= 0:
            raise ValueError("D_m debe ser > 0")
        w_a = min(w_a, 201.1 * H_m * D_m * G_e)
    return w_a / 1000.0


def self_anchored_uplift_length_api650(
    t_a_mm: float,
    Fy_MPa: float,
    H_m: float,
    G_e: float = 1.0,
    D_m: float | None = None,
) -> dict[str, float | bool | None]:
    """Longitud radial de levantamiento del fondo L según API 650 §E.6.2.1.1.2 (SI).

        L = 0.01723 · t_a · sqrt(F_y / (H · G_e))   [m]
        L_max = 0.035 · D                           [m]
    """
    if min(t_a_mm, Fy_MPa, H_m, G_e) <= 0:
        raise ValueError("t_a, F_y, H y G_e deben ser > 0")
    L_m = 0.01723 * t_a_mm * sqrt(Fy_MPa / (H_m * G_e))
    L_max_m = 0.035 * D_m if D_m is not None else None
    within_limit = (L_m <= L_max_m) if L_max_m is not None else True
    return {
        "L_uplift_m": L_m,
        "L_max_0035D_m": L_max_m,
        "L_governed_m": min(L_m, L_max_m) if L_max_m is not None else L_m,
        "within_0035D_limit": within_limit,
    }


# ---------------------------------------------------------------------------
# J-ratio (API 650 §E.6.2.1.1.1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AnchorageJInput:
    D_m: float
    M_rw_kNm: float
    W_t_kN: float
    W_int_kN: float = 0.0
    Fp_kN: float | None = None
    bolt_diameter_mm: float = 25.4
    bolt_Fy_MPa: float = 250.0
    phi_bolt: float = 0.75
    Fy_plate_MPa: float = 250.0
    f_bearing_MPa: float = 10.0
    w_a_kN_m: float | None = None
    A_v: float = 0.0


@dataclass(frozen=True)
class AnchorageJResult:
    J: float
    anchorage_type: str
    N_bolts_required: int
    Ab_mm2: float
    Fp_kN: float
    t_base_plate_mm: float
    L_anchor_mm: float
    is_self_anchored: bool
    w_t_kN_m: float = 0.0
    w_a_kN_m: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "J": self.J,
            "anchorage_type": self.anchorage_type,
            "N_bolts_required": self.N_bolts_required,
            "Ab_mm2": self.Ab_mm2,
            "Fp_kN": self.Fp_kN,
            "t_base_plate_mm": self.t_base_plate_mm,
            "L_anchor_mm": self.L_anchor_mm,
            "is_self_anchored": self.is_self_anchored,
            "w_t_kN_m": self.w_t_kN_m,
            "w_a_kN_m": self.w_a_kN_m,
        }


def check_anchorage_J(inp: AnchorageJInput) -> AnchorageJResult:
    """Relación de anclaje J (API 650 §E.6.2.1.1.1), tipo de anclaje, pernos y silleta."""
    if inp.D_m <= 0:
        raise ValueError("D_m debe ser > 0")
    if inp.bolt_diameter_mm <= 0:
        raise ValueError("bolt_diameter_mm debe ser > 0")
    if inp.W_t_kN < 0 or inp.W_int_kN < 0 or inp.A_v < 0:
        raise ValueError("W_t, W_int y A_v deben ser >= 0")

    D = inp.D_m
    perimetro = pi * D
    w_t = inp.W_t_kN / perimetro
    w_int = inp.W_int_kN / perimetro
    w_a = inp.w_a_kN_m or 0.0

    denominator = D ** 2 * (w_t * (1.0 - 0.4 * inp.A_v) + w_a - 0.4 * w_int)
    if denominator <= 0:
        J = float("inf")
    else:
        J = inp.M_rw_kNm / denominator

    if J <= 0.785:
        anchorage_type = "self-anchored"
    elif J <= 1.54:
        anchorage_type = "conditioned"
    else:
        anchorage_type = "mechanically-anchored"
    is_self_anchored = J <= 0.785

    if inp.Fp_kN is not None:
        Fp = inp.Fp_kN
    else:
        Fp = max(0.0, 4.0 * inp.M_rw_kNm / D - inp.W_t_kN * (1.0 - 0.4 * inp.A_v))

    Ab_mm2 = pi * inp.bolt_diameter_mm ** 2 / 4.0
    capacity_per_bolt_kN = inp.phi_bolt * Ab_mm2 * inp.bolt_Fy_MPa / 1000.0
    if Fp <= 0 or capacity_per_bolt_kN <= 0:
        N_bolts = 4
    else:
        N_bolts = max(4, ceil(Fp / capacity_per_bolt_kN))

    t_bp_mm = inp.bolt_diameter_mm * sqrt(inp.bolt_Fy_MPa / inp.Fy_plate_MPa)

    if inp.f_bearing_MPa > 0:
        L_anchor_mm = inp.bolt_Fy_MPa * inp.bolt_diameter_mm / (4.0 * inp.f_bearing_MPa)
    else:
        L_anchor_mm = 20.0 * inp.bolt_diameter_mm

    return AnchorageJResult(
        J=J,
        anchorage_type=anchorage_type,
        N_bolts_required=N_bolts,
        Ab_mm2=Ab_mm2,
        Fp_kN=Fp,
        t_base_plate_mm=t_bp_mm,
        L_anchor_mm=L_anchor_mm,
        is_self_anchored=is_self_anchored,
        w_t_kN_m=w_t,
        w_a_kN_m=w_a,
    )


def check_anchorage(inp: AnchorageInput) -> AnchorageResult:
    if inp.n_bolts < 4:
        raise ValueError("n_bolts debe ser ≥ 4")
    if inp.D_m <= 0 or inp.bolt_diameter_mm <= 0:
        raise ValueError("D_m y bolt_diameter_mm deben ser > 0")

    F_up = max(0.0, (4.0 * inp.M_overturn_kNm - inp.W_tank_kN * inp.D_m) /
               (inp.n_bolts * inp.D_m))

    A_b_mm2 = pi * inp.bolt_diameter_mm ** 2 / 4.0
    F_all = 0.6 * inp.bolt_Fy_MPa * A_b_mm2 / 1000.0

    DCR = F_up / F_all if F_all > 0 else float("inf")
    is_safe = DCR <= 1.0

    if F_up <= 0:
        n_req = inp.n_bolts
    else:
        n_req = int(max(4, ((4 * inp.M_overturn_kNm - inp.W_tank_kN * inp.D_m)
                            / (inp.D_m * F_all)) + 1))

    return AnchorageResult(
        F_uplift_per_bolt_kN=F_up, F_allowable_per_bolt_kN=F_all,
        DCR=DCR, is_safe=is_safe, n_bolts_required_min=n_req,
    )


__all__ = [
    "AnchorageInput", "AnchorageResult", "check_anchorage",
    "AnchorageJInput", "AnchorageJResult", "check_anchorage_J",
    "annulus_resisting_force_kN_m",
    "self_anchored_uplift_length_api650",
]
