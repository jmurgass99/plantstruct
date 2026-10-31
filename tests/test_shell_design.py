# -*- coding: utf-8 -*-
"""Espesor de virola API 650 — Metodo del Pie (§5.6.3.2)."""
import pytest

from plantstruct.tanks.shell_design import shell_thickness_one_foot


class TestOneFoot:
    def test_formula_diseno(self):
        # t_d = 4.9·D·(H-0.3)·G/Sd + CA
        r = shell_thickness_one_foot(D_m=12.0, H_m=12.0, G=1.0, Sd_MPa=160.0, St_MPa=171.0, CA_mm=0.0)
        esperado = 4.9 * 12.0 * (12.0 - 0.3) * 1.0 / 160.0
        assert r.t_design_mm == pytest.approx(esperado, rel=1e-9)

    def test_minimo_nominal_gobierna_tanque_pequeno(self):
        # Tanque pequeno: el espesor calculado es bajo -> gobierna minimo nominal (5 mm para D<15).
        r = shell_thickness_one_foot(D_m=10.0, H_m=6.0, G=1.0)
        assert r.t_min_nominal_mm == 5.0
        assert r.t_required_mm == pytest.approx(5.0)
        assert r.governing == "minimo_nominal"

    def test_corrosion_aumenta_diseno(self):
        sin = shell_thickness_one_foot(20.0, 14.0, 1.0, CA_mm=0.0).t_design_mm
        con = shell_thickness_one_foot(20.0, 14.0, 1.0, CA_mm=3.0).t_design_mm
        assert con == pytest.approx(sin + 3.0)

    def test_gravedad_mayor_mas_espesor(self):
        agua = shell_thickness_one_foot(30.0, 18.0, G=1.0).t_design_mm
        acido = shell_thickness_one_foot(30.0, 18.0, G=1.5).t_design_mm
        assert acido > agua

    def test_minimo_nominal_por_diametro(self):
        assert shell_thickness_one_foot(40.0, 5.0).t_min_nominal_mm == 8.0  # 36<=D<60

    def test_diametro_excesivo_lanza(self):
        with pytest.raises(ValueError):
            shell_thickness_one_foot(70.0, 18.0)
