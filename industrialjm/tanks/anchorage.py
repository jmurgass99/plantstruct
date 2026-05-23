"""
Anclajes de estanques API 650 §E.6.2 — verificación de pernos vs uplift
por momento volcante sísmico.

Procedimiento básico:
    1. M_overturn de Housner (`api650.housner_masses`)
    2. F_uplift por perno = (4·M - W_T·D) / (N_b · D)  (API 650 Eq. E.6.2.1-1)
    3. Comparar con F_perno_allowable = π·d_b²/4 · F_y_perno · 0.6

Procedimiento completo §E.6.2:
    4. J = M_rw / (D² · (W_t - 0.4·W_int))   — anchorage ratio
       J ≤ 0.785  → self-anchored (no requiere pernos)
       0.785 < J ≤ 1.54 → self-anchored condicionado
       J > 1.54   → mechanically anchored
    5. N_b = P_a / (φ·Ab·Fy) — número de pernos requerido
    6. Silleta: espesor base plate, longitud de anclaje
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, pi, sqrt
from typing import Any


@dataclass(frozen=True)
class AnchorageInput:
    D_m: float                  # diámetro estanque
    W_tank_kN: float            # peso del estanque (manto+techo+contenido)
    M_overturn_kNm: float       # momento volcante sísmico
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
# J-ratio (API 650 §E.6.2.1.1) — anchorage ratio
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AnchorageJInput:
    """Entrada para verificación J-ratio API 650 §E.6.2.1.1.

    Args:
        D_m: diámetro del estanque [m].
        M_rw_kNm: momento volcante ringwall (base del manto) [kN·m].
        W_t_kN: peso estabilizante del estanque (manto + techo + porción
                 del líquido que actúa como peso muerto) [kN].
        W_int_kN: fuerza de levantamiento por presión interna [kN].
                  Típicamente cero para tanques atmosféricos.
        Fp_kN: fuerza total de anclaje requerida (uplift neto) [kN].
                Si None, se calcula como max(0, 4·M_rw/(D) - W_t).
        bolt_diameter_mm: diámetro nominal del perno de anclaje [mm].
        bolt_Fy_MPa: fluencia del perno [MPa].
        phi_bolt: factor de resistencia del perno (LRFD).
        Fy_plate_MPa: fluencia de la placa base (silleta) [MPa].
        f_bearing_MPa: esfuerzo admisible de apoyo sobre concreto [MPa].
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


@dataclass(frozen=True)
class AnchorageJResult:
    """Resultado de verificación J-ratio + diseño de anclaje."""
    J: float
    anchorage_type: str       # "self-anchored" | "conditioned" | "mechanically-anchored"
    N_bolts_required: int
    Ab_mm2: float             # área de un perno
    Fp_kN: float              # uplift total neto
    t_base_plate_mm: float    # espesor mínimo placa base (silleta)
    L_anchor_mm: float        # longitud de anclaje mínima (desarrollo)
    is_self_anchored: bool

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
        }


def check_anchorage_J(inp: AnchorageJInput) -> AnchorageJResult:
    """Verificación completa de anclaje API 650 §E.6.2.

    Calcula el J-ratio, clasifica el tipo de anclaje,
    determina el número de pernos requerido y diseña la silleta.
    """
    if inp.D_m <= 0:
        raise ValueError("D_m debe ser > 0")
    if inp.bolt_diameter_mm <= 0:
        raise ValueError("bolt_diameter_mm debe ser > 0")

    D = inp.D_m

    # --- J-ratio: API 650 §E.6.2.1.1 ---
    denominator = D ** 2 * (inp.W_t_kN - 0.4 * inp.W_int_kN)
    if denominator <= 0:
        J = float("inf")
    else:
        J = inp.M_rw_kNm / denominator

    # Clasificación
    if J <= 0.785:
        anchorage_type = "self-anchored"
    elif J <= 1.54:
        anchorage_type = "conditioned"
    else:
        anchorage_type = "mechanically-anchored"

    is_self_anchored = J <= 0.785

    # --- Uplift total neto ---
    if inp.Fp_kN is not None:
        Fp = inp.Fp_kN
    else:
        Fp = max(0.0, 4.0 * inp.M_rw_kNm / D - inp.W_t_kN)

    # --- Número de pernos: N_b = P_a / (φ·Ab·Fy) ---
    Ab_mm2 = pi * inp.bolt_diameter_mm ** 2 / 4.0
    capacity_per_bolt_kN = inp.phi_bolt * Ab_mm2 * inp.bolt_Fy_MPa / 1000.0  # kN

    if Fp <= 0 or capacity_per_bolt_kN <= 0:
        N_bolts = 4  # mínimo constructivo
    else:
        N_bolts = max(4, ceil(Fp / capacity_per_bolt_kN))

    # --- Diseño de silleta (base plate) ---
    # Espesor mínimo placa base: t_bp = d_bolt · √(Fy_bolt / Fy_plate)
    # (criterio de flexión local de la placa alrededor del perno)
    t_bp_mm = inp.bolt_diameter_mm * sqrt(inp.bolt_Fy_MPa / inp.Fy_plate_MPa)

    # Longitud de anclaje mínima: L_anchor
    # Transferencia al concreto por adherencia:
    # L = Fy · db / (4 · f_bearing)  (desarrollo simplificado)
    if inp.f_bearing_MPa > 0:
        L_anchor_mm = (inp.bolt_Fy_MPa * inp.bolt_diameter_mm
                       / (4.0 * inp.f_bearing_MPa))
    else:
        L_anchor_mm = 20.0 * inp.bolt_diameter_mm  # fallback

    return AnchorageJResult(
        J=J,
        anchorage_type=anchorage_type,
        N_bolts_required=N_bolts,
        Ab_mm2=Ab_mm2,
        Fp_kN=Fp,
        t_base_plate_mm=t_bp_mm,
        L_anchor_mm=L_anchor_mm,
        is_self_anchored=is_self_anchored,
    )


def check_anchorage(inp: AnchorageInput) -> AnchorageResult:
    if inp.n_bolts < 4:
        raise ValueError("n_bolts debe ser ≥ 4")
    if inp.D_m <= 0 or inp.bolt_diameter_mm <= 0:
        raise ValueError("D_m y bolt_diameter_mm deben ser > 0")

    # Uplift por perno — API 650 Eq. E.6.2.1-1 simplificada
    F_up = max(0.0, (4.0 * inp.M_overturn_kNm - inp.W_tank_kN * inp.D_m) /
               (inp.n_bolts * inp.D_m))

    # Capacidad axial del perno (kN), 60% de fluencia
    A_b_mm2 = pi * inp.bolt_diameter_mm ** 2 / 4.0
    F_all = 0.6 * inp.bolt_Fy_MPa * A_b_mm2 / 1000.0  # kN

    DCR = F_up / F_all if F_all > 0 else float("inf")
    is_safe = DCR <= 1.0

    # Pernos requeridos
    if F_up <= 0:
        n_req = inp.n_bolts
    else:
        # Resolver n_b tal que F_up_per_bolt = F_all
        # F_up = (4M - W·D)/(n_b·D) ≤ F_all → n_b ≥ (4M - W·D)/(D·F_all)
        n_req = int(max(4, ((4 * inp.M_overturn_kNm - inp.W_tank_kN * inp.D_m)
                            / (inp.D_m * F_all)) + 1))

    return AnchorageResult(
        F_uplift_per_bolt_kN=F_up, F_allowable_per_bolt_kN=F_all,
        DCR=DCR, is_safe=is_safe, n_bolts_required_min=n_req,
    )


__all__ = [
    "AnchorageInput", "AnchorageResult", "check_anchorage",
    "AnchorageJInput", "AnchorageJResult", "check_anchorage_J",
]
