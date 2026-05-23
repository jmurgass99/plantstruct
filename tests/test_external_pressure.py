"""Tests external pressure."""
import pytest
from industrialjm.external_pressure import (
    ExtPressureInput, critical_external_pressure, max_unstiffened_length_m,
)


def test_typical_tank_vacuum():
    # tanque 10m diámetro, 8mm pared, 5m altura, vacío parcial 2 kPa
    r = critical_external_pressure(ExtPressureInput(D_m=10.0, t_mm=8.0, L_m=5.0,
                                                    P_ext_kPa=2.0, code="USA"))
    assert r.P_cr_kPa > 0
    assert r.factor_of_safety > 0


def test_thicker_wall_higher_Pcr():
    r1 = critical_external_pressure(ExtPressureInput(D_m=10, t_mm=6, L_m=5))
    r2 = critical_external_pressure(ExtPressureInput(D_m=10, t_mm=10, L_m=5))
    assert r2.P_cr_kPa > r1.P_cr_kPa


def test_multi_code_required_FS():
    for code in ("USA", "EU", "NSR", "AS", "SG"):
        r = critical_external_pressure(ExtPressureInput(D_m=10, t_mm=8, L_m=5,
                                                        P_ext_kPa=1.0, code=code))
        assert r.required_FS > 0


def test_max_length_inverse():
    L = max_unstiffened_length_m(D_m=10, t_mm=8, P_ext_kPa=1.0, code="USA")
    assert L > 0
    # Verifica que a esa L el FS=3
    r = critical_external_pressure(ExtPressureInput(D_m=10, t_mm=8, L_m=L,
                                                    P_ext_kPa=1.0, code="USA"))
    assert r.factor_of_safety == pytest.approx(3.0, rel=1e-2)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        critical_external_pressure(ExtPressureInput(D_m=0, t_mm=8, L_m=5))
    with pytest.raises(ValueError):
        critical_external_pressure(ExtPressureInput(D_m=10, t_mm=8, L_m=5, code="ZZ"))
