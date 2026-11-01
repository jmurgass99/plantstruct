"""Tests para mejoras de plantstruct: API 650 §E.6.2.2.3 Fc, §E.6.2.1.1.2 L, ACI 318-19 §17.6.1.2 / §17.7 y k_yy exacto EC3."""
from __future__ import annotations

import pytest

from plantstruct.bases_columna import (
    BaseColumnaInput,
    check_anchor_shear_aci318_17_7,
    disenar_base,
)
from plantstruct.portal_frame import check_steel_member_interaction
from plantstruct.tanks.anchorage import self_anchored_uplift_length_api650
from plantstruct.tanks.shell_buckling import (
    ShellBucklingFullInput,
    api650_allowable_shell_buckling_stress_fc,
    check_shell_buckling_full,
)


def test_api650_e6223_allowable_shell_buckling_stress_fc():
    # g_hd = 1.0 * 12 * 20^2 / 8^2 = 75 >= 44 -> Fc = 83 * 8 / 20 = 33.2 MPa <= 0.5*250
    fc_slender = api650_allowable_shell_buckling_stress_fc(D_m=20.0, t_mm=8.0, H_liquid_m=12.0, Fy_MPa=250.0)
    assert fc_slender == pytest.approx(83.0 * 8.0 / 20.0, rel=1e-9)

    # g_hd = 1.0 * 10 * 10^2 / 16^2 = 3.90625 < 44 -> Fc = 83*16/(2.5*10) + 7.5*sqrt(10) = 53.12 + 23.717 = 76.837 MPa
    fc_stocky = api650_allowable_shell_buckling_stress_fc(D_m=10.0, t_mm=16.0, H_liquid_m=10.0, Fy_MPa=250.0)
    assert fc_stocky == pytest.approx(83.0 * 16.0 / 25.0 + 7.5 * (10.0 ** 0.5), rel=1e-9)

    full = check_shell_buckling_full(ShellBucklingFullInput(D_m=20.0, H_shell_m=14.0, H_liquid_m=12.0, t_shell_mm=8.0, Fy_MPa=250.0))
    assert full.Fc_api650_e6223_MPa == pytest.approx(fc_slender, rel=1e-6)


def test_api650_e62112_self_anchored_uplift_length():
    res = self_anchored_uplift_length_api650(t_a_mm=10.0, Fy_MPa=250.0, H_m=12.0, G_e=1.0, D_m=30.0)
    expected_L = 0.01723 * 10.0 * (250.0 / 12.0) ** 0.5
    assert res["L_uplift_m"] == pytest.approx(expected_L, rel=1e-9)
    assert res["within_0035D_limit"] is True


def test_bases_columna_aci318_17_6_1_2_and_17_7():
    # Con Ase_N_mm2 y futa_MPa explícitos usa N_sa = n_t * A_se,N * min(f_uta, 1.9*f_yb, 860)
    inp = BaseColumnaInput(
        P_kN=500.0,
        M_kNm=140.0,
        d_mm=300.0,
        bf_mm=250.0,
        n_anchors=4,
        db_anchor_mm=25.0,
        fyb_MPa=350.0,
        futa_MPa=500.0,
        Ase_N_mm2=353.0,
        hef_mm=300.0,
        ca1_mm=400.0,
        ca2_mm=400.0,
        s_anchor_mm=200.0,
        Abrg_mm2=900.0,
    )
    res = disenar_base(inp)
    # n_t = 2 -> N_sa = 2 * 353 * 500 / 1000 = 353.0 kN
    assert res.anchor_tension.steel_capacity_kN == pytest.approx(353.0, rel=1e-9)

    sh = check_anchor_shear_aci318_17_7(
        Vu_kN=60.0,
        n_anchors=4,
        db_anchor_mm=25.0,
        futa_MPa=500.0,
        fc_MPa=25.0,
        hef_mm=300.0,
        ca1_mm=350.0,
        Tu_kN=50.0,
        phi_Nn_kN=200.0,
    )
    assert sh["Vsa_design_kN"] > 0
    assert sh["Vcb_design_kN"] > 0
    assert sh["Vcp_design_kN"] > 0
    assert sh["interaction_ratio_17_8"] < 1.0
    assert sh["is_ok"] is True


def test_portal_frame_exact_kyy_with_lambda_y():
    kw = dict(N_Ed_kN=500.0, My_Ed_kNm=100.0, A_mm2=8446.0, Wel_y_mm3=1156000.0, fyi_MPa=275.0, chi_y=0.85, chi_LT=0.90)
    r_exact = check_steel_member_interaction(**kw, lambda_y=1.1, C_my=0.95)
    n_y = r_exact["axial_utilization"]
    # lambda_y = 1.1 >= 1.0 -> min(1.1 - 0.2, 0.8) = 0.8
    assert r_exact["interaction_coefficient_ky"] == pytest.approx(0.95 * (1.0 + 0.8 * n_y), rel=1e-9)
