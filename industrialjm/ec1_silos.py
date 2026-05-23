"""EN 1991-4:2006 — Actions on silos and tanks.

Implementa presiones de llenado (Janssen, §5.2), clasificación de
esbeltez (§1.5.31-33), factores de descarga Ch/Cw (§5.3, Tablas 5.2/5.3),
carga parcheada asimétrica (§5.2.4) y presiones de flow funnel
(§5.2.3 / Anexo G) para silos esbeltos.

Las variables siguen la notación de EN 1991-4:
- ``gamma`` : peso específico del sólido a granel γ [kN/m³].
- ``mu``    : coeficiente de rozamiento con la pared μ = tan φ_w.
- ``K``     : razón de presión lateral/vertical K = p_h / p_v.
- ``d_h``   : diámetro hidráulico = 4·A/U (D para circular).
- ``z``     : profundidad medida desde la superficie equivalente (m).
"""
from __future__ import annotations

from math import exp, pi
from typing import Literal

Slenderness = Literal["slender", "intermediate", "squat", "retaining"]


# ---------------------------------------------------------------------------
# §5.2 — Presiones de llenado (Janssen)
# ---------------------------------------------------------------------------
def janssen_pressure(
    z: float,
    gamma: float,
    mu: float,
    K: float,
    d_h: float,
) -> tuple[float, float]:
    """Presión horizontal y vertical de Janssen (EN 1991-4 §5.2.1.1).

    La profundidad característica de Janssen es::

        z_o = 1/(K·μ) · A/U = d_h / (4·K·μ)

    de donde::

        p_ho(z) = γ·K·z_o · (1 - exp(-z/z_o))
        p_vo(z) =  γ·z_o   · (1 - exp(-z/z_o))   =  p_ho / K

    Parameters
    ----------
    z : float
        Profundidad bajo la superficie equivalente [m]; ``z >= 0``.
    gamma : float
        Peso específico γ del material a granel [kN/m³].
    mu : float
        Coeficiente de fricción sólido-pared μ = tan φ_w.
    K : float
        Razón de presión lateral K = p_h/p_v (típ. 0.4–0.6).
    d_h : float
        Diámetro hidráulico ``4·A/U`` [m] (D para sección circular).

    Returns
    -------
    (p_h, p_v) : tuple[float, float]
        Presión horizontal y vertical en la pared [kPa] (γ en kN/m³).
    """
    if z < 0:
        raise ValueError("z debe ser >= 0")
    if mu <= 0 or K <= 0 or d_h <= 0:
        raise ValueError("mu, K, d_h deben ser > 0")
    z_o = d_h / (4.0 * K * mu)
    factor = 1.0 - exp(-z / z_o)
    p_h = gamma * K * z_o * factor
    p_v = gamma * z_o * factor
    return p_h, p_v


# ---------------------------------------------------------------------------
# §1.5.31-33 — Clasificación geométrica
# ---------------------------------------------------------------------------
def silo_slenderness_class(h_c: float, d_c: float) -> Slenderness:
    """Clasifica el silo por esbeltez (EN 1991-4 §1.5.31-33).

    - ``h_c/d_c >= 2``       : silo esbelto ("slender")
    - ``1 <= h_c/d_c < 2``   : silo intermedio ("intermediate")
    - ``0.4 <= h_c/d_c < 1`` : silo achaparrado ("squat")
    - ``h_c/d_c < 0.4``      : depósito ("retaining")
    """
    if h_c <= 0 or d_c <= 0:
        raise ValueError("h_c y d_c deben ser > 0")
    r = h_c / d_c
    if r >= 2.0:
        return "slender"
    if r >= 1.0:
        return "intermediate"
    if r >= 0.4:
        return "squat"
    return "retaining"


# ---------------------------------------------------------------------------
# §5.3 — Factores de amplificación de descarga (Tablas 5.2/5.3)
# ---------------------------------------------------------------------------
def discharge_pressure_factors(slenderness: Slenderness) -> tuple[float, float]:
    """Multiplicadores C_h, C_w de descarga (EN 1991-4 §5.3, Tabla 5.2).

    Aplicados a las presiones de llenado para obtener ``p_he`` y ``p_we``::

        p_he(z) = C_h · p_hf(z)
        p_we(z) = C_w · p_wf(z)

    Returns
    -------
    (C_h, C_w)
        Valores recomendados de Tabla 5.2 (clase de evaluación 2).
    """
    table = {
        "slender":      (1.15, 1.10),
        "intermediate": (1.15, 1.10),
        "squat":        (1.00, 1.00),
        "retaining":    (1.00, 1.00),
    }
    if slenderness not in table:
        raise ValueError(f"Clase desconocida: {slenderness!r}")
    return table[slenderness]


# ---------------------------------------------------------------------------
# §5.2.4 — Carga parcheada asimétrica
# ---------------------------------------------------------------------------
def patch_load(
    z: float,
    d_c: float,
    slenderness: Slenderness,
    gamma: float | None = None,
    K: float | None = None,
    z_o: float | None = None,
) -> tuple[float, float]:
    """Carga parcheada de llenado p_pf (EN 1991-4 §5.2.4).

    Genera dos cargas parcheadas opuestas (signo + / signo −) sobre
    una banda axial de altura ``s = π·d_c/16`` (≈ 0.2·d_c).
    Para silos esbeltos clase 2 se adopta:

        p_pf =  C_pf · γ · K · z_o · (1 - exp(-z/z_o)) · 0.21
        p_pf,opuesto = - p_pf

    con C_pf = 0.5 (slender), 0.21 (intermediate), 0 (squat).
    El resultado son las dos amplitudes (+, −) en kPa sobre la pared.
    """
    if z < 0 or d_c <= 0:
        raise ValueError("z>=0 y d_c>0")
    coef = {"slender": 0.5, "intermediate": 0.21, "squat": 0.0, "retaining": 0.0}
    c_pf = coef[slenderness]
    if gamma is None or K is None or z_o is None:
        amp = c_pf
    else:
        if gamma <= 0 or K <= 0 or z_o <= 0:
            raise ValueError("gamma, K, z_o deben ser > 0")
        p_ho = gamma * K * z_o * (1.0 - exp(-z / z_o))
        amp = c_pf * p_ho * 0.21
    return (+amp, -amp)


# ---------------------------------------------------------------------------
# §5.2.3 / Anexo G — Flow funnel en silos esbeltos
# ---------------------------------------------------------------------------
def flow_pressure_funnel(
    z: float,
    h_c: float,
    d_c: float,
    gamma: float,
    mu: float,
    K: float,
) -> float:
    """Presión horizontal en el flow funnel (EN 1991-4 Anexo G).

    Para silos esbeltos en descarga másica, el canal de flujo
    reduce la presión sobre la pared en su interior::

        p_hce(z) = p_hf(z) · (1 - G·exp(-z/z_o))

    con ``G = 0.1`` (Anexo G, ec. G.7) valor recomendado para sólidos
    de fricción media. Devuelve la presión horizontal corregida [kPa].
    """
    cls = silo_slenderness_class(h_c, d_c)
    if cls != "slender":
        # Sólo aplica plenamente a silos esbeltos.
        return janssen_pressure(z, gamma, mu, K, d_c)[0]
    p_h, _ = janssen_pressure(z, gamma, mu, K, d_c)
    z_o = d_c / (4.0 * K * mu)
    G = 0.10
    return p_h * (1.0 - G * exp(-z / z_o))


__all__ = [
    "janssen_pressure",
    "silo_slenderness_class",
    "discharge_pressure_factors",
    "patch_load",
    "flow_pressure_funnel",
]
