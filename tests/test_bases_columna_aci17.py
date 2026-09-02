"""Anclajes a traccion en ``bases_columna``: modos de fallo del HORMIGON (ACI 318-19 Cap. 17).

DEFECTO QUE ATACAN ESTOS TESTS
------------------------------
``cap_anchor`` calculaba SOLO la fluencia del acero de los pernos
(``n/2 * A_perno * fyb``). No existia ningun modo de fallo del hormigon, luego
``anchors_ok`` podia salir ``True`` con un anclaje que arranca el cono de
hormigon mucho antes de que el acero fluya -- el modo gobernante en la mayoria
de bases reales con embebido corto o cerca de un borde.

UNIDADES -- EL PUNTO CRITICO DE ESTE FICHERO
--------------------------------------------
ACI 318-19 da ``k_c`` en DOS sistemas de unidades distintos:

    pulgada-libra (lb, psi, in):  k_c = 24 (coladero) / 17 (post-instalado)
    SI            (N, mm, MPa):   k_c = 10 (coladero) /  7 (post-instalado)

Conversion directa de la forma pulgada-libra a SI, para comprobar que 24 -> 10:

    N_b[lb] = 24 * sqrt(f'c[psi]) * h_ef[in]^1.5
    f'c[psi]   = 145.038 * f'c[MPa]      -> sqrt() aporta 12.043
    h_ef[in]   = h_ef[mm] / 25.4         -> ()^1.5 aporta 1/25.4^1.5 = 1/128.0
    1 lb       = 4.448 N

    k_c,SI = 24 * 12.043 * 4.448 / 128.0 = 10.04  ->  k_c = 10  (SI)

Este modulo trabaja en N/mm/MPa, luego USA k_c = 10. Usar 24 en SI multiplica
la resistencia del cono por 2.4 y es exactamente la clase de error que esta
campana persigue.

GOLDEN vs CARACTERIZACION
-------------------------
Todos los ``test_golden_*`` de este fichero aseveran numeros derivados A MANO en
el docstring del propio test a partir de la ecuacion de ACI 318-19 citada.
No hay valores capturados de la implementacion.
"""
from __future__ import annotations

import math

import pytest

from industrialjm.bases_columna import (
    BaseColumnaInput,
    Nb_kN,
    ANc_mm2,
    ANco_mm2,
    KC_CAST_IN_SI,
    STATUS_NO_VERIFICADO,
    STATUS_VERIFICADO,
    disenar_base,
    psi_ed_N,
)


# --------------------------------------------------------------------------
# Entradas comunes. La geometria del anclaje (h_ef, ca1, ca2, s, A_brg) es
# ENTRADA DEL TEST, no un valor "tipico" del modulo.
# --------------------------------------------------------------------------
def _inp(**kw) -> BaseColumnaInput:
    base = dict(
        P_kN=600.0,
        V_kN=0.0,
        M_kNm=135.0,     # produce Tu = 150 kN (ver test_tu_positivo_en_el_caso_base)
        bf_mm=200.0,
        d_mm=300.0,
        fc_MPa=25.0,
        fyb_MPa=420.0,
        n_anchors=4,
        db_anchor_mm=25.0,
        mu_friction=0.40,
        code="US",
    )
    base.update(kw)
    return BaseColumnaInput(**base)


def _geom(**kw) -> dict:
    g = dict(
        hef_mm=300.0,
        ca1_mm=1000.0,
        ca2_mm=1000.0,
        s_anchor_mm=300.0,
        Abrg_mm2=2000.0,
        cracked_concrete=True,
        cast_in=True,
    )
    g.update(kw)
    return g


def test_tu_positivo_en_el_caso_base():
    """Pre-condicion de los demas tests: el caso base SI tiene traccion de anclaje.

    Sin ella los modos del hormigon no tendrian demanda contra la que comparar y
    los tests no discriminarian nada.
    """
    res = disenar_base(_inp(**_geom()))
    assert res.Tu_anchor_kN is not None and res.Tu_anchor_kN > 0.0


# --------------------------------------------------------------------------
# 1. GOLDEN -- ACI 318-19 Eq. 17.6.2.1.4 : A_Nco = 9 * h_ef^2
# --------------------------------------------------------------------------
def test_golden_ANco_es_nueve_hef_cuadrado():
    """ACI 318-19 §17.6.2.1.4:  A_Nco = 9 * h_ef^2.

    Derivacion a mano con h_ef = 300 mm:
        A_Nco = 9 * 300^2 = 9 * 90000 = 810000 mm^2
    """
    assert ANco_mm2(300.0) == pytest.approx(810000.0)
    # Un segundo punto para fijar el EXPONENTE, no solo el coeficiente:
    #   9 * 150^2 = 9 * 22500 = 202500 mm^2
    assert ANco_mm2(150.0) == pytest.approx(202500.0)


# --------------------------------------------------------------------------
# 2. GOLDEN -- ACI 318-19 Eq. 17.6.2.2.1 : N_b = k_c * lambda_a * sqrt(f'c) * h_ef^1.5
# --------------------------------------------------------------------------
def test_golden_Nb_cast_in_cracked_SI():
    """ACI 318-19 §17.6.2.2.1:  N_b = k_c * lambda_a * sqrt(f'c) * h_ef^1.5

    Unidades SI (N, mm, MPa) -> k_c = 10 para anclajes coladeros (cast-in).
    (El 24 del enunciado es el valor en pulgada-libra; ver docstring del modulo.)

    Derivacion a mano con f'c = 25 MPa, h_ef = 300 mm, lambda_a = 1.0:
        sqrt(25)     = 5
        300^1.5      = 300 * sqrt(300) = 300 * 17.3205080757 = 5196.1524227
        N_b = 10 * 1.0 * 5 * 5196.1524227 = 259807.62114 N = 259.80762 kN
    """
    assert KC_CAST_IN_SI == 10.0
    assert Nb_kN(fc_MPa=25.0, hef_mm=300.0, cast_in=True, lambda_a=1.0) == pytest.approx(
        259.8076211353, rel=1e-9
    )


def test_golden_Nb_post_instalado_es_siete_en_SI():
    """ACI 318-19 §17.6.2.2.1: k_c = 7 para post-instalados en SI (17 en pulgada-libra).

    Derivacion a mano, mismos f'c y h_ef:
        N_b = 7 * 1.0 * 5 * 5196.1524227 = 181865.33 N = 181.86533 kN
    """
    assert Nb_kN(fc_MPa=25.0, hef_mm=300.0, cast_in=False, lambda_a=1.0) == pytest.approx(
        181.8653347947, rel=1e-9
    )


def test_golden_Nb_escala_con_hef_a_la_uno_coma_cinco():
    """El exponente 1.5 fijado por relacion cerrada: duplicar h_ef multiplica por 2^1.5.

    N_b(600) / N_b(300) = (600/300)^1.5 = 2^1.5 = 2.8284271247
    """
    r = Nb_kN(25.0, 600.0) / Nb_kN(25.0, 300.0)
    assert r == pytest.approx(2.0 ** 1.5, rel=1e-12)


# --------------------------------------------------------------------------
# 3. GOLDEN -- ACI 318-19 §17.6.2.4 : Psi_ed,N
# --------------------------------------------------------------------------
def test_golden_psi_ed_N():
    """ACI 318-19 §17.6.2.4:
        c_a,min >= 1.5 h_ef  ->  Psi_ed,N = 1.0                       (17.6.2.4.1a)
        c_a,min <  1.5 h_ef  ->  Psi_ed,N = 0.7 + 0.3*c_a,min/(1.5 h_ef)  (17.6.2.4.1b)

    Derivacion a mano con h_ef = 300 mm  ->  1.5 h_ef = 450 mm:
        c_a,min = 1000 mm >= 450  -> 1.0
        c_a,min =  450 mm  = 450  -> 0.7 + 0.3*450/450 = 1.0      (continuidad)
        c_a,min =  200 mm <  450  -> 0.7 + 0.3*200/450 = 0.7 + 0.1333333 = 0.8333333
        c_a,min =    0 mm         -> 0.7
    """
    assert psi_ed_N(1000.0, 300.0) == pytest.approx(1.0)
    assert psi_ed_N(450.0, 300.0) == pytest.approx(1.0)
    assert psi_ed_N(200.0, 300.0) == pytest.approx(0.8333333333, rel=1e-9)
    assert psi_ed_N(0.0, 300.0) == pytest.approx(0.7)


# --------------------------------------------------------------------------
# 4. GOLDEN -- A_Nc (ACI 318-19 §17.6.2.1) y su tope n * A_Nco
# --------------------------------------------------------------------------
def test_golden_ANc_grupo_de_dos_sin_efecto_de_borde():
    """A_Nc de una fila de 2 anclajes, ambos bordes lejanos (ACI 318-19 §17.6.2.1).

    Modelo implementado (declarado en el modulo): fila de n_t anclajes paralela
    al borde proximo, a distancia ca1 de el, con ca2 a los bordes laterales.

        ancho perpendicular al borde = min(ca1, 1.5 h_ef) + 1.5 h_ef
        ancho a lo largo de la fila  = min(ca2, 1.5 h_ef) + (n_t-1)*min(s, 3 h_ef)
                                       + min(ca2, 1.5 h_ef)

    Derivacion a mano: h_ef = 300 -> 1.5 h_ef = 450, 3 h_ef = 900.
    ca1 = ca2 = 1000 mm, s = 300 mm, n_t = 2:
        W1 = min(1000,450) + 450 = 450 + 450 = 900 mm
        W2 = 450 + 1*min(300,900) + 450 = 450 + 300 + 450 = 1200 mm
        A_Nc = 900 * 1200 = 1080000 mm^2
    Tope: n_t * A_Nco = 2 * 810000 = 1620000 > 1080000, no gobierna.
    """
    assert ANc_mm2(hef_mm=300.0, ca1_mm=1000.0, ca2_mm=1000.0,
                   s_anchor_mm=300.0, n_tension=2) == pytest.approx(1080000.0)


def test_golden_ANc_topado_en_n_por_ANco():
    """A_Nc <= n_t * A_Nco (ACI 318-19 §17.6.2.1.1): conos que ya no se solapan.

    Derivacion a mano: h_ef = 300 -> 1.5h_ef = 450, 3h_ef = 900, A_Nco = 810000.
    ca1 = ca2 = 1000, s = 2000 mm (>3h_ef), n_t = 2:
        W1 = 450 + 450 = 900
        W2 = 450 + min(2000,900) + 450 = 450 + 900 + 450 = 1800
        producto = 900*1800 = 1620000 mm^2
        tope     = 2 * 810000 = 1620000 mm^2   -> coinciden exactamente
    Con s = 3000 mm el producto NO crece: sigue topado en 1620000.
    """
    assert ANc_mm2(300.0, 1000.0, 1000.0, 2000.0, 2) == pytest.approx(1620000.0)
    assert ANc_mm2(300.0, 1000.0, 1000.0, 3000.0, 2) == pytest.approx(1620000.0)


def test_golden_ANc_anclaje_unico_lejos_de_bordes_es_ANco():
    """n_t = 1 y bordes lejanos -> A_Nc = (1.5h+1.5h)^2 = 9 h_ef^2 = A_Nco.

    Derivacion: 900 * 900 = 810000 = 9*300^2. Identidad que ata A_Nc con A_Nco.
    """
    assert ANc_mm2(300.0, 1000.0, 1000.0, None, 1) == pytest.approx(ANco_mm2(300.0))


# --------------------------------------------------------------------------
# 5. GOLDEN -- N_cbg completo (ACI 318-19 Eq. 17.6.2.1b)
# --------------------------------------------------------------------------
def test_golden_Ncbg_caso_base():
    """ACI 318-19 Eq. 17.6.2.1b:
        N_cbg = (A_Nc/A_Nco) * Psi_ec,N * Psi_ed,N * Psi_c,N * Psi_cp,N * N_b

    Derivacion a mano (h_ef=300, ca1=ca2=1000, s=300, n_t=2, f'c=25, coladero,
    hormigon FISURADO):
        A_Nc/A_Nco = 1080000/810000 = 1.3333333
        Psi_ec,N   = 1.0  (grupo simetrico, resultante centrada -- HIPOTESIS declarada)
        Psi_ed,N   = 1.0  (ca_min = 1000 >= 1.5*300 = 450)
        Psi_c,N    = 1.0  (fisurado, §17.6.2.5)
        Psi_cp,N   = 1.0  (coladero, §17.6.2.6 no aplica)
        N_b        = 259.8076211 kN
        N_cbg = 1.3333333 * 259.8076211 = 346.4101615 kN
    """
    res = disenar_base(_inp(**_geom()))
    assert res.anchor_tension.concrete_breakout_kN == pytest.approx(346.4101615, rel=1e-7)


def test_golden_Ncbg_no_fisurado_sube_un_25_por_ciento():
    """ACI 318-19 §17.6.2.5: Psi_c,N = 1.25 para anclajes coladeros en hormigon NO fisurado.

    Derivacion a mano: 346.4101615 * 1.25 = 433.0127019 kN.
    """
    res = disenar_base(_inp(**_geom(cracked_concrete=False)))
    assert res.anchor_tension.concrete_breakout_kN == pytest.approx(433.0127019, rel=1e-7)


# --------------------------------------------------------------------------
# 6. GOLDEN -- Pullout y side-face blowout
# --------------------------------------------------------------------------
def test_golden_pullout_headed():
    """ACI 318-19 §17.6.3.2.2a:  N_p = 8 * A_brg * f'c   (cabeza de perno/stud)
       ACI 318-19 §17.6.3.1  :  N_pn = Psi_c,P * N_p ,  Psi_c,P = 1.0 fisurado (§17.6.3.3)

    Derivacion a mano por anclaje, A_brg = 2000 mm^2, f'c = 25 MPa:
        N_p  = 8 * 2000 * 25 = 400000 N = 400 kN
        N_pn = 1.0 * 400 = 400 kN por anclaje
    Grupo de n_t = 2 anclajes traccionados: 2 * 400 = 800 kN.
    """
    res = disenar_base(_inp(**_geom()))
    assert res.anchor_tension.pullout_kN == pytest.approx(800.0)


def test_golden_pullout_no_fisurado():
    """ACI 318-19 §17.6.3.3: Psi_c,P = 1.4 en hormigon NO fisurado.

    Derivacion: 800 * 1.4 = 1120 kN.
    """
    res = disenar_base(_inp(**_geom(cracked_concrete=False)))
    assert res.anchor_tension.pullout_kN == pytest.approx(1120.0)


def test_golden_side_face_blowout_cuando_aplica():
    """ACI 318-19 §17.6.4.1: aplica solo si h_ef > 2.5*ca1 (anclaje con cabeza).
        N_sb = 13 * ca1 * sqrt(A_brg) * lambda_a * sqrt(f'c)

    Derivacion a mano con h_ef = 600 mm, ca1 = 200 mm (600 > 2.5*200 = 500 -> APLICA),
    A_brg = 2000 mm^2, f'c = 25 MPa, ca2 = 2000 mm >= 3*ca1 = 600 (sin modificador):
        sqrt(2000) = 44.7213595
        N_sb = 13 * 200 * 44.7213595 * 1.0 * 5 = 581377.67 N = 581.37767 kN
    """
    res = disenar_base(_inp(**_geom(hef_mm=600.0, ca1_mm=200.0, ca2_mm=2000.0)))
    at = res.anchor_tension
    assert at.side_face_blowout_status == "APLICA"
    assert at.side_face_blowout_kN == pytest.approx(581.3776741, rel=1e-7)


def test_side_face_blowout_no_aplica_no_bloquea_el_veredicto():
    """h_ef <= 2.5*ca1 -> §17.6.4 NO APLICA. 'No aplica' != 'no calculado'.

    Si se colapsaran ambos a None, un anclaje completamente definido y con borde
    generoso nunca podria dar True y la salida (b) seria inutil.
    """
    res = disenar_base(_inp(**_geom()))   # hef=300, ca1=1000 -> 300 <= 2500
    at = res.anchor_tension
    assert at.side_face_blowout_status == "NO_APLICA"
    assert at.side_face_blowout_kN is None
    assert at.is_ok is not None           # el veredicto SI se emite


# --------------------------------------------------------------------------
# 7. EL MODO GOBERNANTE ES EL MINIMO
# --------------------------------------------------------------------------
def test_gobierna_el_hormigon_con_embebido_corto():
    """Embebido corto -> el cono de hormigon gobierna, por debajo del acero.

    Derivacion a mano (h_ef = 150 mm, ca1=ca2=1000, s=300, f'c=25, coladero,
    fisurado; 1.5h=225, 3h=450, A_Nco = 9*150^2 = 202500):
        N_b   = 10*1.0*5*150^1.5 = 50*1837.1173 = 91855.865 N = 91.855865 kN
        W1    = min(1000,225)+225 = 450
        W2    = 225 + min(300,450) + 225 = 750
        A_Nc  = 450*750 = 337500 ; tope 2*202500 = 405000 -> no gobierna
        N_cbg = (337500/202500) * 91.855865 = 1.6666667 * 91.855865 = 153.09311 kN
        phi_c * N_cbg = 0.70 * 153.09311 = 107.16518 kN

        acero: A = pi*25^2/4 = 490.87385 mm^2 ; n/2 = 2
               N_acero = 2*490.87385*420/1000 = 412.33403 kN
               phi_s * N_acero = 0.75 * 412.33403 = 309.25052 kN

        pullout: 2 * 8 * 2000 * 25 / 1000 = 800 kN ; 0.70*800 = 560 kN

    minimo = 107.16518 kN -> gobierna el HORMIGON (breakout).
    """
    res = disenar_base(_inp(**_geom(hef_mm=150.0)))
    at = res.anchor_tension
    assert at.governing_mode == "concrete_breakout"
    assert at.governing_capacity_kN == pytest.approx(107.1651756, rel=1e-7)


def test_gobierna_el_acero_con_embebido_largo():
    """Embebido largo -> el acero gobierna. Mismo min(), otro ganador.

    Derivacion a mano (h_ef = 600 mm, ca1=ca2=2000, s=300; 1.5h=900, 3h=1800,
    A_Nco = 9*600^2 = 3240000):
        N_b   = 10*5*600^1.5 = 50*14696.9385 = 734846.92 N = 734.84692 kN
        W1    = min(2000,900)+900 = 1800
        W2    = 900 + min(300,1800) + 900 = 2100
        A_Nc  = 1800*2100 = 3780000 ; tope 2*3240000 = 6480000 -> no gobierna
        N_cbg = (3780000/3240000)*734.84692 = 1.1666667*734.84692 = 857.32141 kN
        phi_c * N_cbg = 0.70 * 857.32141 = 600.12499 kN
        pullout: 0.70 * 800 = 560 kN
        acero  : 0.75 * 412.33403 = 309.25052 kN   <-- minimo
    """
    res = disenar_base(_inp(**_geom(hef_mm=600.0, ca1_mm=2000.0, ca2_mm=2000.0)))
    at = res.anchor_tension
    assert at.governing_mode == "steel"
    assert at.governing_capacity_kN == pytest.approx(309.2505213, rel=1e-7)


def test_la_capacidad_gobernante_es_el_minimo_de_los_modos():
    """Invariante estructural del min(): ningun modo aplicable queda por debajo.

    Detecta un max() colado o un modo excluido de la seleccion.
    """
    for hef in (150.0, 300.0, 450.0, 600.0):
        res = disenar_base(_inp(**_geom(hef_mm=hef, ca1_mm=2000.0, ca2_mm=2000.0)))
        at = res.anchor_tension
        modos = [v for v in (at.steel_capacity_design_kN,
                             at.concrete_breakout_design_kN,
                             at.pullout_design_kN,
                             at.side_face_blowout_design_kN) if v is not None]
        assert modos, f"sin modos para hef={hef}"
        assert at.governing_capacity_kN == pytest.approx(min(modos), rel=1e-12), hef


# --------------------------------------------------------------------------
# 8. INVARIANTE FISICO -- acercarse a un borde REDUCE la capacidad
# --------------------------------------------------------------------------
def test_golden_efecto_de_borde_reduce_la_capacidad():
    """Acercar el anclaje al borde reduce N_cbg via A_Nc y Psi_ed,N.

    Derivacion a mano (h_ef = 300, ca2 = 1000, s = 300; 1.5h = 450):
      ca1 = 1000:  W1 = 450+450 = 900 ; W2 = 1200 ; A_Nc = 1080000
                   A_Nc/A_Nco = 1.3333333 ; Psi_ed = 1.0
                   N_cbg = 1.3333333*259.8076211 = 346.4101615 kN
      ca1 =  200:  W1 = 200+450 = 650 ; W2 = 1200 ; A_Nc =  780000
                   A_Nc/A_Nco = 0.9629630 ; ca_min = 200 < 450
                   Psi_ed = 0.7+0.3*200/450 = 0.8333333
                   N_cbg = 0.9629630*0.8333333*259.8076211
                         = 0.8024691*259.8076211 = 208.4875972 kN
    """
    lejos = disenar_base(_inp(**_geom(ca1_mm=1000.0))).anchor_tension
    cerca = disenar_base(_inp(**_geom(ca1_mm=200.0))).anchor_tension
    assert lejos.concrete_breakout_kN == pytest.approx(346.4101615, rel=1e-7)
    assert cerca.concrete_breakout_kN == pytest.approx(208.4875972, rel=1e-7)
    assert cerca.concrete_breakout_kN < lejos.concrete_breakout_kN


def test_efecto_de_borde_es_monotono():
    """Invariante fisico: N_cbg no crece al acercar el anclaje al borde."""
    caps = [
        disenar_base(_inp(**_geom(ca1_mm=c))).anchor_tension.concrete_breakout_kN
        for c in (100.0, 200.0, 300.0, 450.0, 600.0, 1000.0, 2000.0)
    ]
    assert all(a <= b + 1e-9 for a, b in zip(caps, caps[1:])), caps


# --------------------------------------------------------------------------
# 9. EL TEST QUE SOSTIENE TODA LA DECISION DE DISENO
# --------------------------------------------------------------------------
def test_sin_geometria_los_modos_del_hormigon_salen_no_calculados():
    """Sin h_ef / ca1 / ca2 / s no se puede aplicar el Cap. 17: NO CALCULADO.

    Y entonces ``anchors_ok`` NO puede ser True, porque solo se comprobo el acero
    y el modo gobernante podria ser cualquier otro.
    """
    res = disenar_base(_inp())        # sin geometria de anclaje
    at = res.anchor_tension
    assert at.concrete_breakout_kN is None
    assert at.pullout_kN is None
    assert at.governing_capacity_kN is None
    assert at.is_ok is not True
    assert res.cumple is not True
    assert res.verification_status == STATUS_NO_VERIFICADO


def test_sin_geometria_el_resultado_dice_QUE_falta():
    """Un 'no verificado' que no nombra el dato que falta es un callejon sin salida."""
    at = disenar_base(_inp()).anchor_tension
    faltan = set(at.missing_inputs)
    assert {"hef_mm", "ca1_mm", "ca2_mm", "s_anchor_mm", "Abrg_mm2"} <= faltan, faltan


def test_geometria_parcial_tampoco_basta():
    """Dar h_ef pero no las distancias a borde sigue siendo NO CALCULADO."""
    at = disenar_base(_inp(hef_mm=300.0)).anchor_tension
    assert at.concrete_breakout_kN is None
    assert at.is_ok is not True
    assert "ca1_mm" in at.missing_inputs


def test_sin_Abrg_el_hormigon_no_esta_completo():
    """Pullout (§17.6.3) es un modo del HORMIGON: sin A_brg no hay veredicto True."""
    at = disenar_base(_inp(**_geom(Abrg_mm2=None))).anchor_tension
    assert at.concrete_breakout_kN is not None    # breakout SI se puede
    assert at.pullout_kN is None
    assert at.is_ok is not True
    assert "Abrg_mm2" in at.missing_inputs


def test_to_dict_expone_la_ausencia_al_consumidor_de_la_api():
    """La ausencia debe ser visible en to_dict(), no solo en el dataclass."""
    d = disenar_base(_inp()).to_dict()
    assert d["verification_status"] == STATUS_NO_VERIFICADO
    assert d["cumple"] is not True
    at = d["anchor_tension"]
    assert at["concrete_breakout_kN"] is None
    assert at["pullout_kN"] is None
    assert at["is_ok"] is not True
    assert at["missing_inputs"], at
    assert any("17" in n for n in d["notes"]), d["notes"]


def test_con_geometria_completa_y_suficiente_si_se_verifica():
    """La salida (b) debe seguir siendo capaz de dar True: si no, no sirve.

    h_ef = 600, bordes lejanos, A_brg dado -> todos los modos aplicables
    calculados, gobierna el acero con 309.25 kN > Tu.
    """
    res = disenar_base(_inp(**_geom(hef_mm=600.0, ca1_mm=2000.0, ca2_mm=2000.0)))
    at = res.anchor_tension
    assert at.is_ok is True
    assert res.verification_status == STATUS_VERIFICADO
    assert res.cumple is True


def test_embebido_corto_reprueba_lo_que_el_acero_solo_aprobaba():
    """EL DEFECTO, en una linea.

    Tu = 150 kN.  P = 600 kN, M = 135 kNm, d = 300 -> N = 400 mm, brazo = N-100 = 300:
        Tu = 135000/300 - 600/2 = 450 - 300 = 150 kN
    Solo acero: 412.33 kN nominal (309.25 de diseno) -> aprobaba.
    Con h_ef = 150 mm el cono de hormigon da 107.17 kN de diseno -> NO cumple.
    """
    res = disenar_base(_inp(**_geom(hef_mm=150.0)))
    assert res.Tu_anchor_kN == pytest.approx(150.0, rel=1e-9)
    assert res.anchor_tension.steel_capacity_kN == pytest.approx(412.3340278, rel=1e-7)
    assert res.anchor_tension.governing_mode == "concrete_breakout"
    assert res.anchor_tension.is_ok is False
    assert res.cumple is False


# --------------------------------------------------------------------------
# 10. Alcance declarado, no omitido en silencio
# --------------------------------------------------------------------------
def test_cortante_en_anclajes_declarado_fuera_de_alcance():
    """§17.7 (cortante en anclajes) NO se implementa: el modulo lleva TODO el
    cortante a friccion + llave. Debe declararse, no omitirse en silencio."""
    notes = " ".join(disenar_base(_inp(**_geom())).notes)
    assert "17.7" in notes


def test_la_nota_de_levantamiento_ya_no_dice_que_no_hay_capacidad_de_anclaje():
    """La rama P<=0 seguia diciendo que el modulo 'no dimensiona anclajes'.

    Con el Cap. 17 implementado eso ya solo es cierto para la DEMANDA Tu bajo
    levantamiento, no para la CAPACIDAD. La nota no debe mentir por defecto.
    """
    res = disenar_base(_inp(P_kN=-400.0, M_kNm=0.0))
    notes = " ".join(res.notes).lower()
    assert res.verification_status == STATUS_NO_VERIFICADO
    assert "demanda" in notes
    assert "17" in notes


def test_lambda_a_hormigon_ligero_reduce_la_capacidad():
    """ACI 318-19 §17.2.4 / Tabla 19.2.4.2: lambda_a < 1 reduce N_b linealmente.

    Derivacion: lambda_a = 0.75 -> N_b = 0.75 * 259.8076211 = 194.8557158 kN.
    """
    assert Nb_kN(25.0, 300.0, cast_in=True, lambda_a=0.75) == pytest.approx(
        194.8557158, rel=1e-9
    )


def test_area_perno_es_la_bruta_declarada():
    """Cordura del acero: A = pi*db^2/4 con db = 25 -> 490.8738521 mm^2."""
    assert math.pi * 25.0 ** 2 / 4.0 == pytest.approx(490.8738521, rel=1e-9)
