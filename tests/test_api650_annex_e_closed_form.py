# -*- coding: utf-8 -*-
"""API 650 Anexo E: fracciones de Housner, alturas, periodos, SRSS y relación J anclados a mano.

Hasta 2026-10-31 ``housner_masses`` daba T_i = 0,006 s para un tanque de 20 m
(faltaban el 1/sqrt(2000) y el sqrt(t_u/D) de §E.4.5.1), solo tenía la rama
D/H >= 1,333, acotaba X_c a 0,4–0,7·H con una expresión propia y sumaba los
momentos linealmente. ``check_anchorage_J`` dividía por el peso total en vez de
por el peso por unidad de perímetro (factor π·D) y la memoria le pasaba el peso
del líquido. ``asce_15_7`` tenía D/H invertido en la fracción convectiva.

Los valores de referencia están calculados a mano con las fórmulas de la norma:

    D = 20 m, H = 15 m (D/H = 1,333):  W_i/W = 0,7096  W_c/W = 0,3042
                                        X_i/H = 0,375   X_c/H = 0,6803
    D = 10 m, H = 8 m  (D/H = 1,25):   W_i/W = 0,7275  X_i/H = 0,3825
    T_i(D = 20, H = 15, t_u = 8 mm, agua, E = 200 000 MPa) = 0,2272 s (C_i = 6,06)
    T_c(D = 20, H = 15) = 1,8·0,5803·sqrt(20) = 4,6715 s
    w_a(t_a = 8, F_y = 250, H = 15, D = 20) = 48,50 kN/m
"""
from __future__ import annotations

from math import pi, sqrt

import pytest

from plantstruct.asce7_15_7 import TankASCEInput, asce_15_7
from plantstruct.tanks import (
    AnchorageJInput,
    TankGeometry,
    annulus_resisting_force_kN_m,
    check_anchorage_J,
    convective_period_s,
    estimate_shell_and_roof_weight_kN,
    housner_masses,
    impulsive_coefficient_Ci,
    impulsive_period_s,
)


def test_housner_fractions_and_heights_D_over_H_1333():
    g = TankGeometry(D_m=20.0, H_l_m=15.0, t_shell_mm=8.0)
    m = housner_masses(g, Sa_i=0.3, Sa_c=0.1)
    assert m.W_i_kN / g.W_l_kN == pytest.approx(0.7096, rel=1e-3)
    assert m.W_c_kN / g.W_l_kN == pytest.approx(0.3042, rel=1e-3)
    assert m.h_i_m / 15.0 == pytest.approx(0.375, abs=1e-9)
    assert m.h_c_m / 15.0 == pytest.approx(0.6803, rel=1e-3)


def test_housner_tall_tank_branch():
    g = TankGeometry(D_m=10.0, H_l_m=8.0, t_shell_mm=8.0)
    m = housner_masses(g, Sa_i=0.3, Sa_c=0.1)
    assert m.W_i_kN / g.W_l_kN == pytest.approx(1.0 - 0.218 * 1.25, rel=1e-9)
    assert m.W_i_kN / g.W_l_kN == pytest.approx(0.7275, rel=1e-3)
    assert m.h_i_m / 8.0 == pytest.approx(0.5 - 0.094 * 1.25, rel=1e-9)


@pytest.mark.safety_critical
def test_impulsive_period_api650_E451():
    T_i = impulsive_period_s(20.0, 15.0, 8.0, 1000.0, 200_000.0)
    assert T_i == pytest.approx(0.2272, rel=2e-3)
    assert impulsive_coefficient_Ci(1.5) == pytest.approx(6.06)
    # identidad de la fórmula de la norma
    C_i = impulsive_coefficient_Ci(2 * 15.0 / 20.0)
    assert T_i * sqrt(2000.0) * sqrt(8.0 / 20.0) * sqrt(200_000.0) / (C_i * 15.0 * sqrt(1000.0)) == pytest.approx(1.0)
    m = housner_masses(TankGeometry(D_m=20.0, H_l_m=15.0, t_shell_mm=8.0), 0.3, 0.1)
    assert m.T_i_s == pytest.approx(T_i)
    assert 0.1 < m.T_i_s < 0.4          # rango físico de tanques de acero medianos


def test_convective_period_api650_E452():
    assert convective_period_s(20.0, 15.0) == pytest.approx(4.6715, rel=1e-3)
    # redondeo de la norma frente a la forma física 2π·sqrt(D/(3,68·g·tanh))
    from math import tanh
    fis = 2 * pi * sqrt(20.0 / (3.68 * 9.80665 * tanh(3.68 * 15.0 / 20.0)))
    assert convective_period_s(20.0, 15.0) == pytest.approx(fis, rel=6e-3)


def test_overturning_and_shear_are_srss():
    g = TankGeometry(D_m=20.0, H_l_m=15.0, t_shell_mm=8.0)
    mi = housner_masses(g, Sa_i=0.3, Sa_c=0.0)
    mc = housner_masses(g, Sa_i=0.0, Sa_c=0.1)
    m = housner_masses(g, Sa_i=0.3, Sa_c=0.1)
    assert mi.M_overturn_kNm == pytest.approx(0.3 * mi.W_i_kN * mi.h_i_m)
    assert m.M_overturn_kNm == pytest.approx(sqrt(mi.M_overturn_kNm ** 2 + mc.M_overturn_kNm ** 2))
    assert m.V_base_kN == pytest.approx(sqrt((0.3 * m.W_i_kN) ** 2 + (0.1 * m.W_c_kN) ** 2))
    # manto y techo entran con A_i
    ms = housner_masses(g, Sa_i=0.3, Sa_c=0.0, W_s_kN=600.0, X_s_m=8.0, W_r_kN=120.0, X_r_m=16.0)
    assert ms.M_overturn_kNm == pytest.approx(0.3 * (mi.W_i_kN * mi.h_i_m + 600.0 * 8.0 + 120.0 * 16.0))
    assert ms.V_base_kN == pytest.approx(0.3 * (mi.W_i_kN + 720.0))


def test_shell_and_roof_weight_estimate():
    w = estimate_shell_and_roof_weight_kN(20.0, 16.0, 8.0)
    assert w == pytest.approx(pi * 20 * 16 * 0.008 * 78.5 + pi * 100 * 0.005 * 78.5, rel=1e-9)
    assert w == pytest.approx(754.6, rel=1e-3)


def test_annulus_resisting_force_E62111():
    assert annulus_resisting_force_kN_m(8.0, 250.0, 15.0, 1.0, 20.0) == pytest.approx(48.50, rel=1e-3)
    # con un anillo grueso manda el tope 201,1·H·D·G_e
    assert annulus_resisting_force_kN_m(40.0, 250.0, 15.0, 1.0, 20.0) == pytest.approx(201.1 * 15 * 20 / 1000.0)


@pytest.mark.safety_critical
def test_J_uses_force_per_unit_circumference():
    D, W_t = 10.0, 1000.0
    w_t = W_t / (pi * D)
    r = check_anchorage_J(AnchorageJInput(D_m=D, M_rw_kNm=D ** 2 * w_t, W_t_kN=W_t))
    assert r.J == pytest.approx(1.0)
    assert r.anchorage_type == "conditioned"
    assert r.w_t_kN_m == pytest.approx(w_t)
    # el anillo de fondo reduce J y el A_v lo aumenta
    r_a = check_anchorage_J(AnchorageJInput(D_m=D, M_rw_kNm=D ** 2 * w_t, W_t_kN=W_t, w_a_kN_m=w_t))
    assert r_a.J == pytest.approx(0.5)
    r_v = check_anchorage_J(AnchorageJInput(D_m=D, M_rw_kNm=D ** 2 * w_t, W_t_kN=W_t, A_v=0.14))
    assert r_v.J == pytest.approx(1.0 / (1.0 - 0.4 * 0.14))


def test_asce_15_7_convective_fraction_and_Sac_cap():
    r = asce_15_7(TankASCEInput(D_m=20.0, H_l_m=10.0, Sds=1.0, Sd1=0.6))
    Wl = pi * 100 * 10 * 1000 * 9.80665 / 1000.0
    assert r.Wc_kN / Wl == pytest.approx(0.4374, rel=1e-3)      # 0,230·(D/H)·tanh(3,68·H/D)
    assert r.Wi_kN / Wl == pytest.approx(0.5423, rel=1e-3)
    assert r.Sac_g == pytest.approx(min(1.5 * 0.6 / r.Tc_s, 1.5))
    assert r.Vc_kN == pytest.approx(r.Sac_g * 1.5 / 1.5 * r.Wc_kN)
    assert r.V_total_kN == pytest.approx(sqrt(r.Vi_kN ** 2 + r.Vc_kN ** 2))
    # con espesor, T_i sale de API 650 §E.4.5.1
    r2 = asce_15_7(TankASCEInput(D_m=20.0, H_l_m=15.0, t_shell_mm=8.0))
    assert r2.Ti_s == pytest.approx(0.2272, rel=2e-3)
    assert r.Ti_s == 0.0


def test_anchor_codes_uncracked_uses_psi_c_125_not_kc_17():
    from plantstruct.anchor_codes import AnchorInput, design_anchor_concrete_cone
    cr = design_anchor_concrete_cone(AnchorInput(fc_MPa=25.0, h_ef_mm=300.0), code="US")
    un = design_anchor_concrete_cone(AnchorInput(fc_MPa=25.0, h_ef_mm=300.0, cracked_concrete=False), code="US")
    # N_b = 10·sqrt(25)·300^1.5 = 259,81 kN (misma derivacion que bases_columna.Nb_kN); phi = 0,65
    assert cr.N_design_kN == pytest.approx(0.65 * 259.8076, rel=1e-4)
    assert un.N_design_kN / cr.N_design_kN == pytest.approx(1.25)


def test_hoop_is_a_tension_check_against_Sd():
    from plantstruct.tanks import ShellBucklingFullInput, ShellBucklingInput, check_shell_buckling, check_shell_buckling_full
    b = check_shell_buckling(ShellBucklingInput(20.0, 16.0, 15.0, 10.0))
    f = check_shell_buckling_full(ShellBucklingFullInput(20.0, 16.0, 15.0, 10.0))
    sigma = 9.81 * 15.0 * 20.0 / (2 * 0.010) / 1000.0   # 147.15 MPa
    assert b.sigma_hoop_demand_MPa == pytest.approx(sigma) and f.sigma_hoop_demand_MPa == pytest.approx(sigma)
    assert b.DCR_hoop == pytest.approx(sigma / 160.0) and f.DCR_hoop == pytest.approx(sigma / 160.0)
    assert b.is_safe and f.is_safe
    # S_d <= 0 no es «sobra margen»: DCR infinito y no seguro
    z = check_shell_buckling(ShellBucklingInput(20.0, 16.0, 15.0, 10.0, Sd_MPa=0.0))
    assert z.DCR_hoop == float("inf") and not z.is_safe


def test_silos_en1991_4_matches_ec1_silos_janssen():
    from math import atan, degrees
    from plantstruct.ec1_silos import janssen_pressure
    from plantstruct.silos_en1991_4 import SiloInput, janssen_pressures
    r = janssen_pressures(SiloInput(6.0, 18.0, 9.0, degrees(atan(0.38)), 0.54))
    p_h, p_v = janssen_pressure(18.0, 9.0, 0.38, 0.54, 6.0)
    assert r.p_horizontal_max_kPa == pytest.approx(p_h, rel=1e-9)
    assert r.p_vertical_max_kPa == pytest.approx(p_v, rel=1e-9)
    assert r.p_wall_friction_max_kPa == pytest.approx(0.38 * p_h, rel=1e-9)
    z_o = 6.0 / (4 * 0.54 * 0.38)
    assert p_h == pytest.approx(9.0 * 0.54 * z_o * (1 - 2.718281828459045 ** (-18.0 / z_o)), rel=1e-6)
