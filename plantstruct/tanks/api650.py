"""
Estanques atmosféricos cilíndricos verticales — API 650 Anexo E (sismo).

Implementa el modelo de Housner tal como lo tabula API 650 Anexo E: masas
impulsiva y convectiva con sus alturas (§E.6.1.1 y §E.6.1.2), periodos
impulsivo y convectivo (§E.4.5.1 y §E.4.5.2), cortante basal y momento
volcante en la base del manto combinados en raíz cuadrada de la suma de
cuadrados (§E.6.1 y §E.6.1.5). Sirve de base para los anclajes y la
verificación de pandeo del manto.

Convenio de entrada: ``Sa_i`` y ``Sa_c`` son los coeficientes A_i y A_c de
§E.4.6.1 (fracción de g), es decir, YA incluyen el factor de reducción R_wi /
R_wc y el factor de importancia I. Si se parte de un espectro elástico hay que
dividir antes por R_w/I.

Hasta 2026-10-31 este módulo (a) usaba solo la rama D/H >= 1,333 para la masa
impulsiva y su altura, (b) calculaba X_c con una expresión propia acotada a
0,4–0,7·H, (c) daba T_i = C_i·H·sqrt(rho/E) sin el factor 1/sqrt(2000) ni el
sqrt(t_u/D) de §E.4.5.1, lo que producía 0,006 s para un tanque de 20 m, y
(d) sumaba linealmente los momentos impulsivo y convectivo en vez de la
combinación SRSS de la norma.

Referencias:
    API 650 (13.ª ed., 2020) — Welded Tanks for Oil Storage, Anexo E.
    Housner, G.W. (1963) — The dynamic behavior of water tanks. BSSA 53(2).
    Malhotra, P.K., Wenk, T., Wieland, M. (2000) — Simple procedure for
    seismic analysis of liquid-storage tanks. Structural Engineering
    International 10(3) (tabla de C_i, recogida en EN 1998-4 Anexo A).
"""
from __future__ import annotations

from dataclasses import dataclass
from math import cosh, pi, sinh, sqrt, tanh
from typing import Any

G_M_S2 = 9.80665
GAMMA_STEEL_KN_M3 = 78.5


@dataclass(frozen=True)
class TankGeometry:
    """Geometría básica del estanque cilíndrico vertical.

    Args:
        D_m: diámetro [m]
        H_l_m: altura del líquido almacenado [m]
        t_shell_mm: espesor uniforme equivalente del manto t_u (§E.4.5.1) [mm];
            también se usa como referencia para el pandeo axial.
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
        return V * self.rho_l_kg_m3 * G_M_S2 / 1000.0


@dataclass(frozen=True)
class SeismicMasses:
    W_i_kN: float        # peso impulsivo efectivo
    W_c_kN: float        # peso convectivo efectivo
    h_i_m: float         # altura X_i del impulsivo sobre el fondo
    h_c_m: float         # altura X_c del convectivo sobre el fondo
    T_i_s: float         # periodo impulsivo (§E.4.5.1)
    T_c_s: float         # periodo convectivo (§E.4.5.2)
    M_overturn_kNm: float  # momento volcante en la base del manto, SRSS (§E.6.1.5)
    V_base_kN: float = 0.0  # cortante basal, SRSS (§E.6.1)
    C_i: float = 0.0        # coeficiente C_i usado en T_i (Fig. E.1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "W_i_kN": self.W_i_kN, "W_c_kN": self.W_c_kN,
            "h_i_m": self.h_i_m, "h_c_m": self.h_c_m,
            "T_i_s": self.T_i_s, "T_c_s": self.T_c_s,
            "M_overturn_kNm": self.M_overturn_kNm,
            "V_base_kN": self.V_base_kN,
            "C_i": self.C_i,
        }


# ---------------------------------------------------------------------------
# §E.4.5 — periodos
# ---------------------------------------------------------------------------

#: C_i frente a H/R (Malhotra, Wenk y Wieland 2000, Tabla 1 = EN 1998-4 Anexo A
#: Tabla A.2). Es la misma curva que API 650 dibuja en la Fig. E.1 frente a H/D.
_CI_TABLE: tuple[tuple[float, float], ...] = (
    (0.3, 9.28), (0.5, 7.74), (0.7, 6.97), (1.0, 6.36),
    (1.5, 6.06), (2.0, 6.21), (2.5, 6.56), (3.0, 7.03),
)


def impulsive_coefficient_Ci(H_over_R: float) -> float:
    """Coeficiente C_i del periodo impulsivo (API 650 Fig. E.1) por interpolación lineal.

    Fuera del rango tabulado (0,3 <= H/R <= 3,0) se devuelve el valor extremo.
    """
    if H_over_R <= 0:
        raise ValueError("H/R debe ser > 0")
    if H_over_R <= _CI_TABLE[0][0]:
        return _CI_TABLE[0][1]
    if H_over_R >= _CI_TABLE[-1][0]:
        return _CI_TABLE[-1][1]
    for (x0, y0), (x1, y1) in zip(_CI_TABLE, _CI_TABLE[1:]):
        if x0 <= H_over_R <= x1:
            return y0 + (y1 - y0) * (H_over_R - x0) / (x1 - x0)
    raise AssertionError("interpolación de C_i fuera de tabla")  # pragma: no cover


def impulsive_period_s(D_m: float, H_m: float, t_u_mm: float,
                       rho_kg_m3: float = 1000.0, E_MPa: float = 200_000.0) -> float:
    """Periodo impulsivo T_i según API 650 §E.4.5.1 (unidades SI de la norma).

        T_i = (1/sqrt(2000)) · (C_i·H / sqrt(t_u/D)) · (sqrt(rho) / sqrt(E))

    con H y D en m, t_u en mm, rho en kg/m³ y E en MPa; devuelve segundos.
    Es idéntica a T_imp = C_i·H·sqrt(rho)/(sqrt(s/R)·sqrt(E)) de Malhotra (2000)
    en unidades base: sqrt(s/R) = sqrt(t_u/D)·sqrt(2/1000) y sqrt(E[Pa]) =
    1000·sqrt(E[MPa]), de donde sale el 1/sqrt(2000).
    """
    if min(D_m, H_m, t_u_mm, rho_kg_m3, E_MPa) <= 0:
        raise ValueError("D, H, t_u, rho y E deben ser > 0")
    C_i = impulsive_coefficient_Ci(2.0 * H_m / D_m)
    return (1.0 / sqrt(2000.0)) * (C_i * H_m / sqrt(t_u_mm / D_m)) * (sqrt(rho_kg_m3) / sqrt(E_MPa))


def convective_period_s(D_m: float, H_m: float) -> float:
    """Periodo convectivo (oleaje) T_c según API 650 §E.4.5.2.

        K_s = 0,578 / sqrt(tanh(3,68·H/D))        T_c = 1,8 · K_s · sqrt(D)

    (equivale a 2π·sqrt(D/(3,68·g·tanh(3,68·H/D))) con el redondeo de la norma).
    """
    if D_m <= 0 or H_m <= 0:
        raise ValueError("D y H deben ser > 0")
    K_s = 0.578 / sqrt(tanh(3.68 * H_m / D_m))
    return 1.8 * K_s * sqrt(D_m)


def estimate_shell_and_roof_weight_kN(D_m: float, H_shell_m: float, t_shell_mm: float,
                                      t_roof_mm: float = 5.0,
                                      gamma_steel_kN_m3: float = GAMMA_STEEL_KN_M3) -> float:
    """Estimación del peso de manto + techo (acero) que gravita sobre el anclaje [kN].

    Manto cilíndrico de espesor uniforme ``t_shell_mm`` y techo plano de
    ``t_roof_mm`` (5 mm por defecto, el mínimo de API 650 §5.10.2.2). Sin
    accesorios, escaleras ni aislamiento: úsese cuando no se conoce el peso real.
    Es el W_t de §E.6.2.1.1; NO incluye el líquido, cuya contribución
    estabilizante es la del anillo de fondo w_a (``anchorage.annulus_resisting_force_kN_m``).
    """
    if min(D_m, H_shell_m, t_shell_mm, t_roof_mm) <= 0:
        raise ValueError("D, H_shell, t_shell y t_roof deben ser > 0")
    shell = pi * D_m * H_shell_m * (t_shell_mm / 1000.0) * gamma_steel_kN_m3
    roof = pi * (D_m / 2.0) ** 2 * (t_roof_mm / 1000.0) * gamma_steel_kN_m3
    return shell + roof


# ---------------------------------------------------------------------------
# §E.6.1 — masas, alturas, cortante y momento
# ---------------------------------------------------------------------------

def housner_masses(geom: TankGeometry, Sa_i: float, Sa_c: float, *,
                   W_s_kN: float = 0.0, X_s_m: float = 0.0,
                   W_r_kN: float = 0.0, X_r_m: float = 0.0,
                   E_MPa: float = 200_000.0) -> SeismicMasses:
    """Pesos efectivos, alturas, periodos, cortante y momento volcante (API 650 Anexo E).

    Args:
        geom: geometría; ``t_shell_mm`` es el espesor uniforme equivalente t_u.
        Sa_i: coeficiente de aceleración impulsiva A_i (fracción de g, §E.4.6.1,
            ya dividido por R_wi/I).
        Sa_c: coeficiente de aceleración convectiva A_c (fracción de g, §E.4.6.1).
        W_s_kN, X_s_m: peso del manto y altura de su centro de gravedad (opcional;
            entran en el cortante y el momento con A_i, §E.6.1 y §E.6.1.5).
        W_r_kN, X_r_m: peso del techo y altura de su centro de gravedad (opcional).
        E_MPa: módulo del acero del manto para T_i.

    Fórmulas (D/H = razón diámetro/altura de líquido):
        D/H >= 1,333:  W_i/W_p = tanh(0,866·D/H)/(0,866·D/H)     X_i = 0,375·H
        D/H <  1,333:  W_i/W_p = 1 − 0,218·D/H                   X_i = (0,5 − 0,094·D/H)·H
        W_c/W_p = 0,230·(D/H)·tanh(3,67·H/D)
        X_c = H·[1 − (cosh(3,67·H/D) − 1)/((3,67·H/D)·sinh(3,67·H/D))]
        V = sqrt(V_i² + V_c²),  V_i = A_i·(W_s + W_r + W_i),  V_c = A_c·W_c
        M_rw = sqrt([A_i·(W_i·X_i + W_s·X_s + W_r·X_r)]² + [A_c·W_c·X_c]²)
    (alturas sin la presión sobre el fondo: momento en la base del manto, "ringwall").
    """
    geom.validate()
    if Sa_i < 0 or Sa_c < 0:
        raise ValueError("Sa_i y Sa_c deben ser >= 0")
    D, H = geom.D_m, geom.H_l_m
    W_p = geom.W_l_kN
    r = D / H

    if r >= 1.333:
        Wi_over_W = tanh(0.866 * r) / (0.866 * r)
        X_i = 0.375 * H
    else:
        Wi_over_W = 1.0 - 0.218 * r
        X_i = (0.5 - 0.094 * r) * H
    a = 3.67 * H / D
    Wc_over_W = 0.230 * r * tanh(a)
    X_c = H * (1.0 - (cosh(a) - 1.0) / (a * sinh(a)))

    W_i = Wi_over_W * W_p
    W_c = Wc_over_W * W_p

    C_i = impulsive_coefficient_Ci(2.0 * H / D)
    T_i = impulsive_period_s(D, H, geom.t_shell_mm, geom.rho_l_kg_m3, E_MPa)
    T_c = convective_period_s(D, H)

    V_i = Sa_i * (W_s_kN + W_r_kN + W_i)
    V_c = Sa_c * W_c
    V = sqrt(V_i ** 2 + V_c ** 2)
    M_i = Sa_i * (W_i * X_i + W_s_kN * X_s_m + W_r_kN * X_r_m)
    M_c = Sa_c * W_c * X_c
    M = sqrt(M_i ** 2 + M_c ** 2)

    return SeismicMasses(
        W_i_kN=W_i, W_c_kN=W_c, h_i_m=X_i, h_c_m=X_c,
        T_i_s=T_i, T_c_s=T_c, M_overturn_kNm=M,
        V_base_kN=V, C_i=C_i,
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
    "impulsive_coefficient_Ci", "impulsive_period_s", "convective_period_s",
    "estimate_shell_and_roof_weight_kN", "G_M_S2", "GAMMA_STEEL_KN_M3",
]
