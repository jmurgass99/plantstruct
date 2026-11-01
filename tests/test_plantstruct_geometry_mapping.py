"""Tests para TankCourseMapping en PlantStruct."""
from plantstruct.geometry_mapping import SemanticShellCourse, build_tank_course_mesh


def test_tank_course_mapping_refinement():
    courses = [
        SemanticShellCourse("COURSE-1", height_m=2.4, thickness_mm=14.0),
        SemanticShellCourse("COURSE-2", height_m=2.4, thickness_mm=11.0),
        SemanticShellCourse("COURSE-3", height_m=2.4, thickness_mm=8.0),
        SemanticShellCourse("COURSE-4", height_m=2.4, thickness_mm=6.0),
    ]
    r_2, m_2, s_2 = build_tank_course_mesh(
        diameter_m=16.0, liquid_height_m=8.8, courses=courses, rings_per_course=2
    )
    r_6, m_6, s_6 = build_tank_course_mesh(
        diameter_m=16.0, liquid_height_m=8.8, courses=courses, rings_per_course=6
    )

    assert len(r_2) == 8
    assert len(r_6) == 24
    assert len(m_6.course_to_rings["COURSE-1"]) == 6
    assert abs(s_2["V_base_kN"] - s_6["V_base_kN"]) < 1e-6
    assert s_6["max_hoop_MPa"] > 30.0
