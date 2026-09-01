"""Tests de regresion para el levantamiento (traccion neta) en ``bases_columna``.

D5 - ``P_comp = max(inp.P_kN, 1.0)`` convertia una traccion neta de -400 kN en
     +1 kN de compresion ficticia: la placa se dimensionaba por aplastamiento
     inexistente, la friccion salia 0.2 kN y el resultado devolvia cumple=True.

D7 - la llave de cortante lleva ``lug_h=75`` y ``lug_t=25`` hardcodeados: son una
     ENTRADA FIJA, no un dimensionamiento. El resultado debe decirlo.

Los valores aseverados salen de forma cerrada (friccion = mu * compresion, y con
traccion neta la compresion sobre el hormigon es nula) o son ausencias exigidas
por la regla del repositorio. No hay valores capturados de la implementacion.
"""
from __future__ import annotations

import pytest

from industrialjm.bases_columna import BaseColumnaInput, disenar_base


def _uplift_input(**kw) -> BaseColumnaInput:
    base = dict(
        P_kN=-400.0,      # traccion neta
        V_kN=50.0,
        M_kNm=0.0,
        bf_mm=200.0,
        d_mm=250.0,
        mu_friction=0.40,
        code="US",
    )
    base.update(kw)
    return BaseColumnaInput(**base)


def test_d5_traccion_neta_no_puede_devolver_cumple_true():
    """DEFECTO: con P = -400 kN el modulo devolvia cumple=True.

    No hay compresion sobre el hormigon, luego no hay area de aplastamiento que
    dimensione la placa ni fuerza normal que genere friccion. El modulo no
    dimensiona anclajes a levantamiento, asi que el unico resultado honesto es
    NO VERIFICADO y cumple != True.
    """
    res = disenar_base(_uplift_input())
    assert res.cumple is not True
    assert res.verification_status == "NO_VERIFICADO"


def test_d5_no_finge_compresion_para_la_friccion():
    """Friccion = mu * N_compresion. Con traccion neta N_compresion = 0 -> 0 kN.

    El defecto daba 0.40 * 1.0 = 0.4 kN (mu * el pseudo-P de 1 kN).
    """
    res = disenar_base(_uplift_input(mu_friction=0.40, V_kN=50.0))
    assert res.shear_lug.shear_friction_capacity_kN == 0.0
    assert res.shear_lug.required is True


def test_d5_no_inventa_geometria_ni_traccion_de_anclaje():
    """Ausencia propagada como ausencia: sin espesor, sin excentricidad, sin Tu."""
    res = disenar_base(_uplift_input())
    assert res.t_mm is None
    assert res.e_mm is None
    assert res.Tu_anchor_kN is None


def test_d5_to_dict_declara_no_verificado():
    """El lector de ``to_dict`` (API/informe) debe ver el estado, no solo cumple."""
    d = disenar_base(_uplift_input()).to_dict()
    assert d["cumple"] is not True
    assert d["verification_status"] == "NO_VERIFICADO"
    assert d["t_mm"] is None
    assert d["Tu_anchor_kN"] is None
    assert any("levantamiento" in n.lower() or "traccion" in n.lower()
               for n in d["notes"]), d["notes"]


def test_d5_p_cero_tambien_es_ausencia_de_compresion():
    """P = 0 no aporta compresion: mismo tratamiento que la traccion neta."""
    res = disenar_base(_uplift_input(P_kN=0.0))
    assert res.cumple is not True
    assert res.verification_status == "NO_VERIFICADO"


def test_d5_compresion_sigue_verificandose_normalmente():
    """La rama de compresion no cambia de estado: sigue produciendo un veredicto."""
    res = disenar_base(BaseColumnaInput(P_kN=600.0, V_kN=180.0, M_kNm=85.0,
                                        d_mm=300.0, mu_friction=0.20, code="US"))
    assert res.verification_status == "VERIFICADO"
    assert res.t_mm is not None and res.t_mm > 0.0
    assert res.shear_lug.shear_friction_capacity_kN == pytest.approx(120.0)


def test_d7_las_dimensiones_de_la_llave_se_declaran_como_entrada_fija():
    """La llave de cortante NO se dimensiona: h y t son constantes del modulo.

    No se arregla (dimensionar una llave es una decision de diseno), pero el
    resultado debe impedir que se lea como un dimensionamiento.
    """
    res = disenar_base(BaseColumnaInput(P_kN=600.0, V_kN=180.0, M_kNm=85.0,
                                        d_mm=300.0, mu_friction=0.20, code="US"))
    assert res.shear_lug.required is True
    assert "ENTRADA FIJA" in res.shear_lug.dims_source
    d = disenar_base(BaseColumnaInput(P_kN=600.0, V_kN=180.0, M_kNm=85.0,
                                      d_mm=300.0, mu_friction=0.20, code="US")).to_dict()
    assert "ENTRADA FIJA" in d["shear_lug"]["dims_source"]
