"""
Diseño de anclajes — multi-código.

Códigos:
    US:   ACI 318-19 Capítulo 17 (post-instalados y concreto coladero)
    CO:   NSR-10 §C.17 (idéntico ACI)
    EU/SG: EN 1992-4 (anchor design)
    AU:   AS 5216 (post-installed) + SA TS 101

Cubre el modo "arrancamiento del cono de hormigón" de UN anclaje sin bordes
(A_Nc = A_Nco) ni excentricidad, multiplicado por el número de anclajes:
    N_cb  = Psi_c,N · k_c·√f'c · h_ef^1.5   (US/CO, SI: k_c = 10, Psi_c,N = 1,25 no fisurado)
    N_Rk,c = k1·√fck · h_ef^1.5             (EU/SG: k1 = 7,7 / 11,0)
Para grupos con bordes y separaciones use ``bases_columna`` (A_Nc/A_Nco, Psi_ed,N).
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
        # ACI 318-19 §17.6.2.2.1: k_c = 10 (SI, coladero). El hormigón no
        # fisurado entra por Psi_c,N = 1,25 (§17.6.2.5), no por k_c. Hasta
        # 2026-10-31 se usaba k_c = 17 para no fisurado, que es el valor en
        # libras-pulgada de los anclajes POST-INSTALADOS (1,7x en vez de 1,25x).
        k_c = 10.0
        psi_c = 1.0 if inp.cracked_concrete else 1.25
        N_cb = psi_c * k_c * sqrt(fc) * h ** 1.5 / 1000.0  # kN
        phi = 0.65  # tension, Condición B sin armadura suplementaria (post-instalado)
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
