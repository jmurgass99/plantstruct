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

K_Y_BASIS = (
    "EN 1993-1-1 Anexo B, Tabla B.1 (Metodo 2, clases 1-2) SIMPLIFICADA: "
    "k_y = min(1 + 0.6*n, 1.4), equivalente a C_my = 1.0 y lambda_y = 0.8 "
    "CLAVADOS (lambda_y = esbeltez adimensional del soporte, que esta funcion "
    "NO recibe). Para lambda_y > 0.8 el valor SUBESTIMA k_yy y es INSEGURO; "
    "el techo 1.4 no procede de la Tabla B.1."
)

K_Y_BASIS_EXACT = (
    "EN 1993-1-1 Anexo B, Tabla B.1 (Metodo 2, clases 1-2) EXACTA: "
    "k_yy = C_my * (1 + min(lambda_y - 0.2, 0.8) * n_y)."
)


def calculate_wind_pressure(
    basic_wind_speed_m_s: float,  # Velocidad básica del viento v_b (m/s)
    height_z_m: float,            # Altura de la corona o alero (m)
    terrain_category: int | str = 2,  # Categoría de terreno (0 a IV)
    air_density: float = 1.25     # Densidad del aire (kg/m3)
) -> float:
    """Calcula la presión dinámica de pico q_p(z) según EN 1991-1-4."""
    q_b = 0.5 * air_density * (basic_wind_speed_m_s ** 2)

    _CAT_MAP = {"0": 0, "I": 1, "1": 1, "II": 2, "2": 2, "III": 3, "3": 3, "IV": 4, "4": 4}
    cat = _CAT_MAP.get(str(terrain_category).strip().upper())
    if cat is None:
        raise ValueError(
            f"calculate_wind_pressure: terrain_category={terrain_category!r} no válida. "
            "Valores permitidos según EN 1991-1-4 Tabla 4.1: 0, 1, 2, 3, 4 (o '0', 'I', 'II', 'III', 'IV')."
        )

    if cat == 0:
        ce = 3.0 * (height_z_m / 10.0) ** 0.17
    elif cat == 1:
        ce = 2.5 * (height_z_m / 10.0) ** 0.19
    elif cat == 2:
        ce = 2.1 * (height_z_m / 10.0) ** 0.22
    elif cat == 3:
        ce = 1.8 * (height_z_m / 10.0) ** 0.25
    elif cat == 4:
        ce = 1.2 * (height_z_m / 10.0) ** 0.30

    qp = ce * q_b
    return qp / 1000.0  # -> en kPa (kN/m2)


def _validar_flexocompresion(
    N_Ed_kN: float, A_mm2: float, Wel_y_mm3: float, fyi_MPa: float,
    chi_y: float, chi_LT: float, gamma_M0: float, gamma_M1: float,
) -> None:
    quien = "check_steel_member_interaction"
    for nombre, valor in (("A_mm2", A_mm2), ("Wel_y_mm3", Wel_y_mm3),
                          ("fyi_MPa", fyi_MPa)):
        if not valor > 0:
            raise ValueError(
                f"{quien}: {nombre}={valor:g} debe ser > 0. Una sección sin "
                "área, sin módulo resistente o sin límite elástico no tiene "
                "capacidad que comprobar; el resultado sería un CUMPLE sobre "
                "una barra que no existe."
            )
    for nombre, valor, clausula in (("chi_y", chi_y, "§6.3.1.2"),
                                    ("chi_LT", chi_LT, "§6.3.2.2")):
        if valor is None:
            raise ValueError(
                f"{quien}: {nombre} debe proporcionarse explícitamente. "
                "No se asumen factores de reducción por defecto (0.85/0.90)."
            )
        if not 0.0 < valor <= 1.0:
            raise ValueError(
                f"{quien}: {nombre}={valor:g} fuera de (0, 1]. El factor de "
                f"reducción por pandeo de {clausula} es > 0 y <= 1; un cero no "
                "es 'sin pandeo', es 'NO CALCULADO', y con él el término "
                "correspondiente de la Eq. (6.61) no se puede evaluar."
            )
    for nombre, valor in (("gamma_M0", gamma_M0), ("gamma_M1", gamma_M1)):
        if not valor > 0:
            raise ValueError(f"{quien}: {nombre}={valor:g} debe ser > 0")
    if N_Ed_kN < 0:
        raise ValueError(
            f"{quien}: N_Ed_kN={N_Ed_kN:g} kN es TRACCIÓN, y EN 1993-1-1 "
            "§6.3.3 cubre 'members in bending and axial compression'. Aquí la "
            "tracción restaría del ratio de interacción y podría aprobar una "
            "barra sobrecargada a flexión. Use la comprobación de tracción + "
            "flexión que corresponda; N_Ed_kN=0 sí es válido (flexión pura)."
        )


def check_steel_member_interaction(
    N_Ed_kN: float,
    My_Ed_kNm: float,
    A_mm2: float,
    Wel_y_mm3: float,
    fyi_MPa: float,
    chi_y: float | None = None,
    chi_LT: float | None = None,
    gamma_M0: float = 1.00,
    gamma_M1: float = 1.00,
    *,
    lambda_y: float | None = None,
    C_my: float = 1.0,
) -> dict[str, float | bool | str]:
    """Realiza la comprobación ULS de flexocompresión combinada según EN 1993-1-1 §6.3.3.

    Si se proporciona ``lambda_y`` (esbeltez adimensional del soporte en eje fuerte),
    calcula ``k_yy`` con la fórmula exacta de la Tabla B.1 (Método 2, Clases 1-2):
        k_yy = C_my * (1 + min(lambda_y - 0.2, 0.8) * n_y)
    Si ``lambda_y is None``, mantiene la fórmula de caracterización histórica.
    """
    _validar_flexocompresion(N_Ed_kN, A_mm2, Wel_y_mm3, fyi_MPa,
                             chi_y, chi_LT, gamma_M0, gamma_M1)

    N_Rk = A_mm2 * fyi_MPa / 1000.0
    M_y_Rk = Wel_y_mm3 * fyi_MPa / 1e6

    N_c_Rd = N_Rk / gamma_M0
    N_b_Rd = chi_y * N_Rk / gamma_M1

    M_y_Rd = M_y_Rk / gamma_M0
    M_LT_Rd = chi_LT * M_y_Rk / gamma_M1

    ratio_axial = N_Ed_kN / N_b_Rd
    ratio_bending = My_Ed_kNm / M_LT_Rd

    if lambda_y is not None:
        if lambda_y < 0.0 or C_my <= 0.0:
            raise ValueError("lambda_y >= 0 y C_my > 0 requeridos")
        factor_lam = min(max(lambda_y - 0.2, 0.0), 0.8)
        k_y = C_my * (1.0 + factor_lam * ratio_axial)
        basis = K_Y_BASIS_EXACT
    else:
        k_y = 1.0 + 0.6 * ratio_axial
        if k_y > 1.4:
            k_y = 1.4
        basis = K_Y_BASIS

    interaction_ratio = ratio_axial + k_y * ratio_bending
    ok = interaction_ratio <= 1.0

    return {
        "member_compression_capacity_kN": N_b_Rd,
        "member_bending_capacity_kNm": M_LT_Rd,
        "axial_utilization": ratio_axial,
        "bending_utilization": ratio_bending,
        "interaction_coefficient_ky": k_y,
        "k_y_basis": basis,
        "combined_interaction_ratio": interaction_ratio,
        "ok": ok,
        "status": "CUMPLE" if ok else "SOBRECARGADO (Inestabilidad en flexocompresión)"
    }
