"""ACI 318-19 §17.7.3: V_cpg = k_cp·N_cbg del grupo, no n·N_b."""
import math

import pytest

from plantstruct.bases_columna import ANco_mm2, Nb_kN, check_anchor_shear_aci318_17_7, psi_ed_N

KW = dict(Vu_kN=80.0, n_anchors=4, db_anchor_mm=24.0, futa_MPa=620.0, fc_MPa=30.0, hef_mm=450.0,
          ca1_mm=200.0, ca2_mm=250.0)


def test_pryout_uses_group_cone_by_hand():
    r = check_anchor_shear_aci318_17_7(**KW, s_anchor_mm=200.0)
    lim = 1.5 * 450.0
    anc = (200.0 + 200.0 + lim) * (250.0 + 200.0 + 250.0)          # malla 2 × 2, s = 200 mm
    ncbg = anc / ANco_mm2(450.0) * psi_ed_N(200.0, 450.0) * Nb_kN(30.0, 450.0)
    assert r["Ncpg_kN"] == pytest.approx(ncbg, rel=1e-12)
    assert r["Vcp_kN"] == pytest.approx(2.0 * ncbg, rel=1e-12)
    # antes: 4·N_b·2 = 4183 kN nominales; ahora del orden del cono real
    assert r["Vcp_kN"] < 0.1 * 4 * 2 * Nb_kN(30.0, 450.0)


def test_pryout_without_spacing_is_single_cone_lower_bound():
    r0 = check_anchor_shear_aci318_17_7(**KW)
    rs = check_anchor_shear_aci318_17_7(**KW, s_anchor_mm=200.0)
    assert r0["Ncpg_kN"] < rs["Ncpg_kN"]


def test_futa_capped_by_1_9_fya():
    r = check_anchor_shear_aci318_17_7(**{**KW, "futa_MPa": 800.0}, fya_MPa=250.0, Ase_V_mm2=353.0)
    assert r["Vsa_kN"] == pytest.approx(4 * 0.6 * 353.0 * 1.9 * 250.0 / 1000.0)
