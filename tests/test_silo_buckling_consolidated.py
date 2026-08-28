"""Tests for consolidated silo buckling in IndustrialJm."""
import pytest
from industrialjm.silo_buckling import meridional_critical_stress, imperfection_alpha, buckling_resistance


def test_meridional_critical_stress_analytical():
    E = 210000.0  # MPa
    t = 8.0  # mm
    r = 2500.0  # mm
    sigma_cr = meridional_critical_stress(E=E, t=t, r=r)
    # sigma_cr = 0.605 * 210000 * 8 / 2500 = 406.56 MPa
    assert pytest.approx(sigma_cr, rel=1e-4) == 406.56


def test_imperfection_alpha_quality_classes():
    alpha_a = imperfection_alpha(r=2500.0, t=8.0, quality_class="A")
    alpha_c = imperfection_alpha(r=2500.0, t=8.0, quality_class="C")
    assert alpha_a > alpha_c
    assert 0.0 < alpha_a < 1.0


def test_buckling_resistance_returns_dict():
    res = buckling_resistance(E=210000.0, t=8.0, r=2500.0, quality_class="B")
    assert "sigma_cr" in res and "alpha" in res and "sigma_Rk" in res
    assert res["sigma_Rk"] == pytest.approx(res["alpha"] * res["sigma_cr"])
