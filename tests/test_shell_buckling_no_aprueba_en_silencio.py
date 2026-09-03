"""`check_shell_buckling_full` no puede declarar seguro lo que no ha verificado.

DOS DEFECTOS DISTINTOS, los dos medidos antes de tocar nada.

1. APROBADO SILENCIOSO (lineas 215-217). Con capacidad <= 0 los tres DCR
   individuales caian a `0.0`, que es el valor de "sobra margen". El mismo
   fichero ya contenia la respuesta correcta: `check_shell_buckling`, veinte
   lineas antes, usa `float("inf")` para exactamente la misma magnitud. Con el
   MISMO input (E_MPa=0):

       check_shell_buckling       -> DCR inf / inf, is_safe = False
       check_shell_buckling_full  -> DCR 0.0 / 0.0, is_safe = True

   ...y la demanda circunferencial real de ese caso era 134.9 MPa. Un manto sin
   capacidad y con 135 MPa encima salia por la API como seguro.

2. LA BRECHA DE ROTTER (lineas 204 y 224). El resultado publica DOS capacidades
   axiales: `Fbi_axial` con el factor de imperfeccion de entrada (0.6 por
   defecto) y `Fbi_diamond` con el knockdown de Rotter, alpha = 1/(1+0.005 R/t).
   El veredicto (`DCR_axial`, `is_safe`, `governing_mode`) usa SIEMPRE la
   primera, la menos conservadora, y nada en la salida decia cual gobernaba.
   Medido:

       D=20 m  t= 8 mm  R/t=1250  Fbi 96.00 vs 22.07  -> 4.35x
       D=30 m  t= 6 mm  R/t=2500  Fbi 48.00 vs  5.93  -> 8.10x
       D=12 m  t=10 mm  R/t= 600  Fbi 200.0 vs 83.33  -> 2.40x

   En el tanque de 30 m el DCR publicado es 0.104 -- parece que no pasa nada --
   y por la ruta de Rotter es 0.844, rozando el limite. Mismo tanque, misma
   carga.

   Cual de las dos DEBE gobernar es una decision de norma, no de este test: se
   deja donde estaba (API 650) y se hace VISIBLE la otra, que es lo que faltaba.
"""
from __future__ import annotations

import math

import pytest

from industrialjm.tanks.shell_buckling import (
    ShellBucklingFullInput,
    ShellBucklingInput,
    check_shell_buckling,
    check_shell_buckling_full,
)

# Tanque corriente: 20 m de diametro, 12 m de manto, 8 mm de chapa.
BASE = dict(D_m=20.0, H_shell_m=12.0, H_liquid_m=11.0, t_shell_mm=8.0,
            sigma_axial_imposed_MPa=50.0, sigma_bending_MPa=10.0)


# ---------------------------------------------------------------------------
# 1. El aprobado silencioso
# ---------------------------------------------------------------------------
def test_capacidad_nula_no_puede_declararse_segura() -> None:
    """E = 0 anula las tres capacidades. Antes: los tres DCR a 0.0 e
    `is_safe = True`, con 134.9 MPa de demanda circunferencial."""
    r = check_shell_buckling_full(ShellBucklingFullInput(**BASE, E_MPa=0.0))

    assert r.Fbi_axial_MPa == 0.0 and r.Fc_hoop_MPa == 0.0
    assert r.sigma_hoop_demand_MPa > 100.0, "el caso debe tener demanda real"
    assert math.isinf(r.DCR_axial)
    assert math.isinf(r.DCR_hoop)
    assert math.isinf(r.DCR_bending)
    assert r.is_safe is False


def test_los_dos_chequeos_del_mismo_fichero_coinciden() -> None:
    """El test mas fuerte: la respuesta correcta ya estaba escrita veinte lineas
    mas arriba. Dos funciones del mismo modulo no pueden dar veredictos opuestos
    sobre la misma magnitud."""
    simple = check_shell_buckling(ShellBucklingInput(
        D_m=BASE["D_m"], H_shell_m=BASE["H_shell_m"],
        H_liquid_m=BASE["H_liquid_m"], t_shell_mm=BASE["t_shell_mm"],
        sigma_axial_imposed_MPa=BASE["sigma_axial_imposed_MPa"], E_MPa=0.0))
    completo = check_shell_buckling_full(ShellBucklingFullInput(**BASE, E_MPa=0.0))

    assert simple.is_safe == completo.is_safe is False
    assert math.isinf(simple.DCR_axial) and math.isinf(completo.DCR_axial)
    assert math.isinf(simple.DCR_hoop) and math.isinf(completo.DCR_hoop)


def test_el_dcr_axial_individual_no_miente_aunque_la_interaccion_salve() -> None:
    """Con alpha_imperfection = 0 solo se anula la capacidad AXIAL.

    Antes `is_safe` ya salia False (lo rescataba el termino de interaccion a
    traves de la flexion), asi que el veredicto global tapaba el problema. Pero
    `DCR_axial` valia 0.0: quien leyera la tabla veia el modo axial holgado.
    """
    r = check_shell_buckling_full(ShellBucklingFullInput(**BASE, alpha_imperfection=0.0))
    assert r.Fbi_axial_MPa == 0.0
    assert math.isinf(r.DCR_axial), "el DCR axial individual seguia siendo 0.0"
    assert r.is_safe is False


def test_espesor_negativo_falla_diciendo_que_pasa() -> None:
    """Medido: el espesor negativo NO producia un aprobado silencioso.

    Producia `TypeError: '>' not supported between instances of 'complex' and
    'int'`, porque `(t/R)**1.5` con base negativa devuelve un complejo. Es un
    fallo ruidoso -- no es de la familia que persigue este fichero -- pero no
    dice nada del problema y aparece cincuenta lineas mas abajo del sitio donde
    se arregla. Ahora se rechaza en la entrada y con motivo.
    """
    with pytest.raises(ValueError, match="t_shell_mm"):
        check_shell_buckling_full(ShellBucklingFullInput(**{**BASE, "t_shell_mm": -8.0}))
    with pytest.raises(ValueError, match="D_m"):
        check_shell_buckling_full(ShellBucklingFullInput(**{**BASE, "D_m": 0.0}))


def test_el_caso_normal_no_cambia() -> None:
    """Control: con capacidades positivas nada de lo anterior interfiere."""
    r = check_shell_buckling_full(ShellBucklingFullInput(**BASE))
    assert r.Fbi_axial_MPa > 0.0
    assert 0.0 < r.DCR_axial < 1.0
    assert math.isfinite(r.DCR_interaction)


# ---------------------------------------------------------------------------
# 2. La brecha de Rotter, visible en la salida
# ---------------------------------------------------------------------------
def test_el_dcr_por_la_ruta_de_rotter_se_publica() -> None:
    """`Fbi_diamond` se calculaba y se serializaba, pero no habia forma de saber
    que DCR implicaba sin recalcularlo a mano."""
    r = check_shell_buckling_full(ShellBucklingFullInput(**BASE))
    esperado = r.sigma_axial_demand_MPa / r.Fbi_diamond_MPa
    assert r.DCR_axial_diamond == pytest.approx(esperado)
    assert "DCR_axial_diamond" in r.to_dict()


def test_el_veredicto_declara_por_que_ruta_va() -> None:
    """Publicar dos capacidades y un solo veredicto sin decir cual gobierna es
    lo que hacia invisible un factor de 8."""
    r = check_shell_buckling_full(ShellBucklingFullInput(**BASE))
    assert r.axial_basis == "API650_alpha_imperfection"
    assert "axial_basis" in r.to_dict()


@pytest.mark.parametrize(
    ("D_m", "t_mm", "ratio_esperado"),
    [(20.0, 8.0, 4.35), (30.0, 6.0, 8.10), (12.0, 10.0, 2.40)],
)
def test_la_brecha_crece_con_la_esbeltez(D_m: float, t_mm: float,
                                         ratio_esperado: float) -> None:
    """Forma cerrada: Fbi_axial/Fbi_diamond = alpha/(1/(1+0.005 R/t))
                                            = 0.6 (1 + 0.005 R/t)

    No es una constante: va de 2.4x a 8.1x en el rango de tanques corrientes, y
    sigue subiendo con R/t. Cualquier cifra unica que se cite ("7x") es el valor
    en un punto, no la brecha.
    """
    r = check_shell_buckling_full(ShellBucklingFullInput(
        D_m=D_m, H_shell_m=12.0, H_liquid_m=11.0, t_shell_mm=t_mm,
        sigma_axial_imposed_MPa=5.0))
    medido = r.Fbi_axial_MPa / r.Fbi_diamond_MPa
    forma_cerrada = 0.6 * (1.0 + 0.005 * (D_m * 1000.0 / 2.0) / t_mm)
    assert medido == pytest.approx(forma_cerrada)
    assert medido == pytest.approx(ratio_esperado, abs=0.01)
    assert r.DCR_axial_diamond == pytest.approx(r.DCR_axial * medido)
