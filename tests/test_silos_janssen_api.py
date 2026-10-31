"""Tests de integración y golden analítico para presiones en silos según EN 1991-4.

Norma: EN 1991-4:2006 §1.5.31-33 (Clasificación de esbeltez), §5.2.1.1 (Janssen) y §5.3 (Tabla 5.2).
"""
import math
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from plantstruct.api.app import create_router
from plantstruct.ec1_silos import (
    janssen_pressure, silo_slenderness_class, discharge_pressure_factors,
)


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(create_router())
    return TestClient(app)


def test_silo_slenderness_classification_golden():
    """Golden de clasificación por esbeltez EN 1991-4 §1.5.31-33."""
    # hc/dc >= 2 -> slender
    assert silo_slenderness_class(h_c=20.0, d_c=6.0) == "slender"
    # 1 <= hc/dc < 2 -> intermediate
    assert silo_slenderness_class(h_c=7.5, d_c=5.0) == "intermediate"
    # 0.4 <= hc/dc < 1 -> squat
    assert silo_slenderness_class(h_c=4.0, d_c=6.0) == "squat"
    # hc/dc < 0.4 -> retaining
    assert silo_slenderness_class(h_c=1.5, d_c=5.0) == "retaining"


def test_silo_janssen_pressure_hand_calculation_golden():
    """Golden analítico exacto derivado a mano según EN 1991-4 §5.2.1.1.

    Silo esbelto de grano (D=6.0 m, gamma=8.5 kN/m³, mu=0.38, K=0.54):
      z_o = D / (4 * K * mu) = 6.0 / (4 * 0.54 * 0.38) = 7.30994 m
      A z = 10.0 m:
        factor = 1 - exp(-10.0 / 7.30994) = 0.745377
        p_hf = gamma * K * z_o * factor = 25.008 kPa
        p_vf = p_hf / K = 46.311 kPa
      Descarga slender (Tabla 5.2):
        C_h = 1.15, C_w = 1.10
        p_he = 1.15 * 25.008 = 28.759 kPa
    """
    gamma = 8.5
    mu = 0.38
    K = 0.54
    D = 6.0
    z = 10.0

    z_o = D / (4.0 * K * mu)
    factor = 1.0 - math.exp(-z / z_o)
    expected_ph = gamma * K * z_o * factor
    expected_pv = gamma * z_o * factor

    p_h, p_v = janssen_pressure(z=z, gamma=gamma, mu=mu, K=K, d_h=D)
    assert p_h == pytest.approx(expected_ph, rel=1e-6)
    assert p_v == pytest.approx(expected_pv, rel=1e-6)
    assert p_h == pytest.approx(25.008, rel=1e-3)
    assert p_v == pytest.approx(46.311, rel=1e-3)

    Ch, Cw = discharge_pressure_factors("slender")
    assert Ch == 1.15
    assert Cw == 1.10


def test_silo_janssen_api_endpoint(client):
    """Verifica endpoint HTTP /api/industrial/silos/janssen."""
    payload = {
        "height_m": 20.0,
        "diameter_m": 6.0,
        "depth_z_m": 10.0,
        "gamma_kN_m3": 8.5,
        "mu_friction": 0.38,
        "K_ratio": 0.54,
    }
    resp = client.post("/api/industrial/silos/janssen", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["slenderness"] == "slender"
    assert data["aspect_ratio_hc_over_dc"] == pytest.approx(20.0 / 6.0, rel=1e-4)
    assert data["p_hf_filling_horizontal_kPa"] == pytest.approx(25.008, rel=1e-3)
    assert data["p_vf_filling_vertical_kPa"] == pytest.approx(46.311, rel=1e-3)
    assert data["C_h_discharge_factor"] == 1.15
    assert data["p_he_discharge_horizontal_kPa"] == pytest.approx(28.759, rel=1e-3)
