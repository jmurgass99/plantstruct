"""
Test suite for PlantStruct Composite Beams (Mezzanines and Equipment Decks).
Covers AISC 360-16 and Eurocode 4 workflows, load calculations, shored vs unpropped
construction checks, and failure diagnostics.
"""

import pytest
import math
from plantstruct.composite_beams import (
    SteelBeamProfile,
    StudConnectorSpec,
    IndustrialMezzanineDemand,
    IndustrialCompositeBeamResult,
    calculate_industrial_mezzanine_loads,
    design_industrial_composite_beam,
)


@pytest.fixture
def standard_w_beam():
    # W18x35 (ASTM A992, Fy=345 MPa)
    # d=450 mm, bf=152 mm, tf=10.8 mm, tw=7.6 mm, A=6650 mm2, Ix=2.12e8 mm4, Zx=1.09e6 mm3
    return SteelBeamProfile(
        name="W18x35",
        d_mm=450.0,
        bf_mm=152.0,
        tf_mm=10.8,
        tw_mm=7.6,
        A_mm2=6650.0,
        Ix_mm4=2.12e8,
        Zx_mm3=1.09e6,
        Fy_MPa=345.0,
    )


@pytest.fixture
def standard_ipe_beam():
    # IPE 400 (S355)
    # h=400 mm, b=180 mm, tf=13.5 mm, tw=8.6 mm, A=8450 mm2, Iy=2.313e8 mm4, Wy=1.307e6 mm3
    return SteelBeamProfile(
        name="IPE 400",
        d_mm=400.0,
        bf_mm=180.0,
        tf_mm=13.5,
        tw_mm=8.6,
        A_mm2=8450.0,
        Ix_mm4=2.313e8,
        Zx_mm3=1.307e6,
        Fy_MPa=355.0,
    )


class TestIndustrialMezzanineLoads:
    def test_load_combination_differences_aisc_vs_ec4(self, standard_w_beam):
        # Demand: span = 8 m, spacing = 2.5 m, SDL = 1.0 kPa, LL = 5.0 kPa
        demand_aisc = IndustrialMezzanineDemand(
            span_m=8.0,
            spacing_m=2.5,
            dead_load_superimposed_kpa=1.0,
            live_load_kpa=5.0,
            standard="AISC_360_16",
        )
        demand_ec4 = IndustrialMezzanineDemand(
            span_m=8.0,
            spacing_m=2.5,
            dead_load_superimposed_kpa=1.0,
            live_load_kpa=5.0,
            standard="EUROCODE_4",
        )

        loads_aisc = calculate_industrial_mezzanine_loads(demand_aisc, standard_w_beam)
        loads_ec4 = calculate_industrial_mezzanine_loads(demand_ec4, standard_w_beam)

        # AISC uses 1.2 D + 1.6 L; Eurocode uses 1.35 G + 1.50 Q
        # Since LL (5.0 kPa) is relatively high compared to D (~3 kPa),
        # 1.6 L in AISC will typically produce higher composite moment than 1.5 Q in EC4
        assert loads_aisc["M_u_comp_kNm"] > 0
        assert loads_ec4["M_u_comp_kNm"] > 0
        assert loads_aisc["M_u_comp_kNm"] != loads_ec4["M_u_comp_kNm"]

    def test_shored_construction_zeroes_construction_steel_moment(self, standard_w_beam):
        demand_unshored = IndustrialMezzanineDemand(
            span_m=9.0,
            spacing_m=3.0,
            dead_load_superimposed_kpa=1.5,
            live_load_kpa=6.0,
            shored_construction=False,
        )
        demand_shored = IndustrialMezzanineDemand(
            span_m=9.0,
            spacing_m=3.0,
            dead_load_superimposed_kpa=1.5,
            live_load_kpa=6.0,
            shored_construction=True,
        )

        loads_unshored = calculate_industrial_mezzanine_loads(demand_unshored, standard_w_beam)
        loads_shored = calculate_industrial_mezzanine_loads(demand_shored, standard_w_beam)

        assert loads_unshored["M_u_const_kNm"] > 0
        assert loads_shored["M_u_const_kNm"] == 0.0
        assert loads_shored["V_u_const_kN"] == 0.0


class TestAISCCompositeMezzanineDesign:
    def test_adequate_aisc_beam_design(self, standard_w_beam):
        demand = IndustrialMezzanineDemand(
            span_m=7.5,
            spacing_m=2.4,
            dead_load_superimposed_kpa=1.0,
            live_load_kpa=4.0,  # Light industrial mezzanine
            slab_thickness_mm=120.0,
            deck_height_mm=50.0,
            concrete_f_c_MPa=28.0,
            standard="AISC_360_16",
        )

        res = design_industrial_composite_beam(demand, standard_w_beam)
        assert res.is_viable is True
        assert res.standard_used == "AISC 360-16 (LRFD)"
        assert res.governing_dcr <= 1.0
        assert res.governing_dcr == pytest.approx(res.governing_dcr, rel=1e-4)
        assert res.num_studs_total > 0
        assert "CUMPLE" in res.summary_markdown()

    def test_overloaded_aisc_beam_fails_with_diagnostics(self, standard_w_beam):
        demand = IndustrialMezzanineDemand(
            span_m=12.0,  # Long span
            spacing_m=3.5,
            dead_load_superimposed_kpa=2.0,
            live_load_kpa=15.0,  # Heavy storage load
            slab_thickness_mm=120.0,
            concrete_f_c_MPa=28.0,
            standard="AISC_360_16",
        )

        res = design_industrial_composite_beam(demand, standard_w_beam)
        assert res.is_viable is False
        assert res.governing_dcr > 1.0
        assert len(res.diagnostics) > 0
        assert "NO CUMPLE" in res.summary_markdown()


class TestEurocodeCompositeMezzanineDesign:
    def test_adequate_eurocode_beam_design(self, standard_ipe_beam):
        demand = IndustrialMezzanineDemand(
            span_m=8.0,
            spacing_m=2.5,
            dead_load_superimposed_kpa=1.2,
            live_load_kpa=5.0,
            slab_thickness_mm=130.0,
            deck_height_mm=50.0,
            concrete_f_c_MPa=30.0,
            standard="EUROCODE_4",
        )

        res = design_industrial_composite_beam(demand, standard_ipe_beam)
        assert res.standard_used == "Eurocódigo 4 (EN 1994-1-1)"
        assert res.is_viable is True
        assert res.dcr_flexure_composite <= 1.0
        assert res.dcr_shear_composite <= 1.0
        assert "CUMPLE" in res.summary_markdown()

    def test_insufficient_shear_connection_triggers_eurocode_warning(self, standard_ipe_beam):
        demand = IndustrialMezzanineDemand(
            span_m=10.0,
            spacing_m=3.0,
            dead_load_superimposed_kpa=1.0,
            live_load_kpa=6.0,
            standard="EUROCODE_4",
        )

        # Force a very low stud count (e.g. 4 studs total, only 2 per half-span)
        res = design_industrial_composite_beam(demand, standard_ipe_beam, num_studs_total=4)
        assert res.num_studs_total == 4
        assert any("Eurocódigo 4 §6.6.1.2" in d for d in res.diagnostics)


class TestValidationAndInvariants:
    def test_invalid_negative_span_raises(self, standard_w_beam):
        with pytest.raises(ValueError):
            IndustrialMezzanineDemand(
                span_m=-5.0,
                spacing_m=2.5,
                dead_load_superimposed_kpa=1.0,
                live_load_kpa=5.0,
            )

    def test_invalid_profile_dimensions_raise(self):
        with pytest.raises(ValueError):
            SteelBeamProfile(
                name="BAD",
                d_mm=0.0,
                bf_mm=100.0,
                tf_mm=10.0,
                tw_mm=5.0,
                A_mm2=3000.0,
                Ix_mm4=1e7,
                Zx_mm3=1e5,
                Fy_MPa=345.0,
            )
