"""Separación Semántica -> Malla de Virolas/Anillos (TankCourseMapping) para PlantStruct.

Mapea virolas semánticas de un tanque cilíndrico API 650 (`course_to_rings`) y anillos
rigidizadores (`frame_to_elements`) a sub-anillos discretos para tensión circunferencial
hidrostática + hidrodinámica (Housner impulsivo/convectivo) y pandeo axial.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .tanks.api650 import TankGeometry, housner_masses


@dataclass(frozen=True)
class SemanticShellCourse:
    id: str
    height_m: float
    thickness_mm: float


@dataclass
class TankCourseMapping:
    """Mapeo Virola Semántica -> Anillos Discretos del Manto."""
    course_to_rings: Dict[str, List[int]] = field(default_factory=dict)
    ring_to_course: Dict[int, str] = field(default_factory=dict)
    frame_to_elements: Dict[str, List[int]] = field(default_factory=dict)


@dataclass
class TankShellRing:
    index: int
    course_id: str
    z_mid_m: float
    dz_m: float
    thickness_mm: float
    hoop_hydrostatic_MPa: float
    hoop_seismic_MPa: float
    hoop_total_MPa: float


def build_tank_course_mesh(
    diameter_m: float,
    liquid_height_m: float,
    courses: List[SemanticShellCourse],
    rings_per_course: int = 4,
    Sa_i: float = 0.28,
    Sa_c: float = 0.12,
) -> Tuple[List[TankShellRing], TankCourseMapping, Dict[str, float]]:
    """Subdivide cada virola en `rings_per_course` anillos y calcula tensiones API 650 Anexo E."""
    div = max(1, int(rings_per_course))
    t_avg = sum(c.thickness_mm * c.height_m for c in courses) / max(
        sum(c.height_m for c in courses), 1e-6
    )
    geom = TankGeometry(D_m=diameter_m, H_l_m=liquid_height_m, t_shell_mm=t_avg)
    seismic = housner_masses(geom, Sa_i=Sa_i, Sa_c=Sa_c)

    mapping = TankCourseMapping()
    rings: List[TankShellRing] = []
    radius_m = diameter_m / 2.0
    gamma_kN_m3 = 9.80665

    z_cursor = 0.0
    for course in courses:
        dz = course.height_m / div
        mapping.course_to_rings[course.id] = []
        for _ in range(div):
            idx = len(rings)
            z_mid = z_cursor + 0.5 * dz
            depth_w = max(0.0, liquid_height_m - z_mid)
            # Tensión circunferencial hidrostática: σ_h = (γ · depth · R) / t [MPa]
            sigma_hydro = (gamma_kN_m3 * depth_w * radius_m) / max(course.thickness_mm, 1.0)
            # Incremento sísmico circunferencial proporcional a la profundidad relativa
            sigma_seis = sigma_hydro * (0.65 * Sa_i + 0.25 * Sa_c)
            rings.append(
                TankShellRing(
                    index=idx,
                    course_id=course.id,
                    z_mid_m=z_mid,
                    dz_m=dz,
                    thickness_mm=course.thickness_mm,
                    hoop_hydrostatic_MPa=sigma_hydro,
                    hoop_seismic_MPa=sigma_seis,
                    hoop_total_MPa=sigma_hydro + sigma_seis,
                )
            )
            mapping.course_to_rings[course.id].append(idx)
            mapping.ring_to_course[idx] = course.id
            z_cursor += dz

    mapping.frame_to_elements["WIND-GIRDER-TOP"] = [len(rings) - 1] if rings else []

    summary = {
        "W_i_kN": seismic.W_i_kN,
        "W_c_kN": seismic.W_c_kN,
        "T_i_s": seismic.T_i_s,
        "T_c_s": seismic.T_c_s,
        "V_base_kN": seismic.V_base_kN,
        "M_overturn_kNm": seismic.M_overturn_kNm,
        "max_hoop_MPa": max((r.hoop_total_MPa for r in rings), default=0.0),
    }
    return rings, mapping, summary
