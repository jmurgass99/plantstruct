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

# Declaración que viaja con cada resultado: qué hipótesis lleva dentro el k_y
# que se ha usado. Mismo idioma que `axial_basis` en tanks/shell_buckling.py.
#
# Sin caracteres fuera de cp1252 A PROPÓSITO: esta cadena sale en cada
# resultado y una consola Windows por defecto la imprime; "lambda_y" en ASCII
# en vez del símbolo evita un UnicodeEncodeError en el consumidor.
K_Y_BASIS = (
    "EN 1993-1-1 Anexo B, Tabla B.1 (Metodo 2, clases 1-2) SIMPLIFICADA: "
    "k_y = min(1 + 0.6*n, 1.4), equivalente a C_my = 1.0 y lambda_y = 0.8 "
    "CLAVADOS (lambda_y = esbeltez adimensional del soporte, que esta funcion "
    "NO recibe). Para lambda_y > 0.8 el valor SUBESTIMA k_yy y es INSEGURO; "
    "el techo 1.4 no procede de la Tabla B.1."
)

def calculate_wind_pressure(
    basic_wind_speed_m_s: float,  # Velocidad básica del viento v_b (m/s)
    height_z_m: float,            # Altura de la corona o alero (m)
    terrain_category: int | str = 2,  # Categoría de terreno (0 a IV)
    air_density: float = 1.25     # Densidad del aire (kg/m3)
) -> float:
    """Calcula la presión dinámica de pico q_p(z) según EN 1991-1-4.
    
    q_b = 0.5 * rho * v_b^2
    q_p(z) = c_e(z) * q_b
    """
    # 1. Presión básica del viento (N/m2)
    q_b = 0.5 * air_density * (basic_wind_speed_m_s ** 2)
    
    # 2. Factor de exposición c_e(z) según EN 1991-1-4 Tabla 4.1
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
    """Rechaza las entradas que EN 1993-1-1 §6.3.3 no puede comprobar.

    Antes de existir esta función, la ausencia de capacidad se fabricaba a cero
    y se propagaba como un aprobado. Con ``chi_y = 0`` (o ``A = 0``, o
    ``fy = 0``) la capacidad a pandeo ``N_b_Rd`` valía 0 kN, el término axial
    de la Eq. (6.61) se sustituía por ``0.0`` y DESAPARECÍA del sumatorio: la
    función devolvía salida idéntica byte a byte para 500 kN y para 1e9 kN de
    compresión sobre una barra que no aguanta ninguna de las dos, con
    ``ok = True`` y ``status = "CUMPLE"``.

    Un chi o un área que faltan no son un cero: son un dato que no se ha
    calculado, y con él la mitad de la comprobación no existe. Como aquí no hay
    respuesta parcial que dar -a diferencia de ``bases_columna.py``, donde el
    modo del acero se calcula aunque falten los del hormigón-, la salida
    honesta es negarse a emitir veredicto, no emitir uno incompleto.

    ``N_Ed`` negativo se rechaza por el mismo motivo: §6.3.3 se titula "Uniform
    members in bending and axial COMPRESSION". Con tracción el término axial se
    vuelve negativo y RESTA del sumatorio, además de hundir ``k_y`` por debajo
    de 1.0; medido sobre IPE 400 S275 con My_Ed = 330 kNm, la barra pasaba de
    interacción 1.153 (SOBRECARGADO) a -0.132 (CUMPLE) solo por añadirle
    1500 kN de tracción. La tracción con flexión es otro capítulo, no un caso
    favorable de éste. ``N_Ed = 0`` sí es válido: es flexión pura, y entonces el
    término axial vale cero de verdad.
    """
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
    N_Ed_kN: float,         # Esfuerzo axial de diseño (compresión = positivo)
    My_Ed_kNm: float,       # Momento flector alrededor del eje fuerte de diseño
    A_mm2: float,           # Área bruta de la sección de acero
    Wel_y_mm3: float,       # Módulo elástico de la sección alrededor de eje y
    fyi_MPa: float,         # Límite elástico del acero (e.g. S275 = 275.0)
    chi_y: float | None = None,   # Factor de reducción por pandeo flexional (eje y, obligatorio)
    chi_LT: float | None = None,  # Factor de reducción por pandeo lateral-torsional (obligatorio)
    gamma_M0: float = 1.00, # Factor parcial para resistencia de secciones
    gamma_M1: float = 1.00  # Factor parcial para pandeo e inestabilidad de miembros
) -> dict[str, float | bool | str]:
    """Realiza la comprobación ULS de flexocompresión combinada según EN 1993-1-1 §6.3.3.

    Fórmula de interacción simplificada:
    (N_Ed / (chi_y * N_Rk / gamma_M1)) + (k_y * M_y_Ed / (chi_LT * M_y_Rk / gamma_M1)) <= 1.0

    Es la Eq. (6.61) de §6.3.3 con M_z,Ed = 0 (flexión sólo en el eje fuerte).

    QUÉ SOSTIENE EL k_y Y QUÉ NO
    ----------------------------
    (``lambda_y`` = esbeltez adimensional del soporte respecto al eje fuerte.
    Se escribe en ASCII, no con el símbolo, para que este docstring y la cadena
    ``k_y_basis`` se puedan imprimir en una consola Windows cp1252.)

    ``k_y = min(1 + 0.6*n, 1.4)``, con ``n`` la utilización axial. La Tabla B.1
    del Anexo B (Método 2), para clases 1-2, es::

        k_yy = C_my * (1 + (lambda_y - 0.2)*n)   ,  <= C_my * (1 + 0.8*n)

    (forma corroborada contra el módulo hermano canónico del monorepo,
    ``packages/fastsap/fastsap/codes/ec3_interaction.py:47-62``; el texto de la
    norma NO se ha consultado aquí). Comparando término a término, lo que hay
    implementado equivale a ``C_my = 1.0`` y ``lambda_y = 0.8`` CLAVADOS: el
    0.6 no es una constante de la norma, es ``(lambda_y - 0.2)`` con una
    esbeltez concreta metida dentro. Para barras más esbeltas que
    lambda_y = 0.8 el módulo SUBESTIMA k_yy, y eso es inseguro. Medido:
    k_yy(Tabla B.1)/k_y(módulo) va de 0.82 a lambda_y = 0.418 (conservador) a
    1.29 a lambda_y = 1.064 con n = 1.0 (inseguro). El signo del error depende
    de la esbeltez del soporte, que esta función NO recibe.

    El techo ``1.4`` TAMPOCO es el de la Tabla B.1: el techo de la tabla es
    ``C_my*(1 + 0.8*n)``, que con C_my = 1 y lambda_y = 0.8 nunca puede morder
    (1 + 0.6*n <= 1 + 0.8*n para todo n >= 0). Es un tope sin respaldo
    localizado, y por ser un tope sobre k_y es inseguro por encima de
    n ~ 0.667.

    Corregirlo exige recibir lambda_y y C_my como entradas; se deja declarado,
    no silenciado, y ``k_y_basis`` lo repite en cada resultado.
    """
    _validar_flexocompresion(N_Ed_kN, A_mm2, Wel_y_mm3, fyi_MPa,
                             chi_y, chi_LT, gamma_M0, gamma_M1)

    N_Rk = A_mm2 * fyi_MPa / 1000.0 # kN
    M_y_Rk = Wel_y_mm3 * fyi_MPa / 1e6 # kN m
    
    # Capacidad a compresión pura de diseño (kN)
    N_c_Rd = N_Rk / gamma_M0
    N_b_Rd = chi_y * N_Rk / gamma_M1
    
    # Capacidad a flexión pura de diseño (kN m)
    M_y_Rd = M_y_Rk / gamma_M0
    M_LT_Rd = chi_LT * M_y_Rk / gamma_M1
    
    # Ratios de comprobación individuales.
    # Sin fallback: _validar_flexocompresion ya garantiza que los denominadores
    # son > 0. Un `if N_b_Rd else 0.0` aquí borraría el término axial del
    # sumatorio y devolvería CUMPLE para cualquier compresión (ver su docstring).
    ratio_axial = N_Ed_kN / N_b_Rd
    ratio_bending = My_Ed_kNm / M_LT_Rd

    # Coeficiente de interacción k_y. Anexo B, Tabla B.1 (Método 2) con
    # C_my = 1.0 y lambda_y = 0.8 clavados, y un techo 1.4 sin respaldo:
    # ver la sección "QUÉ SOSTIENE EL k_y Y QUÉ NO" del docstring.
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
        "k_y_basis": K_Y_BASIS,
        "combined_interaction_ratio": interaction_ratio,
        "ok": ok,
        "status": "CUMPLE" if ok else "SOBRECARGADO (Inestabilidad en flexocompresión)"
    }
