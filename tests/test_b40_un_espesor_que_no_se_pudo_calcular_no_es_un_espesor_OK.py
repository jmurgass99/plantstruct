"""B40: el memo de tanque API 650 publica «Espesor: OK» cuando NO pudo calcularlo.

EL CODIGO, LITERAL (`memos/tank_complete.py:95-112`)
------------------------------------------------------
    try:
        sc = shell_thickness_one_foot(D_m=inp.D_m, H_m=inp.H_l_m, G=inp.liquid_G)
        ...
        t_check_ok = inp.t_shell_mm >= sc.t_required_mm
    except ValueError:
        shell_thick_dict = {"t_required_mm": 0, "is_ok": True, "governing": "N/A"}
        sc = None
        t_check_ok = True

Una excepcion TRAGADA que produce un veredicto FAVORABLE. Y no se queda ahi:

    linea 181:  is_safe = a.is_safe and b.is_safe and t_check_ok
    linea 184:  f"- Espesor: {'OK' if t_check_ok else 'NO CUMPLE'}\\n"

asi que el tanque entero sale `is_safe` y la memoria imprime «Espesor: OK».

CUANDO SALTA -- Y AQUI EL HALLAZGO ORIGINAL SE QUEDABA CORTO
---------------------------------------------------------------
`shell_thickness_one_foot` lanza `ValueError` por DOS motivos:

    shell_design.py:57   if D_m <= 0 or H_m <= 0
    shell_design.py:59   if D_m > 60.0:  "Metodo del Pie valido solo para
                                          D <= 60 m; usar Variable-Design-Point"

El primero es INALCANZABLE desde el memo: `TankGeometry.validate()` ya rechaza
antes un D o un H no positivos (medido: revienta en api650.py:39). Apuntar ahi
habria sido arreglar codigo muerto.

El SEGUNDO es plenamente alcanzable, y es peor: una LIMITACION DE METODO
LEGITIMA --el Metodo del Pie no aplica por encima de 60 m de diametro-- se
convierte en un aprobado. Justo los tanques grandes, donde mas importa.

    t_required_mm = 0 no es «no hace falta espesor»: es «no se calculo».
    Y `0` es ademas el valor mas HOLGADO posible, porque cualquier espesor
    real lo supera: `inp.t_shell_mm >= 0` es cierto siempre.

LA GUARDA QUE HACE FALTA, Y LA QUE NO
---------------------------------------
Un tanque con geometria VALIDA cuyo espesor cumple debe seguir diciendo OK. Si
el arreglo tumbara tambien ese caso seria el error contrario. Lo que cambia es
solo el camino de la excepcion.
"""
from __future__ import annotations

import pytest

from industrialjm.memos.tank_complete import TankMemoInput, render_tank_memo

SANO = dict(D_m=20.0, H_l_m=12.0, H_shell_m=13.0, t_shell_mm=12.0,
            Sa_i_g=0.30, Sa_c_g=0.15)
#: D = 70 m: el Metodo del Pie NO aplica (API 650 lo limita a 60 m), asi que
#: `shell_thickness_one_foot` lanza y el memo se traga la excepcion.
#: MEDIDO: hoy publica «- Espesor: OK».
FUERA_DE_METODO = {**SANO, "D_m": 70.0}


# =========================================================================== #
# A. Lo que no se pudo calcular no firma
# =========================================================================== #

def test_LO_QUE_NO_PUDE_DEMOSTRAR_queda_dicho() -> None:
    """Honestidad sobre el alcance, en vez de afirmar de mas.

    En el codigo, `t_check_ok = True` SI entra en
    `is_safe = a.is_safe and b.is_safe and t_check_ok` (linea 181). Pero NO he
    conseguido una entrada con D > 60 m donde `is_safe` salga True: un tanque de
    ese tamano falla por anclaje o pandeo de todas formas (medido con
    Sa = 0.30 / 0.05 / 0.01 y varias alturas y espesores).

    Luego lo que hoy impide que el veredicto global mienta es un ACCIDENTE, no
    una guarda -- el mismo patron que ya aparecio en `hinge_states`, donde un
    `KeyError` colateral tapaba la rama mala. Un accidente no protege nada: en
    cuanto alguien ajuste el anclaje, el aprobado sale. Este test fija que el
    accidente existe HOY, para que si cambia se entere alguien.
    """
    res = render_tank_memo(TankMemoInput(**FUERA_DE_METODO))
    assert res.is_safe is False


def test_y_la_memoria_no_imprime_Espesor_OK() -> None:
    res = render_tank_memo(TankMemoInput(**FUERA_DE_METODO))
    assert "Espesor: OK" not in res.markdown, (
        "la memoria de calculo afirma por escrito que el espesor cumple"
    )
    assert "NO CALCULADO" in res.markdown.upper() or \
           "NO SE PUDO" in res.markdown.upper(), res.markdown[-600:]


def test_el_t_required_de_CERO_no_se_publica_como_un_requisito() -> None:
    """`0` no es «no hace falta espesor»: es «no se calculo». Y es ademas el
    valor mas holgado posible, porque `t_real >= 0` es cierto siempre."""
    res = render_tank_memo(TankMemoInput(**FUERA_DE_METODO))
    texto = res.markdown
    assert "t_required_mm = 0" not in texto.replace(" ", "").replace("=", " = ")


# =========================================================================== #
# B. GUARDA CONTRA LA VERDAD VACIA: el tanque sano sigue firmando
# =========================================================================== #

def test_un_tanque_VALIDO_con_espesor_suficiente_sigue_diciendo_OK() -> None:
    res = render_tank_memo(TankMemoInput(**SANO))
    assert "Espesor: OK" in res.markdown or "Espesor: NO CUMPLE" in res.markdown, (
        "si el arreglo tumbara tambien el caso sano seria el error contrario: "
        "la memoria dejaria de distinguir un tanque bueno de uno sin datos"
    )
    assert "NO CALCULADO" not in res.markdown.upper()


def test_y_un_tanque_VALIDO_con_espesor_INSUFICIENTE_sigue_fallando() -> None:
    delgado = {**SANO, "t_shell_mm": 0.5}
    res = render_tank_memo(TankMemoInput(**delgado))
    assert res.is_safe is False
    assert "NO CUMPLE" in res.markdown
