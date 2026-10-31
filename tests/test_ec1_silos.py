"""Tests EN 1991-4 §5 — silos y depósitos (módulo ec1_silos)."""
from math import exp, isclose

import pytest

from plantstruct.ec1_silos import (
    discharge_pressure_factors,
    flow_pressure_funnel,
    janssen_pressure,
    patch_load,
    silo_slenderness_class,
)


# --- §5.2 Janssen ----------------------------------------------------------
def test_janssen_z0_is_zero():
    p_h, p_v = janssen_pressure(0.0, gamma=8.0, mu=0.4, K=0.5, d_h=4.0)
    assert isclose(p_h, 0.0, abs_tol=1e-12)
    assert isclose(p_v, 0.0, abs_tol=1e-12)


def test_janssen_asymptote_inf():
    """z→∞ ⇒ p_h → γ·K·z_o."""
    gamma, mu, K, d_h = 8.0, 0.4, 0.5, 4.0
    z_o = d_h / (4.0 * K * mu)
    p_h, _ = janssen_pressure(1e6, gamma, mu, K, d_h)
    assert isclose(p_h, gamma * K * z_o, rel_tol=1e-9)


def test_janssen_pv_equals_ph_over_K():
    p_h, p_v = janssen_pressure(5.0, gamma=8.0, mu=0.4, K=0.5, d_h=4.0)
    assert isclose(p_v, p_h / 0.5, rel_tol=1e-12)


def test_janssen_invalid_inputs():
    with pytest.raises(ValueError):
        janssen_pressure(-1.0, 8.0, 0.4, 0.5, 4.0)
    with pytest.raises(ValueError):
        janssen_pressure(1.0, 8.0, 0.0, 0.5, 4.0)


# --- §1.5 esbeltez ---------------------------------------------------------
def test_slender_silo_H20_D5():
    assert silo_slenderness_class(h_c=20.0, d_c=5.0) == "slender"


def test_slenderness_categories():
    assert silo_slenderness_class(6.0, 5.0) == "intermediate"
    assert silo_slenderness_class(3.0, 5.0) == "squat"
    assert silo_slenderness_class(1.0, 5.0) == "retaining"


# --- §5.3 Ch/Cw ------------------------------------------------------------
def test_discharge_factor_slender_class2():
    C_h, C_w = discharge_pressure_factors("slender")
    assert C_h == pytest.approx(1.15)
    assert C_w == pytest.approx(1.10)


def test_discharge_factor_squat_is_unity():
    C_h, C_w = discharge_pressure_factors("squat")
    assert C_h == 1.0 and C_w == 1.0


# --- §5.2.4 carga parcheada ------------------------------------------------
def test_patch_load_asymmetric_sign():
    pos, neg = patch_load(z=5.0, d_c=5.0, slenderness="slender")
    assert pos > 0 and neg < 0
    assert isclose(pos, -neg, rel_tol=1e-12)


def test_patch_load_zero_for_squat():
    pos, neg = patch_load(z=5.0, d_c=5.0, slenderness="squat")
    assert pos == 0.0 and neg == 0.0


# --- §Anexo G flow funnel --------------------------------------------------
def test_flow_funnel_reduces_pressure_for_slender():
    args = dict(z=10.0, h_c=20.0, d_c=5.0, gamma=8.0, mu=0.4, K=0.5)
    p_h_jan, _ = janssen_pressure(args["z"], args["gamma"], args["mu"], args["K"], args["d_c"])
    p_h_fun = flow_pressure_funnel(**args)
    assert p_h_fun < p_h_jan  # canal de flujo reduce presión


# --- Caso 5: silo cuadrado equivalente -------------------------------------
def test_square_silo_equivalent_diameter():
    """Silo cuadrado de lado B: A=B², U=4B → d_h = 4A/U = B.

    Debe coincidir con un silo circular de d_h = B.
    """
    B = 4.0
    A = B * B
    U = 4.0 * B
    d_h_square = 4.0 * A / U  # = B
    p_square, _ = janssen_pressure(5.0, gamma=8.0, mu=0.4, K=0.5, d_h=d_h_square)
    p_circ, _ = janssen_pressure(5.0, gamma=8.0, mu=0.4, K=0.5, d_h=B)
    assert isclose(p_square, p_circ, rel_tol=1e-12)
