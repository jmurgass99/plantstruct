# -*- coding: utf-8 -*-
"""Espesor de virola de tanques de almacenamiento — API 650 §5.6 (Metodo del Pie).

El "1-Foot Method" (§5.6.3.2) es el calculo fundamental del espesor de cada anillo
de la virola, valido para D <= 60 m:

    t_d = 4.9·D·(H − 0.3)·G / S_d + CA      (condicion de diseno, mm)
    t_t = 4.9·D·(H − 0.3)     / S_t          (prueba hidrostatica, mm)

con D en m, H en m (altura del liquido sobre el anillo), G gravedad especifica,
S_d/S_t esfuerzos admisibles (MPa), CA sobreespesor por corrosion (mm). El espesor
requerido es el mayor de t_d, t_t y el minimo nominal por diametro (Tabla 5.6a).
"""
from __future__ import annotations

from dataclasses import dataclass


def _min_nominal_thickness(D_m: float) -> float:
    """Espesor nominal minimo de virola por diametro (API 650 Tabla 5.6a), mm."""
    if D_m < 15.0:
        return 5.0
    if D_m < 36.0:
        return 6.0
    if D_m < 60.0:
        return 8.0
    return 10.0


@dataclass(frozen=True)
class ShellCourseResult:
    t_design_mm: float
    t_test_mm: float
    t_min_nominal_mm: float
    t_required_mm: float
    governing: str


def shell_thickness_one_foot(
    D_m: float,
    H_m: float,
    G: float = 1.0,
    Sd_MPa: float = 160.0,
    St_MPa: float = 171.0,
    CA_mm: float = 0.0,
) -> ShellCourseResult:
    """Espesor requerido de un anillo de virola por el Metodo del Pie (API 650 §5.6.3.2).

    Args:
        D_m: diametro nominal del tanque.
        H_m: altura del liquido sobre el fondo del anillo considerado.
        G: gravedad especifica del liquido (>=1.0 tipico).
        Sd_MPa, St_MPa: esfuerzos admisibles de diseno y prueba (material).
        CA_mm: sobreespesor por corrosion.
    """
    if D_m <= 0 or H_m <= 0:
        raise ValueError("D y H deben ser > 0")
    if D_m > 60.0:
        raise ValueError("Metodo del Pie valido solo para D <= 60 m; usar Variable-Design-Point")

    t_d = 4.9 * D_m * (H_m - 0.3) * G / Sd_MPa + CA_mm
    t_t = 4.9 * D_m * (H_m - 0.3) / St_MPa
    t_min = _min_nominal_thickness(D_m)

    t_req = max(t_d, t_t, t_min)
    if t_req == t_min and t_min > max(t_d, t_t):
        gov = "minimo_nominal"
    elif t_d >= t_t:
        gov = "diseno"
    else:
        gov = "prueba_hidrostatica"
    return ShellCourseResult(
        t_design_mm=t_d, t_test_mm=t_t, t_min_nominal_mm=t_min,
        t_required_mm=t_req, governing=gov,
    )


__all__ = ["ShellCourseResult", "shell_thickness_one_foot"]
