# -*- coding: utf-8 -*-
"""Tests para el dimensionado de bunkers y tolvas consolidado en PlantStruct."""
import math
from plantstruct.bunker import design_bunker
from plantstruct.bunker_schemas import BunkerIn


def test_bunker_design_in_plantstruct():
    inp = BunkerIn(
        impulse=2000.0,
        m=200.0,
        k=1.0e7,
        Rm=1.0e5,
        mu_allowable=10.0,
        span=4.0,
    )
    res = design_bunker(inp)
    assert math.isclose(res.x_el, 0.01, rel_tol=1e-12)
    assert math.isclose(res.mu, 11.0, rel_tol=1e-12)
    assert math.isclose(res.x_max, 0.11, rel_tol=1e-12)
    assert res.passed is False
