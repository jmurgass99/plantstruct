"""Golden tests y caracterización analítica de estructuras industriales anclados a fichas del master.

Fichas ancla
------------
* **W01046 / W01096 / W01112 — Depósitos cilíndricos y láminas de revolución**:
  - Tensión circunferencial de membrana (Hoop tension):
      T = gamma * (H - y) * r
  - Ejemplo numérico resuelto en W01046 / W01096:
      H = 10 m, r = 5 m, gamma = 10000 N/m3 -> T_base = 10000 * 10 * 5 = 500,000 N/m (500 kN/m).
  - Tracción en anillo de borde bajo presión interior: T = R * P.

* **API 650 (1-Foot Method) — Tanques de almacenamiento cilíndricos**:
  - Ecuaciones de diseño §5.6.3.2:
      t_d = 4.9 * D * (H - 0.3) * G / S_d + CA
      t_t = 4.9 * D * (H - 0.3) / S_t
  - Espesor mínimo nominal según Tabla 5.2 (D < 15m -> 5mm, 15 <= D < 36m -> 6mm, etc.).

* **W00225 / EN 1991-4 — Silos cilíndricos y teoría de presiones de Janssen**:
  - Radio hidráulico de silo circular A/U = d_c / 4.
  - Profundidad característica de Janssen: z0 = (A / U) / (K * mu) = d_c / (4 * K * mu).
  - Presión asintótica horizontal: p_h0 = gamma * K * z0 = gamma * (A / U) / mu.
  - Presión horizontal: p_hf(z) = p_h0 * (1 - exp(-z / z0)).
  - Presión vertical: p_vf(z) = p_hf(z) / K = gamma * z0 * (1 - exp(-z / z0)).
  - Fricción con pared: p_wf(z) = mu * p_hf(z).

* **EN 1991-1-4 Anexo E — Chimeneas industriales y desprendimiento de vórtices**:
  - Velocidad crítica de resonancia por vórtices de Von Kármán: v_crit = (b * n_1) / St (St = 0.18).

* **W00262 / ASME BPVC Sec VIII Div 1 — Esferas de almacenamiento GLP/GPL**:
  - Tensión de membrana esférica pura: sigma = P * R / (2 * t * E).
"""
from __future__ import annotations
from plantstruct.tanks import hoop_tension

import math
import pytest

from plantstruct.tanks.shell_design import (
    shell_thickness_one_foot,
    ShellCourseResult,
)
from plantstruct.ec1_silos import (
    janssen_pressure,
    silo_slenderness_class,
)
from plantstruct.silos_en1991_4 import (
    SiloInput,
    janssen_pressures,
)
from plantstruct.chimneys import (
    ChimneyInput,
    evaluate_chimney,
)
from plantstruct.esferas_gpl import (
    EsferaGLPInput,
    disenar_esfera,
)


class TestW01046CylindricalTankHoopMembraneGolden:
    """Validación del modelo canónico de tensión circunferencial de depósitos cilíndricos."""

    def test_w01046_hoop_tension_at_base(self):
        """Ejemplo resuelto W01046: H=10m, r=5m, gamma=10,000 N/m3 -> T_base = 500 kN/m."""
        H = 10.0       # m
        r = 5.0        # m (radio)
        gamma = 10000.0  # N/m3

        # Llamada a la funcion implementada en plantstruct.tanks.hoop_tension
        T_base_N_m = hoop_tension(radius_m=r, liquid_height_m=H, gamma_N_m3=gamma, elevation_m=0.0)
        T_base_kN_m = T_base_N_m / 1000.0

        assert T_base_N_m == pytest.approx(500000.0, rel=1e-9)
        assert T_base_kN_m == pytest.approx(500.0, rel=1e-9)

        # A media altura (y = 5m), la tensión debe ser exactamente la mitad (250 kN/m)
        T_mid_N_m = hoop_tension(radius_m=r, liquid_height_m=H, gamma_N_m3=gamma, elevation_m=5.0)
        assert (T_mid_N_m / 1000.0) == pytest.approx(250.0, rel=1e-9)

        # En la superficie libre (y = H = 10m), la tensión es nula
        T_top_N_m = hoop_tension(radius_m=r, liquid_height_m=H, gamma_N_m3=gamma, elevation_m=10.0)
        assert T_top_N_m == pytest.approx(0.0, abs=1e-9)

    def test_ring_tension_under_internal_pressure(self):
        """Fórmula de anillo W01046 / W01096: T = R * P."""
        R = 4.0      # m
        P = 150.0    # kPa (kN/m2)
        T_N_m = hoop_tension(radius_m=R, liquid_height_m=0.0, internal_pressure_kPa=P)
        assert (T_N_m / 1000.0) == pytest.approx(600.0, rel=1e-9)


class TestAPI650ShellDesignOneFootMethodGolden:
    """Validación del método de 1 pie (1-Foot Method) según API 650 §5.6.3.2."""

    def test_api650_course_thickness_benchmark(self):
        """Tanque D=20m, H=12m, G=1.0, Sd=160 MPa, St=171 MPa, CA=1.5mm."""
        D = 20.0
        H = 12.0
        G = 1.0
        Sd = 160.0
        St = 171.0
        CA = 1.5

        res = shell_thickness_one_foot(D_m=D, H_m=H, G=G, Sd_MPa=Sd, St_MPa=St, CA_mm=CA)

        # t_d = 4.9 * 20 * (12 - 0.3) * 1.0 / 160 + 1.5 = 1146.6 / 160 + 1.5 = 7.16625 + 1.5 = 8.66625 mm
        expected_td = (4.9 * D * (H - 0.3) * G / Sd) + CA
        # t_t = 4.9 * 20 * (12 - 0.3) / 171 = 1146.6 / 171 = 6.70526 mm
        expected_tt = 4.9 * D * (H - 0.3) / St

        assert res.t_design_mm == pytest.approx(expected_td, rel=1e-5)
        assert res.t_test_mm == pytest.approx(expected_tt, rel=1e-5)
        # Para D=20m (15 <= D < 36), t_min_nominal = 6.0 mm
        assert res.t_min_nominal_mm == 6.0
        assert res.t_required_mm == pytest.approx(max(expected_td, expected_tt, 6.0), rel=1e-5)
        assert res.governing == "diseno"

    @pytest.mark.parametrize("diameter, expected_tmin", [
        (10.0, 5.0),
        (25.0, 6.0),
        (45.0, 8.0),
        (60.0, 10.0),
    ])
    def test_api650_min_nominal_thickness_table(self, diameter, expected_tmin):
        """Verifica la tabla 5.2 de espesores mínimos constructivos de API 650."""
        res = shell_thickness_one_foot(D_m=diameter, H_m=1.0, G=0.1, Sd_MPa=500.0, CA_mm=0.0)
        assert res.t_min_nominal_mm == expected_tmin


class TestEN19914JanssenSiloPressuresGolden:
    """Validación analítica de la teoría de presiones de silo de Janssen (EN 1991-4)."""

    def test_janssen_analytical_closed_form(self):
        """Silo D=6m (dh=6m), H=24m, gamma=8.5 kN/m3, mu=0.364, K=0.52.

        z0 = dh / (4 * K * mu) = 6 / (4 * 0.52 * 0.364) = 7.92518 m.
        ph0 = gamma * K * z0 = 35.029 kPa.
        """
        gamma = 8.5
        mu = 0.364
        K = 0.52
        dh = 6.0

        z0_expected = dh / (4.0 * K * mu)
        ph0_expected = gamma * K * z0_expected

        z = 10.0
        ph, pv = janssen_pressure(z=z, gamma=gamma, mu=mu, K=K, d_h=dh)

        expected_ph = ph0_expected * (1.0 - math.exp(-z / z0_expected))
        expected_pv = expected_ph / K

        assert ph == pytest.approx(expected_ph, rel=1e-6)
        assert pv == pytest.approx(expected_pv, rel=1e-6)
        # La presión vertical de Janssen (48.29 kPa) es mucho menor que la hidrostática (85.0 kPa)
        assert pv < gamma * z

    def test_janssen_asymptotic_behavior_deep_silo(self):
        """A gran profundidad z >> z0, la presión vertical satura asintóticamente a gamma * z0."""
        gamma = 10.0
        mu = 0.40
        K = 0.50
        dh = 4.0

        # z0 = 4 / (4 * 0.5 * 0.4) = 5.0 m
        # pv_asymptotic = gamma * z0 = 50.0 kPa
        z_deep = 100.0  # 20 * z0
        ph_deep, pv_deep = janssen_pressure(z=z_deep, gamma=gamma, mu=mu, K=K, d_h=dh)

        assert pv_deep == pytest.approx(50.0, rel=1e-4)
        assert ph_deep == pytest.approx(50.0 * K, rel=1e-4)

    def test_silo_slenderness_classification(self):
        """Clasificación de esbeltez de silos según EN 1991-4 §1.5.31-33."""
        # Esbelto: h_c / d_c >= 2.0
        assert silo_slenderness_class(h_c=20.0, d_c=6.0) == "slender"
        # Bajo / Squat: h_c / d_c < 1.0
        assert silo_slenderness_class(h_c=4.0, d_c=8.0) == "squat"


class TestEN199114ChimneysVortexSheddingGolden:
    """Validación de vibraciones por desprendimiento de vórtices en chimeneas (EN 1991-1-4 Anexo E)."""

    def test_chimney_vortex_shedding_critical_velocity(self):
        """Chimenea D=2.5m, H=45m, t=10mm, Vb=26 m/s."""
        inp = ChimneyInput(
            D_outer_m=2.5,
            H_m=45.0,
            t_shell_mm=10.0,
            Vb_m_per_s=26.0,
            rho_steel_kg_m3=7850.0,
            E_MPa=210000.0,
        )
        res = evaluate_chimney(inp)

        assert res.f1_Hz > 0.0
        assert res.T1_s == pytest.approx(1.0 / res.f1_Hz, rel=1e-6)
        # v_crit = D * f1 / St (con St = 0.18)
        expected_vcrit = (2.5 * res.f1_Hz) / 0.18
        assert res.v_critical_m_per_s == pytest.approx(expected_vcrit, rel=1e-5)
        assert res.aspect_ratio == pytest.approx(45.0 / 2.5, rel=1e-6)


class TestASMEBPVCLPGSphericalVesselGolden:
    """Validación de recipientes esféricos de almacenamiento de GLP/GPL (W00262)."""

    def test_lpg_sphere_shell_thickness(self):
        """Esfera GLP D=16m (R=8m), P=16 bar (1.6 MPa), S=138 MPa, E=1.0."""
        inp = EsferaGLPInput(
            D_m=16.0,
            P_design_bar=16.0,
            rho_liquido_kg_m3=580.0,
            fill_pct=0.85,
            S_allow_MPa=138.0,
            E_joint=1.0,
            n_columnas=8,
            code="US",
        )
        res = disenar_esfera(inp)

        assert res.t_min_mm > 0.0
        assert res.W_total_kN > 0.0
        assert res.P_col_kN == pytest.approx(res.W_total_kN / 8.0, rel=1e-3)
        assert res.code == "US"
