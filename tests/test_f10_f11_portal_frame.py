"""Tests para F.10 y F.11 en PlantStruct (portal_frame.py).

F.10: check_steel_member_interaction exige chi_y y chi_LT obligatorios (sin defaults 0.85/0.90).
F.11: calculate_wind_pressure rechaza categorías de terreno no normativas.
"""
import pytest
from plantstruct.portal_frame import check_steel_member_interaction, calculate_wind_pressure


def test_check_steel_member_interaction_rejects_missing_chi_factors():
    """F.10: No se deben asumir factores chi_y=0.85 o chi_LT=0.90 en silencio."""
    kw = dict(
        N_Ed_kN=100.0,
        My_Ed_kNm=50.0,
        A_mm2=5000.0,
        Wel_y_mm3=500_000.0,
        fyi_MPa=275.0,
    )
    # Sin chi_y
    with pytest.raises(ValueError, match="chi_y debe proporcionarse"):
        check_steel_member_interaction(chi_y=None, chi_LT=0.90, **kw)

    # Sin chi_LT
    with pytest.raises(ValueError, match="chi_LT debe proporcionarse"):
        check_steel_member_interaction(chi_y=0.85, chi_LT=None, **kw)


def test_calculate_wind_pressure_terrain_categories():
    """F.11: Acepta categorías válidas 0..4 (y números romanos) y rechaza desconocidas."""
    # Válidas
    qp_2_int = calculate_wind_pressure(26.0, 10.0, terrain_category=2)
    qp_2_roman = calculate_wind_pressure(26.0, 10.0, terrain_category="II")
    assert qp_2_int == pytest.approx(qp_2_roman)
    assert qp_2_int > 0.0

    # Categorías extremas válidas
    qp_0 = calculate_wind_pressure(26.0, 10.0, terrain_category=0)
    qp_4 = calculate_wind_pressure(26.0, 10.0, terrain_category=4)
    assert qp_0 > qp_2_int > qp_4

    # Rechazo de categorías fuera de norma
    for bad_cat in (5, -1, 10, "V", "URBANO", "X"):
        with pytest.raises(ValueError, match="terrain_category.*no válida"):
            calculate_wind_pressure(26.0, 10.0, terrain_category=bad_cat)
