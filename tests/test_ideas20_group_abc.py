"""Tests para IDEAS_20 grupos A/B/C en IndustrialJm."""
import pytest


def test_bases_columna_simple():
    from industrialjm.bases_columna import BaseColumnaInput, disenar_base
    res = disenar_base(BaseColumnaInput(P_kN=500, M_kNm=0, code="US"))
    assert res.t_mm > 0
    assert res.N_mm >= 200


def test_bases_columna_codigo_invalido():
    from industrialjm.bases_columna import BaseColumnaInput, disenar_base
    with pytest.raises(ValueError):
        disenar_base(BaseColumnaInput(P_kN=500, code="ZZ"))


def test_bases_columna_excentrico():
    from industrialjm.bases_columna import BaseColumnaInput, disenar_base
    res = disenar_base(BaseColumnaInput(P_kN=500, M_kNm=300, code="EU"))
    assert res.Tu_anchor_kN > 0


def test_pipe_rack():
    from industrialjm.pipe_rack import PipeRackInput, evaluar_pipe_rack
    res = evaluar_pipe_rack(PipeRackInput(n_niveles=3, L_tramo_m=8, B_rack_m=6, code="US"))
    assert res.W_total_kN > 0
    assert res.cortante_basal_kN > 0


def test_pipe_rack_multi_code():
    from industrialjm.pipe_rack import PipeRackInput, evaluar_pipe_rack
    res_eu = evaluar_pipe_rack(PipeRackInput(n_niveles=2, L_tramo_m=8, B_rack_m=6, code="EU"))
    res_us = evaluar_pipe_rack(PipeRackInput(n_niveles=2, L_tramo_m=8, B_rack_m=6, code="US"))
    assert res_us.cortante_basal_kN > res_eu.cortante_basal_kN


def test_esfera_glp():
    from industrialjm.esferas_gpl import EsferaGLPInput, disenar_esfera
    res = disenar_esfera(EsferaGLPInput(D_m=20, P_design_bar=16, code="US"))
    assert res.t_min_mm > 0
    assert res.W_total_kN > 0
    assert res.P_col_kN > 0


def test_asce_15_7():
    from industrialjm.asce7_15_7 import TankASCEInput, asce_15_7
    res = asce_15_7(TankASCEInput(D_m=20, H_l_m=15, code="US"))
    assert res.Wi_kN > 0
    assert res.Wc_kN > 0
    assert res.V_total_kN > 0


def test_asce_15_7_codigo_invalido():
    from industrialjm.asce7_15_7 import TankASCEInput, asce_15_7
    with pytest.raises(ValueError):
        asce_15_7(TankASCEInput(D_m=20, H_l_m=15, code="EU"))


def test_report_api650():
    from industrialjm.report_api650 import API650ReportInput, generar_reporte_api650
    md = generar_reporte_api650(API650ReportInput(
        D_m=20, H_shell_m=12, H_l_m=10, t_shell_mm=8,
        Sa_i_g=0.5, Sa_c_g=0.15, n_bolts=32, bolt_diameter_mm=25,
    ))
    assert "Annex E" in md
    assert "Anclaje" in md


def test_fastsap_tank_parametric_dry_run():
    from industrialjm.integration.fastsap_tank_parametric import (
        TankParametric, FastSAPTankBuilder,
    )
    t = TankParametric(D_m=10, H_m=8, n_circ=8, n_vert=4)
    b = FastSAPTankBuilder(dry_run=True)
    r = b.build(t)
    assert r["dry_run"] is True
    assert len(r["joints"]) == 8 * 5  # n_circ * (n_vert+1)
    assert len(r["shells"]) == 8 * 4


def test_fastsap_tank_parametric_mock():
    from unittest.mock import MagicMock
    from industrialjm.integration.fastsap_tank_parametric import (
        TankParametric, FastSAPTankBuilder,
    )
    mock = MagicMock()
    b = FastSAPTankBuilder(client=mock, dry_run=False)
    r = b.build(TankParametric(D_m=5, H_m=4, n_circ=4, n_vert=2))
    assert r["dry_run"] is False
