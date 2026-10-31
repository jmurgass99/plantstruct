"""
Diseño de anclajes — multi-código.

Códigos:
    US:   ACI 318-19 Capítulo 17 (post-instalados y concreto coladero)
    CO:   NSR-10 §C.17 (idéntico ACI)
    EU/SG: EN 1992-4 (anchor design)
    AU:   AS 5216 (post-installed) + SA TS 101

Cubre el modo "pull-out de cono de concreto" simplificado:
    N_cb = k·√f'c · h_ef^1.5   (US/CO)
    N_Rk,c = k1·√fck · h_ef^1.5 (EU/SG)
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, Literal


@dataclass(frozen=True)
class AnchorInput:
    fc_MPa: float
    h_ef_mm: float                # profundidad efectiva
    edge_distance_mm: float = 200
    n_anchors: int = 1
    cracked_concrete: bool = True


@dataclass(frozen=True)
class AnchorResult:
    N_design_kN: float
    phi_or_gamma: float
    governing_mode: str
    code: str


def design_anchor_concrete_cone(inp: AnchorInput, code: str = "US"
                                   ) -> AnchorResult:
    """Modo de falla cono de concreto."""
    code = code.upper()
    h = inp.h_ef_mm
    fc = inp.fc_MPa

    if code in ("US", "CO"):
        # ACI 318-19 Eq. 17.6.2.2
        k_c = 10 if inp.cracked_concrete else 17  # SI
        N_cb = k_c * sqrt(fc) * h ** 1.5 / 1000.0  # kN
        phi = 0.65  # tension, cracked
        N_design = phi * N_cb * inp.n_anchors
        return AnchorResult(N_design_kN=N_design, phi_or_gamma=phi,
                             governing_mode="concrete_cone", code=code)
    if code in ("EU", "SG"):
        # EN 1992-4 §7.2.1.4
        k1 = 7.7 if inp.cracked_concrete else 11.0
        N_Rk = k1 * sqrt(fc) * h ** 1.5 / 1000.0
        gamma_Mc = 1.50
        N_design = N_Rk / gamma_Mc * inp.n_anchors
        return AnchorResult(N_design_kN=N_design, phi_or_gamma=1/gamma_Mc,
                             governing_mode="concrete_cone", code=code)
    if code == "AU":
        # AS 5216 §6.2.1 — análogo a EN 1992-4 con γ_M = 1.40
        k = 7.2 if inp.cracked_concrete else 10.1
        N_Rk = k * sqrt(fc) * h ** 1.5 / 1000.0
        gamma_M = 1.40
        N_design = N_Rk / gamma_M * inp.n_anchors
        return AnchorResult(N_design_kN=N_design, phi_or_gamma=1/gamma_M,
                             governing_mode="concrete_cone", code=code)
    raise ValueError(f"código '{code}' no soportado")


__all__ = ["AnchorInput", "AnchorResult", "design_anchor_concrete_cone"]
