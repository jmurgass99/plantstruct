"""Tests anchor codes multi-código."""
import pytest

from industrialjm.anchor_codes import AnchorInput, design_anchor_concrete_cone


@pytest.fixture
def base():
    return AnchorInput(fc_MPa=25, h_ef_mm=150, n_anchors=4)


def test_4_codes(base):
    for c in ("US", "CO", "EU", "SG", "AU"):
        r = design_anchor_concrete_cone(base, code=c)
        assert r.N_design_kN > 0
        assert r.governing_mode == "concrete_cone"


def test_uncracked_mayor_capacidad(base):
    cracked = design_anchor_concrete_cone(base, code="US")
    uncracked = design_anchor_concrete_cone(
        AnchorInput(**{**base.__dict__, "cracked_concrete": False}),
        code="US",
    )
    assert uncracked.N_design_kN > cracked.N_design_kN


def test_invalido(base):
    with pytest.raises(ValueError):
        design_anchor_concrete_cone(base, code="XX")
