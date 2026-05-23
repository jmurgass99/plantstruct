# -*- coding: utf-8 -*-
"""
EN 1993-1-1 — Steel Portal Frame Member Design under Wind Loads
==============================================================
Implementa las ecuaciones de capacidad de diseño a pandeo flexocompresión
y cálculo de presiones de viento en naves industriales bajo Eurocódigo 3,
según el documento Structural_Design_of_Single_Story_Buildi.pdf.
"""
from __future__ import annotations
import math

def calculate_wind_pressure(
    basic_wind_speed_m_s: float,  # Velocidad básica del viento v_b (m/s)
    height_z_m: float,            # Altura de la corona o alero (m)
    terrain_category: int = 2,    # Categoría de terreno (0 a IV)
    air_density: float = 1.25     # Densidad del aire (kg/m3)
) -> float:
    """Calcula la presión dinámica de pico q_p(z) según EN 1991-1-4.
    
    q_b = 0.5 * rho * v_b^2
    q_p(z) = c_e(z) * q_b
    """
    # 1. Presión básica del viento (N/m2)
    q_b = 0.5 * air_density * (basic_wind_speed_m_s ** 2)
    
    # 2. Factor de exposición c_e(z) aproximado para terreno estándar
    # Categoría II: Terreno plano cultivado con obstáculos bajos
    if terrain_category == 0:
        ce = 3.0 * (height_z_m / 10.0) ** 0.17
    elif terrain_category == 1:
        ce = 2.5 * (height_z_m / 10.0) ** 0.19
    elif terrain_category == 3:
        ce = 1.8 * (height_z_m / 10.0) ** 0.25
    elif terrain_category == 4:
        ce = 1.2 * (height_z_m / 10.0) ** 0.30
    else:  # Categoría II por defecto
        ce = 2.1 * (height_z_m / 10.0) ** 0.22
        
    qp = ce * q_b
    return qp / 1000.0  # -> en kPa (kN/m2)

def check_steel_member_interaction(
    N_Ed_kN: float,         # Esfuerzo axial de diseño (compresión = positivo)
    My_Ed_kNm: float,       # Momento flector alrededor del eje fuerte de diseño
    A_mm2: float,           # Área bruta de la sección de acero
    Wel_y_mm3: float,       # Módulo elástico de la sección alrededor de eje y
    fyi_MPa: float,         # Límite elástico del acero (e.g. S275 = 275.0)
    chi_y: float = 0.85,    # Factor de reducción por pandeo flexional (eje y)
    chi_LT: float = 0.90,   # Factor de reducción por pandeo lateral-torsional
    gamma_M0: float = 1.00, # Factor parcial para resistencia de secciones
    gamma_M1: float = 1.00  # Factor parcial para pandeo e inestabilidad de miembros
) -> dict[str, float | bool | str]:
    """Realiza la comprobación ULS de flexocompresión combinada según EN 1993-1-1 §6.3.3.
    
    Fórmula de interacción simplificada:
    (N_Ed / (chi_y * N_Rk / gamma_M1)) + (k_y * M_y_Ed / (chi_LT * M_y_Rk / gamma_M1)) <= 1.0
    """
    N_Rk = A_mm2 * fyi_MPa / 1000.0 # kN
    M_y_Rk = Wel_y_mm3 * fyi_MPa / 1e6 # kN m
    
    # Capacidad a compresión pura de diseño (kN)
    N_c_Rd = N_Rk / gamma_M0
    N_b_Rd = chi_y * N_Rk / gamma_M1
    
    # Capacidad a flexión pura de diseño (kN m)
    M_y_Rd = M_y_Rk / gamma_M0
    M_LT_Rd = chi_LT * M_y_Rk / gamma_M1
    
    # Ratios de comprobación individuales
    ratio_axial = N_Ed_kN / N_b_Rd if N_b_Rd else 0.0
    ratio_bending = My_Ed_kNm / M_LT_Rd if M_LT_Rd else 0.0
    
    # Coeficiente de interacción k_y (simplificado de Anexo B de EN 1993-1-1)
    k_y = 1.0 + 0.6 * ratio_axial
    if k_y > 1.4:
        k_y = 1.4
        
    # Ecuación de interacción combinada
    interaction_ratio = ratio_axial + k_y * ratio_bending
    ok = interaction_ratio <= 1.0
    
    return {
        "member_compression_capacity_kN": N_b_Rd,
        "member_bending_capacity_kNm": M_LT_Rd,
        "axial_utilization": ratio_axial,
        "bending_utilization": ratio_bending,
        "interaction_coefficient_ky": k_y,
        "combined_interaction_ratio": interaction_ratio,
        "ok": ok,
        "status": "CUMPLE" if ok else "SOBRECARGADO (Inestabilidad en flexocompresión)"
    }
