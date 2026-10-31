"""Tests chimneys + silos."""
import pytest

from plantstruct.chimneys import ChimneyInput, evaluate_chimney
from plantstruct.silos_en1991_4 import SiloInput, janssen_pressures


class TestChimney:
    def test_chimnea_caracteristica(self):
        r = evaluate_chimney(ChimneyInput(
            D_outer_m=3.0, H_m=60, t_shell_mm=10, Vb_m_per_s=30,
        ))
        assert r.f1_Hz > 0
        assert r.T1_s > 0
        assert r.aspect_ratio == 20.0

    def test_aspect_ratio(self):
        r = evaluate_chimney(ChimneyInput(
            D_outer_m=2.0, H_m=80, t_shell_mm=8, Vb_m_per_s=30,
        ))
        assert r.aspect_ratio == 40.0


class TestSilos:
    def test_presion_horizontal_creciente_con_z(self):
        r_corto = janssen_pressures(SiloInput(
            diameter_m=8, height_filled_m=5, bulk_density_kN_m3=8,
        ))
        r_alto = janssen_pressures(SiloInput(
            diameter_m=8, height_filled_m=30, bulk_density_kN_m3=8,
        ))
        assert r_alto.p_horizontal_max_kPa > r_corto.p_horizontal_max_kPa

    def test_satura_para_altura_grande(self):
        # Para z >> A, p_h → γ·D/(4μK) constante
        r = janssen_pressures(SiloInput(
            diameter_m=5, height_filled_m=200, bulk_density_kN_m3=8,
        ))
        assert r.p_horizontal_max_kPa > 0
