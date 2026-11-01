"""
Anclajes de estanques API 650 §E.6.2 — relación de anclaje J, pernos y silleta.

Procedimiento básico (``check_anchorage``):
    1. M_rw de ``api650.housner_masses``
    2. Carga por perno P_AB = (4·M_rw/D − W_t) / N_b   (§E.6.2.1.2 con w_t = W_t/(π·D):
       P_AB = [1,273·M_rw/D² − w_t]·π·D/N_b, y 1,273·π = 4)
    3. Comparar con 0,6·F_y·A_b (más conservador que el 0,8·F_y de §E.6.2.1.2)

Procedimiento completo (``check_anchorage_J``, §E.6.2.1.1.1):
    4. J = M_rw / (D² · [w_t·(1 − 0,4·A_v) + w_a − 0,4·w_int])
       con w_t, w_a y w_int en fuerza POR UNIDAD DE PERÍMETRO (kN/m):
       w_t = peso de manto + techo / (π·D), w_a = fuerza resistente del anillo de
       fondo (§E.6.2.1.1.1), w_int = levantamiento por presión interna / (π·D).
       J <= 0,785  → autoanclado sin levantamiento
       0,785 < J <= 1,54 → autoanclado con levantamiento (comprobar L y t_a)
       J > 1,54   → anclaje mecánico
    5. N_b = P_a / (φ·A_b·F_y) — número de pernos
    6. Silleta: espesor de placa base y longitud de anclaje

Hasta 2026-10-31 el J dividía por el peso TOTAL W_t en vez de por el peso por
unidad de perímetro (factor π·D de error, siempre «autoanclado») y la memoria le
pasaba el peso del LÍQUIDO como W_t.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, pi, sqrt
from typing import Any


@dataclass(frozen=True)
class AnchorageInput:
    """Entrada de la comprobación simple de pernos.

    Args:
        D_m: diámetro del estanque [m].
        W_tank_kN: peso de manto + techo + accesorios que gravita sobre el anillo
            de anclaje [kN]. NO incluye el líquido (§E.6.2.1.2 usa w_t).
        M_overturn_kNm: momento volcante en la base del manto M_rw [kN·m].
        n_bolts, bolt_diameter_mm, bolt_Fy_MPa: pernos.
    """
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
# §E.6.2.1.1.1 — fuerza resistente del anillo de fondo
# ---------------------------------------------------------------------------

def annulus_resisting_force_kN_m(t_a_mm: float, Fy_MPa: float, H_m: float,
                                 G_e: float = 1.0, D_m: float | None = None) -> float:
    """Fuerza resistente del anillo de fondo w_a por unidad de perímetro (API 650 §E.6.2.1.1.1).

        w_a = 99 · t_a · sqrt(F_y · H · G_e)   [N/m]    <=  201,1 · H · D · G_e   [N/m]

    con t_a en mm (espesor del anillo menos corrosión), F_y en MPa, H y D en m y
    G_e = G·(1 − 0,4·A_v). El tope solo se aplica si se da D. Devuelve kN/m.
    """
    if min(t_a_mm, Fy_MPa, H_m, G_e) <= 0:
        raise ValueError("t_a, F_y, H y G_e deben ser > 0")
    w_a = 99.0 * t_a_mm * sqrt(Fy_MPa * H_m * G_e)
    if D_m is not None:
        if D_m <= 0:
            raise ValueError("D_m debe ser > 0")
        w_a = min(w_a, 201.1 * H_m * D_m * G_e)
    return w_a / 1000.0


# ---------------------------------------------------------------------------
# J-ratio (API 650 §E.6.2.1.1.1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AnchorageJInput:
    """Entrada para la relación de anclaje J de API 650 §E.6.2.1.1.1.

    Args:
        D_m: diámetro del estanque [m].
        M_rw_kNm: momento volcante en la base del manto (ringwall) [kN·m].
        W_t_kN: peso TOTAL de manto + techo (+ accesorios) que gravita sobre el
            anillo [kN]; se convierte a w_t = W_t/(π·D). NO incluye el líquido.
        W_int_kN: fuerza total de levantamiento por presión interna [kN]
            (cero en tanques atmosféricos); se convierte a w_int = W_int/(π·D).
        w_a_kN_m: fuerza resistente del anillo de fondo por unidad de perímetro
            [kN/m] (``annulus_resisting_force_kN_m``). None = 0 (sin crédito del
            líquido sobre el anillo: conservador para J).
        A_v: coeficiente de aceleración vertical (§E.6.1.3); reduce w_t.
        Fp_kN: levantamiento total neto impuesto [kN]. Si None,
            Fp = max(0, 4·M_rw/D − W_t·(1 − 0,4·A_v)) (§E.6.2.1.2, anclaje mecánico).
        bolt_diameter_mm, bolt_Fy_MPa, phi_bolt: pernos (LRFD).
        Fy_plate_MPa, f_bearing_MPa: silleta y apoyo sobre hormigón.
    """
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
    """Resultado de la relación J + diseño de anclaje."""
    J: float
    anchorage_type: str       # "self-anchored" | "conditioned" | "mechanically-anchored"
    N_bolts_required: int
    Ab_mm2: float             # área de un perno
    Fp_kN: float              # levantamiento total neto
    t_base_plate_mm: float    # espesor mínimo de la placa base (silleta)
    L_anchor_mm: float        # longitud de anclaje mínima (desarrollo)
    is_self_anchored: bool
    w_t_kN_m: float = 0.0     # peso de manto + techo por unidad de perímetro
    w_a_kN_m: float = 0.0     # fuerza resistente del anillo usada

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

    # --- J (§E.6.2.1.1.1), fuerzas por unidad de perímetro ---
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

    # --- Levantamiento total neto (§E.6.2.1.2, anclaje mecánico: sin crédito de w_a) ---
    if inp.Fp_kN is not None:
        Fp = inp.Fp_kN
    else:
        Fp = max(0.0, 4.0 * inp.M_rw_kNm / D - inp.W_t_kN * (1.0 - 0.4 * inp.A_v))

    # --- Número de pernos: N_b = P_a / (φ·Ab·Fy) ---
    Ab_mm2 = pi * inp.bolt_diameter_mm ** 2 / 4.0
    capacity_per_bolt_kN = inp.phi_bolt * Ab_mm2 * inp.bolt_Fy_MPa / 1000.0  # kN
    if Fp <= 0 or capacity_per_bolt_kN <= 0:
        N_bolts = 4  # mínimo constructivo
    else:
        N_bolts = max(4, ceil(Fp / capacity_per_bolt_kN))

    # --- Silleta: t_bp = d_bolt · sqrt(Fy_bolt / Fy_plate) (flexión local alrededor del perno) ---
    t_bp_mm = inp.bolt_diameter_mm * sqrt(inp.bolt_Fy_MPa / inp.Fy_plate_MPa)

    # --- Longitud de anclaje: L = Fy · db / (4 · f_bearing) (desarrollo simplificado) ---
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

    # Carga por perno — API 650 §E.6.2.1.2 con w_t = W_tank/(π·D)
    F_up = max(0.0, (4.0 * inp.M_overturn_kNm - inp.W_tank_kN * inp.D_m) /
               (inp.n_bolts * inp.D_m))

    # Capacidad axial del perno (kN), 60 % de la fluencia (§E.6.2.1.2 admite 0,8·F_y)
    A_b_mm2 = pi * inp.bolt_diameter_mm ** 2 / 4.0
    F_all = 0.6 * inp.bolt_Fy_MPa * A_b_mm2 / 1000.0  # kN

    DCR = F_up / F_all if F_all > 0 else float("inf")
    is_safe = DCR <= 1.0

    if F_up <= 0:
        n_req = inp.n_bolts
    else:
        # F_up = (4M − W·D)/(n_b·D) <= F_all → n_b >= (4M − W·D)/(D·F_all)
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
]
