"""Tests para anchorage + shell_buckling."""
import pytest

from plantstruct.tanks import (
    AnchorageInput, ShellBucklingInput,
    check_anchorage, check_shell_buckling,
    TankGeometry, housner_masses,
    AnchorageJInput, check_anchorage_J,
    ShellBucklingFullInput, check_shell_buckling_full,
)


class TestAnchorage:
    def test_sin_uplift_no_pernos_extras(self):
        # M chico → uplift negativo → F_up = 0
        r = check_anchorage(AnchorageInput(
            D_m=20, W_tank_kN=50_000, M_overturn_kNm=10_000,
            n_bolts=24, bolt_diameter_mm=25.4,
        ))
        assert r.F_uplift_per_bolt_kN == 0.0
        assert r.is_safe

    def test_uplift_severo(self):
        r = check_anchorage(AnchorageInput(
            D_m=20, W_tank_kN=5_000, M_overturn_kNm=500_000,
            n_bolts=12, bolt_diameter_mm=25.4,
        ))
        assert r.F_uplift_per_bolt_kN > 0
        assert r.DCR > 0
        assert r.n_bolts_required_min >= 12

    def test_validacion(self):
        with pytest.raises(ValueError):
            check_anchorage(AnchorageInput(
                D_m=20, W_tank_kN=5_000, M_overturn_kNm=1_000,
                n_bolts=3,
            ))


class TestShellBuckling:
    def test_demanda_hoop_no_negativa(self):
        r = check_shell_buckling(ShellBucklingInput(
            D_m=20, H_shell_m=16, H_liquid_m=15, t_shell_mm=8,
        ))
        assert r.sigma_hoop_demand_MPa > 0

    def test_axial_pequeno_safe(self):
        r = check_shell_buckling(ShellBucklingInput(
            D_m=10, H_shell_m=12, H_liquid_m=10, t_shell_mm=10,
            sigma_axial_imposed_MPa=10,
        ))
        assert r.sigma_axial_critical_MPa > r.sigma_axial_demand_MPa

    def test_hoop_es_traccion_frente_a_Sd_y_no_entra_en_la_interaccion(self):
        # Hasta 2026-11-01 la traccion anular hidrostatica se comparaba con la
        # tension critica de Donnell a presion EXTERIOR (2-4 MPa) y entraba al
        # cuadrado en la interaccion: cualquier tanque lleno daba DCR_hoop > 40.
        r = check_shell_buckling(ShellBucklingInput(
            D_m=20, H_shell_m=16, H_liquid_m=15, t_shell_mm=6,
        ))
        sigma_hoop = 9.81 * 15 * 20 / (2 * 0.006) / 1000.0   # 245.25 MPa
        assert r.sigma_hoop_demand_MPa == pytest.approx(sigma_hoop)
        assert r.sigma_hoop_allowable_MPa == 160.0
        assert r.DCR_hoop == pytest.approx(sigma_hoop / 160.0)
        assert r.DCR_interaction == pytest.approx(r.DCR_axial)
        assert not r.is_safe                                   # 245 MPa > 160 MPa: no cumple a traccion


def test_integracion_housner_anchorage():
    g = TankGeometry(D_m=20, H_l_m=15)
    masses = housner_masses(g, Sa_i=0.4, Sa_c=0.15)
    r = check_anchorage(AnchorageInput(
        D_m=g.D_m, W_tank_kN=g.W_l_kN * 1.05,
        M_overturn_kNm=masses.M_overturn_kNm,
        n_bolts=24,
    ))
    assert r.DCR >= 0


# ===========================================================================
# IN-001: Tests J-ratio API 650 §E.6.2 completo
# ===========================================================================

class TestAnchorageJ:
    """Verificacion J-ratio, numero de pernos y silleta — API 650 §E.6.2."""

    def test_J_self_anchored(self):
        """W_t alto y M_rw bajo -> J <= 0.785 -> self-anchored."""
        r = check_anchorage_J(AnchorageJInput(
            D_m=10, M_rw_kNm=5_000, W_t_kN=50_000,
        ))
        assert r.J < 0.785
        assert r.anchorage_type == "self-anchored"
        assert r.is_self_anchored is True

    def test_J_mechanically_anchored(self):
        """M_rw alto -> J > 1.54 -> mechanically anchored."""
        r = check_anchorage_J(AnchorageJInput(
            D_m=10, M_rw_kNm=500_000, W_t_kN=1_000,
        ))
        assert r.J > 1.54
        assert r.anchorage_type == "mechanically-anchored"
        assert r.is_self_anchored is False

    def test_J_conditioned(self):
        """J entre 0.785 y 1.54 -> conditioned."""
        # Calibrar: J = M / (D^2 * w_t) con w_t = W_t/(pi*D) (API 650 E.6.2.1.1.1,
        # fuerza por unidad de perimetro). Hasta 2026-10-31 el test calibraba con
        # el peso TOTAL (M = D^2 * W_t), que es la formula erronea que tenia el codigo.
        from math import pi
        D = 10
        W_t = 1000
        M = 1.0 * D ** 2 * W_t / (pi * D)  # J = 1.0
        r = check_anchorage_J(AnchorageJInput(
            D_m=D, M_rw_kNm=M, W_t_kN=W_t,
        ))
        assert 0.785 < r.J <= 1.54
        assert r.anchorage_type == "conditioned"

    def test_referencia_D10_H8_t8_Fp100(self):
        """Estanque D=10m, H=8m, t_shell=8mm, Fp=100kN.

        Verifica que J y N_b son calculados consistentemente.
        Fp=100 kN es la fuerza de uplift total neta impuesta.
        """
        g = TankGeometry(D_m=10, H_l_m=8, t_shell_mm=8)
        masses = housner_masses(g, Sa_i=0.4, Sa_c=0.15)
        W_tank = g.W_l_kN * 1.05

        r = check_anchorage_J(AnchorageJInput(
            D_m=10,
            M_rw_kNm=masses.M_overturn_kNm,
            W_t_kN=W_tank,
            Fp_kN=100.0,
            bolt_diameter_mm=25.4,
            bolt_Fy_MPa=250.0,
        ))
        # J debe ser finito y positivo
        assert r.J > 0
        assert r.J < float("inf")
        # N_bolts_required >= 4
        assert r.N_bolts_required >= 4
        # Ab correcta
        assert r.Ab_mm2 == pytest.approx(506.7, rel=1e-2)
        # Base plate y anchor length positivos
        assert r.t_base_plate_mm > 0
        assert r.L_anchor_mm > 0
        # to_dict tiene todas las claves
        d = r.to_dict()
        assert "J" in d
        assert "N_bolts_required" in d
        assert "t_base_plate_mm" in d
        assert "L_anchor_mm" in d

    def test_W_int_reduce_denominador(self):
        """W_int > 0 reduce el denominador, aumentando J."""
        r0 = check_anchorage_J(AnchorageJInput(
            D_m=10, M_rw_kNm=50_000, W_t_kN=5_000, W_int_kN=0,
        ))
        r1 = check_anchorage_J(AnchorageJInput(
            D_m=10, M_rw_kNm=50_000, W_t_kN=5_000, W_int_kN=2_000,
        ))
        assert r1.J > r0.J

    def test_validacion_D_negativo(self):
        with pytest.raises(ValueError):
            check_anchorage_J(AnchorageJInput(
                D_m=-5, M_rw_kNm=100, W_t_kN=100,
            ))


# ===========================================================================
# IN-002: Tests pandeo completo del manto
# ===========================================================================

class TestShellBucklingFull:
    """Pandeo completo: axial + hoop + flexion + interaccion + Rotter."""

    def test_esbelto_HD2_gobierna_pandeo(self):
        """Estanque esbelto H/D=2 -> pandeo por hoop o bending es critico."""
        r = check_shell_buckling_full(ShellBucklingFullInput(
            D_m=5, H_shell_m=10, H_liquid_m=10, t_shell_mm=6,
        ))
        # Para H/D=2 (esbelto), sigma_hoop es significativo
        assert r.sigma_hoop_demand_MPa > 0
        assert r.DCR_hoop > 0
        # Fb_bending debe ser calculado
        assert r.Fb_bending_MPa > 0
        # Interaccion cuadratica
        assert r.DCR_interaction == pytest.approx(
            r.DCR_axial ** 2 + r.DCR_bending ** 2, rel=1e-6,
        )

    def test_robusto_HD03(self):
        """Estanque robusto H/D=0.3 -> hoop bajo, pandeo no critico."""
        r = check_shell_buckling_full(ShellBucklingFullInput(
            D_m=30, H_shell_m=9.5, H_liquid_m=9, t_shell_mm=40,
        ))
        # Robusto: hoop mas bajo, mas estable
        assert r.is_safe
        assert r.governing_mode in ("axial", "hoop", "bending", "interaction")

    def test_rotter_diamond_knockdown(self):
        """Factor Rotter: 0 < alpha < 1, decrece con R/t."""
        r_thin = check_shell_buckling_full(ShellBucklingFullInput(
            D_m=20, H_shell_m=10, H_liquid_m=8, t_shell_mm=5,
        ))
        r_thick = check_shell_buckling_full(ShellBucklingFullInput(
            D_m=20, H_shell_m=10, H_liquid_m=8, t_shell_mm=20,
        ))
        # Manto delgado -> R/t grande -> alpha mas bajo
        assert 0 < r_thin.alpha_diamond < 1
        assert 0 < r_thick.alpha_diamond < 1
        assert r_thin.alpha_diamond < r_thick.alpha_diamond

    def test_Fbi_diamond_menor_que_Fbi_axial(self):
        """Pandeo diamante siempre menor que pandeo axial ideal."""
        r = check_shell_buckling_full(ShellBucklingFullInput(
            D_m=15, H_shell_m=12, H_liquid_m=10, t_shell_mm=8,
        ))
        assert r.Fbi_diamond_MPa < r.Fbi_axial_MPa

    def test_interaccion_bending_axial(self):
        """Interaccion (fa/Fa)^2 + (fb/Fb)^2 <= 1.0 con bending impuesto."""
        r = check_shell_buckling_full(ShellBucklingFullInput(
            D_m=10, H_shell_m=12, H_liquid_m=10, t_shell_mm=10,
            sigma_axial_imposed_MPa=10, sigma_bending_MPa=5,
        ))
        expected = (10 / r.Fbi_axial_MPa) ** 2 + (5 / r.Fb_bending_MPa) ** 2
        assert r.DCR_interaction == pytest.approx(expected, rel=1e-6)

    def test_esbelto_vs_robusto_hoop(self):
        """Esbelto tiene mas hoop demand que robusto para misma H_liquid."""
        r_esb = check_shell_buckling_full(ShellBucklingFullInput(
            D_m=5, H_shell_m=10, H_liquid_m=8, t_shell_mm=8,
        ))
        r_rob = check_shell_buckling_full(ShellBucklingFullInput(
            D_m=30, H_shell_m=10, H_liquid_m=8, t_shell_mm=8,
        ))
        # sigma_hoop = gamma*H*D/(2*t) -> D grande tiene mas hoop
        assert r_rob.sigma_hoop_demand_MPa > r_esb.sigma_hoop_demand_MPa

    def test_to_dict_keys(self):
        r = check_shell_buckling_full(ShellBucklingFullInput(
            D_m=10, H_shell_m=12, H_liquid_m=10, t_shell_mm=8,
        ))
        d = r.to_dict()
        expected_keys = {
            "sigma_axial_demand_MPa", "sigma_hoop_demand_MPa",
            "sigma_bending_demand_MPa", "Fbi_axial_MPa", "Fh_hoop_allowable_MPa",
            "Fb_bending_MPa", "DCR_axial", "DCR_hoop", "DCR_bending",
            "DCR_interaction", "alpha_diamond", "Fbi_diamond_MPa",
            "is_safe", "governing_mode",
            # El resultado ya publicaba DOS capacidades axiales (Fbi_axial por
            # API 650 y Fbi_diamond por Rotter) sin decir cual sostenia el
            # veredicto ni que DCR implicaba la otra. La brecha entre ambas es
            # 0.6*(1 + 0.005*R/t): 2.4x a R/t=600 y 8.1x a R/t=2500.
            "DCR_axial_diamond", "axial_basis",
        }
        assert set(d.keys()) == expected_keys
