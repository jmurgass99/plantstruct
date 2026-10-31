"""Tests para API 650 §E (masas Housner + pandeo manto)."""
import pytest

from plantstruct.tanks import (
    TankGeometry,
    housner_masses,
    shell_axial_buckling_stress,
)


def test_W_l_kN_calculo():
    g = TankGeometry(D_m=20, H_l_m=15, rho_l_kg_m3=1000)
    # V = π·100·15 ≈ 4712.4 m³, W = ρ·V·g/1000 = 46217 kN
    assert g.W_l_kN == pytest.approx(46217.0, rel=1e-3)


def test_housner_suma_masas_consistente():
    g = TankGeometry(D_m=20, H_l_m=15)
    r = housner_masses(g, Sa_i=0.3, Sa_c=0.10)
    # W_i + W_c ≤ W_l (no necesariamente suma exacta — diferencia es masa
    # "rígida" del fondo)
    assert r.W_i_kN > 0
    assert r.W_c_kN > 0
    assert r.W_i_kN + r.W_c_kN <= g.W_l_kN * 1.1


def test_periodo_convectivo_es_fisico():
    g = TankGeometry(D_m=20, H_l_m=15)
    r = housner_masses(g, Sa_i=0.3, Sa_c=0.10)
    # Para tanques medianos, T_c suele estar entre 3 y 8 s
    assert 2.0 < r.T_c_s < 10.0


def test_momento_volcante_no_negativo():
    g = TankGeometry(D_m=20, H_l_m=15)
    r = housner_masses(g, Sa_i=0.3, Sa_c=0.10)
    assert r.M_overturn_kNm > 0


def test_pandeo_manto_inversamente_proporcional_R():
    sigma_grande = shell_axial_buckling_stress(
        TankGeometry(D_m=10, H_l_m=10, t_shell_mm=6)
    )
    sigma_gigante = shell_axial_buckling_stress(
        TankGeometry(D_m=30, H_l_m=10, t_shell_mm=6)
    )
    # σ_cr ∝ 1/R → estanque grande tiene σ_cr menor
    assert sigma_grande > sigma_gigante


def test_validacion_geometria():
    with pytest.raises(ValueError):
        TankGeometry(D_m=-1, H_l_m=1).validate()


@pytest.mark.parametrize(
    "D_m, H_l_m",
    [(30, 5), (40, 8), (25, 6), (20, 15), (15, 15), (12, 18), (10, 20)],
)
def test_housner_invariantes_fisicos_en_rango(D_m, H_l_m):
    """Invariantes físicos que deben cumplirse en TODO el rango de esbeltez
    (H/D ≈ 0.17 → 2.0), no solo en el caso único D=20/H=15 de los otros tests."""
    g = TankGeometry(D_m=D_m, H_l_m=H_l_m)
    W_l = g.W_l_kN
    r = housner_masses(g, Sa_i=0.3, Sa_c=0.10)

    # Masas no negativas; la impulsiva no puede exceder el peso total del líquido
    assert r.W_i_kN >= 0.0
    assert r.W_c_kN >= 0.0
    assert r.W_i_kN <= W_l + 1e-6
    assert r.W_i_kN + r.W_c_kN <= W_l * 1.1

    # Brazos en rango físico (h_i exacto; h_c acotado por construcción)
    assert r.h_i_m == pytest.approx(0.375 * H_l_m)
    assert 0.4 * H_l_m <= r.h_c_m <= 0.7 * H_l_m

    # Periodos no negativos y momento volcante no negativo
    assert r.T_i_s > 0.0
    assert r.T_c_s >= 0.0
    assert r.M_overturn_kNm >= 0.0
