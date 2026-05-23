"""
Estanques atmosféricos cilíndricos verticales — API 650 §E (sismo).

Implementa el modelo Housner / API 650 Apéndice E para masas impulsiva
y convectiva, periodos asociados y momento volcante de diseño. Sirve
de base para los anclajes y la verificación de pandeo del manto.

Referencias:
    API 650 (2020) — Welded Tanks for Oil Storage.
    Housner, G.W. (1963) — Dynamic behavior of water tanks.
    Malhotra, P.K. (2000) — Simple procedure for seismic analysis.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt, tanh
from typing import Any


@dataclass(frozen=True)
class TankGeometry:
    """Geometría básica del estanque cilíndrico vertical.

    Args:
        D_m: diámetro [m]
        H_l_m: altura del líquido almacenado [m]
        t_shell_mm: espesor del manto (referencia para pandeo) [mm]
        rho_l_kg_m3: densidad del líquido (default agua 1000 kg/m³)
    """
    D_m: float
    H_l_m: float
    t_shell_mm: float = 6.0
    rho_l_kg_m3: float = 1000.0

    def validate(self) -> None:
        for n, v in (("D_m", self.D_m), ("H_l_m", self.H_l_m),
                      ("t_shell_mm", self.t_shell_mm)):
            if v <= 0:
                raise ValueError(f"{n} debe ser > 0")
        if self.rho_l_kg_m3 <= 0:
            raise ValueError("rho_l_kg_m3 debe ser > 0")

    @property
    def W_l_kN(self) -> float:
        """Peso total del líquido [kN]."""
        V = pi * (self.D_m / 2) ** 2 * self.H_l_m
        return V * self.rho_l_kg_m3 * 9.80665 / 1000.0


@dataclass(frozen=True)
class SeismicMasses:
    W_i_kN: float        # impulsiva
    W_c_kN: float        # convectiva
    h_i_m: float         # brazo impulsiva
    h_c_m: float         # brazo convectiva
    T_i_s: float         # periodo impulsivo
    T_c_s: float         # periodo convectivo
    M_overturn_kNm: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "W_i_kN": self.W_i_kN, "W_c_kN": self.W_c_kN,
            "h_i_m": self.h_i_m, "h_c_m": self.h_c_m,
            "T_i_s": self.T_i_s, "T_c_s": self.T_c_s,
            "M_overturn_kNm": self.M_overturn_kNm,
        }


def housner_masses(geom: TankGeometry, Sa_i: float, Sa_c: float
                    ) -> SeismicMasses:
    """Masas y momento volcante por Housner (API 650 §E.6.1).

    Args:
        Sa_i: aceleración espectral impulsiva (fracción de g).
        Sa_c: aceleración espectral convectiva (fracción de g).
    """
    geom.validate()
    D, H = geom.D_m, geom.H_l_m
    W_l = geom.W_l_kN

    # Razones Housner (forma cerrada exacta del integral)
    ratio_HD = H / D
    tanh_term = tanh(sqrt(3.0) * D / (2.0 * H)) if H > 0 else 1.0
    Wi_over_W = tanh(sqrt(3.0) * D / (2.0 * H)) / (sqrt(3.0) * D / (2.0 * H))
    Wc_over_W = (D / H) * 0.230 * tanh(3.67 * H / D)

    W_i = Wi_over_W * W_l
    W_c = Wc_over_W * W_l

    # Brazos (sin contribución por presión de fondo)
    h_i = 0.375 * H
    h_c = H * (1.0 - (1.0 - 0.218 / (Wc_over_W or 1e-9)) / 1.0)
    # Forma estable equivalente:
    h_c = H * (1.0 - (1.0 / (3.67 * H / D)) * (
        (((H/D)**2) / (Wc_over_W + 1e-9))
    )) if H > 0 else 0.0
    h_c = max(0.4 * H, min(0.7 * H, h_c))  # acotar al rango físico

    # Periodo impulsivo (API 650 §E.4.5.1 / Malhotra 2000)
    # T_i = Ci · H · sqrt(ρ / E)  con Ci ≈ 6.0 para estanques de acero típicos
    # E acero ≈ 200 GPa = 200e9 Pa, ρ líquido en kg/m³
    Ci = 6.0  # coeficiente Malhotra (función de H/R, valor central)
    E_steel = 200.0e9  # Pa
    T_i = Ci * H * sqrt(geom.rho_l_kg_m3 / E_steel)

    # Periodo convectivo (API 650 §E.4.5.2)
    tanh_val = tanh(3.68 * H / D) if D > 0 else 0.0
    T_c = 2.0 * pi * sqrt(D / (3.68 * 9.80665 * tanh_val)) if tanh_val > 1e-9 else 0.0

    # Momento volcante en la base del manto
    M = Sa_i * W_i * h_i + Sa_c * W_c * h_c

    return SeismicMasses(
        W_i_kN=W_i, W_c_kN=W_c, h_i_m=h_i, h_c_m=h_c,
        T_i_s=T_i, T_c_s=T_c, M_overturn_kNm=M,
    )


def shell_axial_buckling_stress(geom: TankGeometry, E_MPa: float = 200_000.0
                                  ) -> float:
    """Esfuerzo crítico de pandeo axial del manto (Timoshenko ideal).

    σ_cr = 0.6 · E · t / R (factor empírico de imperfecciones API 650 §5.10.3).
    """
    R = geom.D_m * 1000.0 / 2.0  # mm
    return 0.6 * E_MPa * geom.t_shell_mm / R


__all__ = [
    "TankGeometry", "SeismicMasses",
    "housner_masses", "shell_axial_buckling_stress",
]
