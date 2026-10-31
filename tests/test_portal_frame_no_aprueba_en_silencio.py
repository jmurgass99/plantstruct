# -*- coding: utf-8 -*-
"""portal_frame.check_steel_member_interaction NO puede aprobar en silencio.

QUE SE COMPRUEBA AQUI Y QUE NO
------------------------------
Esto NO son goldens: no hay ningun valor de norma ni de ejemplo publicado
contrastado contra el modulo.  Son INVARIANTES de honestidad ("una barra con
capacidad nula no puede salir CUMPLE") mas un caso de CARACTERIZACION
explicitamente marcado, que fija la rama valida para que el arreglo no la
mueva.

EL DEFECTO QUE MOTIVA EL FICHERO
--------------------------------
``portal_frame.py`` calculaba::

    ratio_axial   = N_Ed_kN  / N_b_Rd  if N_b_Rd  else 0.0
    ratio_bending = My_Ed_kNm/ M_LT_Rd if M_LT_Rd else 0.0

Cuando la capacidad de pandeo es nula (``chi_y = 0``, ``A = 0``, ``fy = 0``)
el ratio -que deberia diverger- se fabricaba a 0.0 y DESAPARECIA del sumatorio
de interaccion.  Medido antes del arreglo: 500 kN y 1e9 kN sobre la misma
IPE 400 con ``chi_y = 0`` devolvian salida identica byte a byte,
``combined_interaction_ratio = 0.3495``, ``ok = True``, ``"CUMPLE"``.

Y una tercera via, independiente de esas dos lineas: con ``N_Ed`` NEGATIVO
(traccion) el termino axial se vuelve negativo y RESTA del sumatorio.  Medido
antes del arreglo sobre IPE 400 S275 con My_Ed = 330 kNm (utilizacion a
flexion 1.153, o sea un 15 % sobrecargada): ``combined_interaction_ratio =
-0.132``, ``ok = True``, ``"CUMPLE"``.  Anadir traccion "arreglaba" una viga
sobrecargada.  EN 1993-1-1 §6.3.3 se titula "Uniform members in bending and
axial COMPRESSION": la traccion esta fuera del capitulo.

Los tests estan escritos para ser AGNOSTICOS A LA FORMA DEL ARREGLO: aceptan
tanto que la funcion rechace la entrada (excepcion) como que devuelva un
veredicto no aprobatorio.  Lo unico que prohiben es el CUMPLE en silencio.
Cuando la respuesta es un rechazo, se exige ademas que el mensaje NOMBRE el
parametro culpable, para que la rama de rechazo no la pueda satisfacer una
excepcion cualquiera.
"""
from __future__ import annotations

import pytest

from plantstruct.portal_frame import check_steel_member_interaction

# IPE 400 / HEB 300, S275 (A y Wel,y de EN 10365).  El catalogo NO se importa
# aqui a proposito: estos tests no verifican el catalogo, verifican la funcion.
IPE400_S275 = dict(A_mm2=8446.0, Wel_y_mm3=1_156_000.0, fyi_MPa=275.0)
HEB300_S275 = dict(A_mm2=14_910.0, Wel_y_mm3=1_678_000.0, fyi_MPa=275.0)

RECHAZADO = "RECHAZADO"
CALCULADO = "CALCULADO"


def _veredicto(**kw) -> tuple[str, object]:
    """Llama a la funcion y normaliza las dos respuestas honestas posibles.

    Devuelve ``(RECHAZADO, mensaje)`` si la funcion se niega a calcular con
    esa entrada, o ``(CALCULADO, dict)`` si emite un resultado.

    ``TypeError`` NO se captura: una firma rota debe romper el test, no
    colarse por la puerta del rechazo legitimo.
    """
    try:
        return (CALCULADO, check_steel_member_interaction(**kw))
    except (ValueError, ZeroDivisionError) as exc:
        return (RECHAZADO, f"{type(exc).__name__}: {exc}")


def _exigir_rechazo_explicito(mensaje: str, parametro: str) -> None:
    """El rechazo tiene que decir QUE dato es el que falta o sobra."""
    assert parametro in mensaje, (
        f"la entrada se rechazo, pero el mensaje no nombra {parametro!r}, "
        f"asi que el test no distingue este rechazo de cualquier otro: "
        f"{mensaje!r}"
    )


# ---------------------------------------------------------------------------
# 1. INVARIANTE PRINCIPAL: el veredicto no puede ignorar el axil
# ---------------------------------------------------------------------------
def test_el_veredicto_no_puede_ser_independiente_del_axil():
    """Multiplicar el axil por 2e6 tiene que cambiar algo.

    Este es el invariante que el fallo violaba de forma mas flagrante: con
    ``chi_y = 0`` el termino axial salia del sumatorio y la funcion devolvia
    EXACTAMENTE el mismo diccionario para 500 kN y para 1e9 kN.

    Se escribe como invariante -y no como "debe lanzar ValueError"- para que
    siga cazando el fallo si alguien reintroduce un valor fabricado por otra
    via (un minimo, un ``max(x, 1e-9)``, un clamp).
    """
    base = dict(My_Ed_kNm=100.0, chi_y=0.0, **IPE400_S275)
    estado_bajo, bajo = _veredicto(N_Ed_kN=500.0, **base)
    estado_alto, alto = _veredicto(N_Ed_kN=1e9, **base)

    if estado_bajo == RECHAZADO and estado_alto == RECHAZADO:
        _exigir_rechazo_explicito(str(bajo), "chi_y")
        _exigir_rechazo_explicito(str(alto), "chi_y")
        return  # la ausencia se propago como ausencia: correcto

    assert estado_bajo == estado_alto == CALCULADO
    assert bajo != alto, (
        "APROBADO SILENCIOSO: 500 kN y 1e9 kN sobre la misma barra con "
        f"capacidad de pandeo nula devuelven el MISMO resultado: {bajo}"
    )


# ---------------------------------------------------------------------------
# 2. Capacidad nula por chi_y (linea 70): jamas CUMPLE
# ---------------------------------------------------------------------------
def test_capacidad_axial_nula_nunca_declara_cumple():
    """``chi_y = 0`` -> ``N_b_Rd = 0 kN``. Ninguna compresion cabe ahi."""
    estado, r = _veredicto(N_Ed_kN=1e9, My_Ed_kNm=100.0, chi_y=0.0,
                           **IPE400_S275)
    if estado == RECHAZADO:
        _exigir_rechazo_explicito(str(r), "chi_y")
        return
    assert r["ok"] is not True, (
        "APROBADO SILENCIOSO: 1e9 kN de compresion sobre una barra con "
        f"member_compression_capacity_kN = {r['member_compression_capacity_kN']} "
        f"-> {r['status']!r}. Resultado completo: {r}"
    )


# ---------------------------------------------------------------------------
# 3. Capacidad nula por chi_LT (linea 71): jamas CUMPLE
# ---------------------------------------------------------------------------
def test_capacidad_a_flexion_nula_nunca_declara_cumple():
    """Misma patologia en el termino de flexion: ``chi_LT = 0``."""
    estado, r = _veredicto(N_Ed_kN=1000.0, My_Ed_kNm=1e6, chi_y=0.85, chi_LT=0.0,
                           **HEB300_S275)
    if estado == RECHAZADO:
        _exigir_rechazo_explicito(str(r), "chi_LT")
        return
    assert r["ok"] is not True, (
        "APROBADO SILENCIOSO: 1e6 kNm sobre una barra con "
        f"member_bending_capacity_kNm = {r['member_bending_capacity_kNm']} "
        f"-> {r['status']!r}. Resultado completo: {r}"
    )


# ---------------------------------------------------------------------------
# 4. Seccion inexistente: capacidad nula en LOS DOS ejes
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "titulo, parametro, seccion",
    [
        ("area nula", "A_mm2",
         dict(A_mm2=0.0, Wel_y_mm3=1_156_000.0, fyi_MPa=275.0)),
        ("modulo resistente nulo", "Wel_y_mm3",
         dict(A_mm2=8446.0, Wel_y_mm3=0.0, fyi_MPa=275.0)),
        ("grado de acero ausente", "fyi_MPa",
         dict(A_mm2=8446.0, Wel_y_mm3=1_156_000.0, fyi_MPa=0.0)),
    ],
)
def test_barra_sin_capacidad_nunca_declara_cumple(titulo, parametro, seccion):
    """Una barra que no existe no puede CUMPLIR.

    Antes del arreglo, ``A = 0`` y ``fy = 0`` devolvian ambos
    ``combined_interaction_ratio = 0.0`` y ``"CUMPLE"``: los dos ratios se
    fabricaban a cero a la vez y el sumatorio quedaba vacio.
    """
    estado, r = _veredicto(N_Ed_kN=500.0, My_Ed_kNm=100.0, chi_y=0.85, chi_LT=0.90, **seccion)
    if estado == RECHAZADO:
        _exigir_rechazo_explicito(str(r), parametro)
        return
    assert r["ok"] is not True, (
        f"APROBADO SILENCIOSO ({titulo}): capacidades "
        f"{r['member_compression_capacity_kN']} kN / "
        f"{r['member_bending_capacity_kNm']} kNm -> {r['status']!r}"
    )


# ---------------------------------------------------------------------------
# 5. El veredicto no puede MEJORAR cuando la barra empeora
# ---------------------------------------------------------------------------
def test_el_veredicto_no_mejora_al_reducir_chi_y():
    """Monotonia: si a ``chi_y = 1e-12`` la barra esta SOBRECARGADA, a
    ``chi_y = 0`` no puede estar CUMPLE.

    Medido antes del arreglo (IPE 400, N_Ed = 500 kN, My_Ed = 100 kNm):
    chi_y = 1e-12 -> interaccion 2.15e+11 (SOBRECARGADO)
    chi_y = 0     -> interaccion 0.3495   (CUMPLE)
    Un salto de once ordenes de magnitud justo donde la funcion deberia
    diverger.
    """
    fijos = dict(N_Ed_kN=500.0, My_Ed_kNm=100.0, chi_LT=0.90, **IPE400_S275)
    ya_fallaba = False
    for chi in (1e-2, 1e-4, 1e-6, 1e-9, 1e-12, 0.0):
        estado, r = _veredicto(chi_y=chi, **fijos)
        if estado == RECHAZADO:
            continue
        if ya_fallaba:
            assert r["ok"] is not True, (
                f"APROBADO SILENCIOSO: con chi_y mayor la barra estaba "
                f"SOBRECARGADA, y al bajar a chi_y = {chi:g} pasa a "
                f"{r['status']!r} (interaccion {r['combined_interaction_ratio']})"
            )
        if r["ok"] is False:
            ya_fallaba = True
    assert ya_fallaba, "el barrido no llego a sobrecargar la barra: test inutil"


# ---------------------------------------------------------------------------
# 6. Traccion: §6.3.3 no la cubre y no puede servir para aprobar
# ---------------------------------------------------------------------------
def test_la_traccion_no_puede_compensar_una_flexion_sobrecargada():
    """Tercera via de aprobado silencioso, independiente de las lineas 70-71.

    Con ``N_Ed < 0`` el termino axial de la Eq. (6.61) se vuelve negativo y
    RESTA, y ademas hunde ``k_y`` por debajo de 1.0.  Medido antes del
    arreglo: la MISMA IPE 400 con My_Ed = 330 kNm da interaccion 1.153
    (SOBRECARGADO) con N_Ed = 0, y interaccion -0.132 (CUMPLE) con
    N_Ed = -1500 kN.

    EN 1993-1-1 §6.3.3 se titula "Uniform members in bending and axial
    COMPRESSION"; la traccion es otro capitulo, no un caso favorable de este.
    """
    _, sin_axil = _veredicto(N_Ed_kN=0.0, My_Ed_kNm=330.0, chi_y=0.85, chi_LT=0.90, **IPE400_S275)
    assert sin_axil["ok"] is False, (
        "premisa del test rota: la barra deberia estar sobrecargada a flexion "
        f"pura, y da {sin_axil}"
    )

    estado, r = _veredicto(N_Ed_kN=-1500.0, My_Ed_kNm=330.0, chi_y=0.85, chi_LT=0.90, **IPE400_S275)
    if estado == RECHAZADO:
        _exigir_rechazo_explicito(str(r), "N_Ed_kN")
        return
    assert r["ok"] is not True, (
        "APROBADO SILENCIOSO: la misma barra sobrecargada a flexion pura "
        f"(interaccion {sin_axil['combined_interaction_ratio']:.4f}) pasa a "
        f"{r['status']!r} con interaccion {r['combined_interaction_ratio']:.4f} "
        "solo por anadirle traccion"
    )


# ---------------------------------------------------------------------------
# 7. CARACTERIZACION (no golden): la rama valida no debe moverse
# ---------------------------------------------------------------------------
def test_caracterizacion_rama_valida_no_cambia():
    """CARACTERIZACION, NO GOLDEN.

    Los numeros de abajo se capturaron de la PROPIA implementacion antes del
    arreglo; no proceden de ningun capitulo de norma ni de ningun ejemplo
    publicado.  Solo sirven para demostrar que la validacion anadida no toca
    la rama de entradas validas.

    Aritmetica reproducible a mano:
        N_Rk    = 8446 * 275 / 1000               = 2322.65     kN
        N_b_Rd  = 0.85 * 2322.65                  = 1974.2525   kN
        M_y_Rk  = 1156000 * 275 / 1e6             =  317.9      kNm
        M_LT_Rd = 0.90 * 317.9                    =  286.11     kNm
        n       = 500 / 1974.2525                 =    0.25326041
        k_y     = 1 + 0.6 * n                     =    1.15195625
        interac = n + k_y * (100 / 286.11)        =    0.65588746
    """
    r = check_steel_member_interaction(
        N_Ed_kN=500.0, My_Ed_kNm=100.0, chi_y=0.85, chi_LT=0.90, **IPE400_S275)
    assert r["member_compression_capacity_kN"] == pytest.approx(1974.2525)
    assert r["member_bending_capacity_kNm"] == pytest.approx(286.11)
    assert r["axial_utilization"] == pytest.approx(0.25326041, rel=1e-8)
    assert r["bending_utilization"] == pytest.approx(0.34951592, rel=1e-8)
    assert r["interaction_coefficient_ky"] == pytest.approx(1.15195625, rel=1e-8)
    assert r["combined_interaction_ratio"] == pytest.approx(0.65588746, rel=1e-8)
    assert r["ok"] is True
    assert r["status"] == "CUMPLE"


def test_flexion_pura_sigue_siendo_calculable():
    """``N_Ed = 0`` es flexion pura, un caso legitimo de la Eq. (6.61): el
    termino axial vale cero de verdad, no fabricado.  La validacion no puede
    rechazarlo."""
    r = check_steel_member_interaction(
        N_Ed_kN=0.0, My_Ed_kNm=100.0, chi_y=0.85, chi_LT=0.90, **IPE400_S275)
    assert r["axial_utilization"] == 0.0
    assert r["interaction_coefficient_ky"] == pytest.approx(1.0)
    assert r["combined_interaction_ratio"] == pytest.approx(0.34951592, rel=1e-8)
    assert r["ok"] is True
