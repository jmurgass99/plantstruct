"""Tests del modelo stick Housner para SAP (idea #11).

Conecta housner_masses (api650) con el modelo de masas para SAP: masa impulsiva
rígida + masa convectiva sobre resorte (k = m_c·ω_c²). Pura lógica, sin SAP.
"""
import math

from industrialjm.tanks.api650 import TankGeometry, housner_masses
from industrialjm.integration.fastsap_tank_parametric import build_housner_stick_model

G = 9.80665


def test_masas_son_W_sobre_g():
    geom = TankGeometry(D_m=20.0, H_l_m=12.0)
    sm = housner_masses(geom, Sa_i=0.5, Sa_c=0.15)
    model = build_housner_stick_model(geom, Sa_i=0.5, Sa_c=0.15)

    masses = {m["node"]: m["mass"] for m in model["masses"]}
    assert math.isclose(masses["IMP"], sm.W_i_kN / G, rel_tol=1e-9)
    assert math.isclose(masses["CONV"], sm.W_c_kN / G, rel_tol=1e-9)


def test_resorte_convectivo_k_igual_m_omega2():
    geom = TankGeometry(D_m=20.0, H_l_m=12.0)
    sm = housner_masses(geom, Sa_i=0.5, Sa_c=0.15)
    model = build_housner_stick_model(geom, Sa_i=0.5, Sa_c=0.15)

    m_c = sm.W_c_kN / G
    omega_c = 2 * math.pi / sm.T_c_s
    assert math.isclose(model["convective_spring"]["k_kN_m"], m_c * omega_c ** 2, rel_tol=1e-9)
    assert model["convective_spring"]["node"] == "CONV"


def test_nodos_base_empotrada_y_alturas():
    geom = TankGeometry(D_m=20.0, H_l_m=12.0)
    sm = housner_masses(geom, Sa_i=0.5, Sa_c=0.15)
    model = build_housner_stick_model(geom, Sa_i=0.5, Sa_c=0.15)

    nodes = {n["name"]: n for n in model["nodes"]}
    assert nodes["BASE"]["restraint"] == [True] * 6
    assert math.isclose(nodes["IMP"]["z"], sm.h_i_m, rel_tol=1e-9)
    assert math.isclose(nodes["CONV"]["z"], sm.h_c_m, rel_tol=1e-9)


def test_incluye_resumen_sismico():
    geom = TankGeometry(D_m=15.0, H_l_m=9.0)
    model = build_housner_stick_model(geom, Sa_i=0.4, Sa_c=0.1)
    assert "M_overturn_kNm" in model["seismic"] and model["seismic"]["W_i_kN"] > 0
