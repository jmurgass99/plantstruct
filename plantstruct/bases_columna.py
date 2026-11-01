"""Bases de columna - diseno placa base por Salmon & Johnson.

Considera carga axial + momento, dimensiona placa, anclajes y rigidizadores.

ANCLAJES A TRACCION -- ACI 318-19 Capitulo 17
=============================================
La capacidad a traccion de los anclajes NO es solo la fluencia del acero. ACI
318-19 exige tomar el MINIMO de los modos aplicables:

    §17.6.1  resistencia del ACERO
    §17.6.2  arrancamiento del CONO DE HORMIGON (concrete breakout, metodo CCD)
    §17.6.3  extraccion (pullout)
    §17.6.4  desprendimiento lateral (side-face blowout)

Estos modos necesitan geometria que NO estaba en la entrada del modulo: h_ef,
ca1, ca2, separacion entre pernos y area de apoyo de la cabeza A_brg. Rellenarlos
con valores "tipicos" seria fabricar seguridad sobre datos inventados, asi que
se ha elegido la salida (b):

    * son ENTRADAS OPCIONALES;
    * si faltan, los modos del hormigon se reportan como NO CALCULADO (``None``)
      y ``AnchorTensionResult.missing_inputs`` dice EXACTAMENTE cual falta;
    * en ese caso ``is_ok`` es ``None`` (nunca ``True``), ``cumple`` es ``False``
      y ``verification_status`` es ``NO_VERIFICADO``.

Se distingue NO_APLICA de NO_CALCULADO: §17.6.4 solo rige si h_ef > 2.5*ca1; que
no aplique no puede impedir un veredicto favorable.

UNIDADES -- k_c
---------------
ACI 318-19 §17.6.2.2.1 da k_c en dos sistemas:

    pulgada-libra (lb, psi, in):  k_c = 24 (coladero) / 17 (post-instalado)
    SI            (N, mm, MPa):   k_c = 10 (coladero) /  7 (post-instalado)

Comprobacion de la equivalencia (24 -> 10), convirtiendo la forma pulgada-libra:

    f'c[psi] = 145.038*f'c[MPa]  -> sqrt() aporta 12.043
    h_ef[in] = h_ef[mm]/25.4     -> ()^1.5 aporta 1/25.4^1.5 = 1/128.0
    1 lb = 4.448 N
    k_c,SI = 24 * 12.043 * 4.448 / 128.0 = 10.04  ->  10

Este modulo trabaja en N/mm/MPa: usa k_c = 10. Usar 24 aqui multiplicaria la
resistencia del cono por 2.4.

ALCANCE DECLARADO (lo que NO se implementa)
-------------------------------------------
    * §17.7 (cortante en anclajes: acero, breakout y pryout) NO se implementa.
      Este modulo lleva TODO el cortante a friccion + llave de cortante y nunca
      asigna cortante a los pernos. Si el proyectista si se lo asigna, §17.7
      queda pendiente y este modulo no lo cubre.
    * §17.8 (interaccion traccion-cortante) queda fuera por lo anterior.
    * La DEMANDA Tu bajo levantamiento neto (P <= 0) sigue sin derivarse.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt


@dataclass(frozen=True)
class BaseColumnaInput:
    """Entradas para diseño de placa base según Salmon & Johnson y AISC DG1.

    Reacciones en la base ingresadas como ENTRADA:
        P_kN: Reacción axial (+ compresión, - tracción).
        V_kN: Reacción cortante horizontal.
        M_kNm: Reacción momento flector.
    """
    P_kN: float
    V_kN: float = 0.0
    M_kNm: float = 0.0
    bf_mm: float = 200.0
    d_mm: float = 250.0
    fy_MPa: float = 250.0
    fc_MPa: float = 25.0
    fyb_MPa: float = 420.0
    n_anchors: int = 4
    db_anchor_mm: float = 25.0
    mu_friction: float = 0.40
    code: str = "US"

    # --- Geometria del anclaje para ACI 318-19 Cap. 17 (OPCIONAL) -----------
    # Si falta cualquiera de las requeridas por un modo, ese modo se reporta
    # NO CALCULADO y el anclaje NO puede darse por verificado. NO hay valores
    # "tipicos" por defecto: la ausencia se propaga como ausencia.
    hef_mm: float | None = None        # profundidad efectiva de embebido
    ca1_mm: float | None = None        # distancia al borde mas proximo
    ca2_mm: float | None = None        # distancia al borde perpendicular
    s_anchor_mm: float | None = None   # separacion entre pernos traccionados
    Abrg_mm2: float | None = None      # area de apoyo de la cabeza (§17.6.3/§17.6.4)
    cracked_concrete: bool = True      # §17.6.2.5 / §17.6.3.3
    cast_in: bool = True               # coladero (k_c=10) vs post-instalado (k_c=7)
    lambda_a: float = 1.0              # §17.2.4: 1.0 hormigon de peso normal
    futa_MPa: float | None = None
    Ase_N_mm2: float | None = None


# Dimensiones de la llave de cortante: NO se dimensionan, son constantes del
# modulo. Se exponen como tales en el resultado (``ShearLugResult.dims_source``)
# para que nadie lea la salida como si la llave se hubiera calculado.
LUG_HEIGHT_MM = 75.0     # ENTRADA FIJA
LUG_THICKNESS_MM = 25.0  # ENTRADA FIJA
LUG_DIMS_SOURCE = (
    "ENTRADA FIJA: altura 75 mm y espesor 25 mm son constantes del modulo, "
    "NO un dimensionamiento. Solo el ancho se ata a la geometria de la placa. "
    "Las capacidades reportadas verifican esa geometria supuesta; dimensionar "
    "la llave sigue siendo una decision del proyectista."
)

# Estados de verificacion del diseno de la base.
STATUS_VERIFICADO = "VERIFICADO"
STATUS_NO_VERIFICADO = "NO_VERIFICADO"

# ---------------------------------------------------------------------------
# ACI 318-19 Capitulo 17 -- coeficientes, EN UNIDADES SI (N, mm, MPa)
# ---------------------------------------------------------------------------
KC_CAST_IN_SI = 10.0          # §17.6.2.2.1, coladero      (24 en pulgada-libra)
KC_POST_INSTALLED_SI = 7.0    # §17.6.2.2.1, post-instalado (17 en pulgada-libra)
PSI_C_N_UNCRACKED_CAST_IN = 1.25   # §17.6.2.5, coladero en hormigon no fisurado
PSI_C_P_UNCRACKED = 1.4            # §17.6.3.3, pullout en hormigon no fisurado
NP_HEAD_COEFF = 8.0                # §17.6.3.2.2a: N_p = 8*A_brg*f'c
NSB_COEFF_SI = 13.0                # §17.6.4.1: N_sb = 13*ca1*sqrt(A_brg)*lam*sqrt(f'c)
                                   #            (160 en pulgada-libra)

# Factores de reduccion. ENTRADA FIJA del modulo, NO verificada linea a linea
# contra la Tabla 17.5.3 impresa de ACI 318-19: se toman los valores de la
# condicion SIN armadura suplementaria (la desfavorable). El proyectista debe
# confirmarlos. Los goldens del modulo aseveran capacidades NOMINALES, que no
# dependen de estos factores.
PHI_STEEL_TENSION = 0.75      # §17.5.3, acero ductil a traccion
PHI_CONCRETE_TENSION = 0.70   # §17.5.3, modos de hormigon, Condicion B
PHI_SOURCE = (
    "ENTRADA FIJA: phi_acero = 0.75 y phi_hormigon = 0.70 (condicion sin "
    "armadura suplementaria). NO verificados contra la Tabla 17.5.3 impresa de "
    "ACI 318-19; las capacidades NOMINALES reportadas no dependen de ellos."
)

MODE_STEEL = "steel"
MODE_BREAKOUT = "concrete_breakout"
MODE_PULLOUT = "pullout"
MODE_BLOWOUT = "side_face_blowout"
MODE_NO_DEMAND = "sin_demanda_de_traccion"

CALC_APLICA = "APLICA"
CALC_NO_APLICA = "NO_APLICA"
CALC_NO_CALCULADO = "NO_CALCULADO"


def ANco_mm2(hef_mm: float) -> float:
    """ACI 318-19 §17.6.2.1.4: area proyectada de UN anclaje sin bordes.

        A_Nco = 9 * h_ef^2

    Con h_ef = 300 mm:  9 * 300^2 = 810000 mm^2.
    """
    return 9.0 * hef_mm * hef_mm


def Nb_kN(fc_MPa: float, hef_mm: float, cast_in: bool = True,
          lambda_a: float = 1.0) -> float:
    futa_MPa: float | None = None
    Ase_N_mm2: float | None = None
    """ACI 318-19 §17.6.2.2.1: resistencia basica al arrancamiento del cono.

        N_b = k_c * lambda_a * sqrt(f'c) * h_ef^1.5      [N, mm, MPa]

    k_c = 10 (coladero) / 7 (post-instalado) en SI. Ver el docstring del modulo
    para la conversion que demuestra que el 24 tabulado es pulgada-libra.

    Derivacion con k_c=10, f'c=25 MPa, h_ef=300 mm, lambda_a=1.0:
        sqrt(25) = 5 ;  300^1.5 = 300*17.3205080757 = 5196.1524227
        N_b = 10 * 1.0 * 5 * 5196.1524227 = 259807.62114 N = 259.80762 kN
    """
    kc = KC_CAST_IN_SI if cast_in else KC_POST_INSTALLED_SI
    return kc * lambda_a * sqrt(fc_MPa) * hef_mm ** 1.5 / 1000.0


def psi_ed_N(ca_min_mm: float, hef_mm: float) -> float:
    """ACI 318-19 §17.6.2.4: modificador por proximidad de borde.

        c_a,min >= 1.5 h_ef  ->  1.0                                 (17.6.2.4.1a)
        c_a,min <  1.5 h_ef  ->  0.7 + 0.3 * c_a,min / (1.5 h_ef)    (17.6.2.4.1b)
    """
    lim = 1.5 * hef_mm
    if ca_min_mm >= lim:
        return 1.0
    return 0.7 + 0.3 * ca_min_mm / lim


def ANc_mm2(hef_mm: float, ca1_mm: float, ca2_mm: float,
            s_anchor_mm: float | None, n_tension: int) -> float:
    """ACI 318-19 §17.6.2.1: area proyectada del grupo traccionado.

    MODELO GEOMETRICO IMPLEMENTADO (hipotesis declarada, no una generalidad):
    una unica FILA de ``n_tension`` anclajes, paralela al borde proximo, a
    distancia ``ca1`` de el, con ``ca2`` a los bordes laterales y separacion
    uniforme ``s``. Es la geometria que el modulo ya presuponia al usar n/2
    pernos traccionados. Patrones arbitrarios NO estan cubiertos.

        W1 (perpendicular al borde) = min(ca1, 1.5 h_ef) + 1.5 h_ef
        W2 (a lo largo de la fila)  = min(ca2, 1.5 h_ef)
                                      + (n_t - 1) * min(s, 3 h_ef)
                                      + min(ca2, 1.5 h_ef)
        A_Nc = min(W1 * W2, n_t * A_Nco)          (tope de §17.6.2.1.1)

    El lado interior (opuesto al borde ca1) se toma como 1.5 h_ef completos:
    HIPOTESIS de que ese borde esta a mas de 1.5 h_ef. Si no lo esta, el
    resultado queda del lado INSEGURO y el modelo no aplica.
    """
    lim = 1.5 * hef_mm
    w1 = min(ca1_mm, lim) + lim
    gap = 0.0
    if n_tension > 1:
        if s_anchor_mm is None:
            raise ValueError("s_anchor_mm requerido para n_tension > 1")
        gap = (n_tension - 1) * min(s_anchor_mm, 3.0 * hef_mm)
    w2 = min(ca2_mm, lim) + gap + min(ca2_mm, lim)
    return min(w1 * w2, n_tension * ANco_mm2(hef_mm))


@dataclass(frozen=True)
class AnchorTensionResult:
    """Anclajes a traccion: TODOS los modos de ACI 318-19 §17.6, no solo el acero.

    ``None`` significa NO CALCULADO (falta un dato de entrada) salvo cuando el
    ``*_status`` asociado dice ``NO_APLICA``. Las capacidades ``*_kN`` son
    NOMINALES; las ``*_design_kN`` llevan el phi correspondiente.
    """
    Tu_kN: float | None
    steel_capacity_kN: float | None
    steel_capacity_design_kN: float | None
    concrete_breakout_kN: float | None
    concrete_breakout_design_kN: float | None
    concrete_breakout_status: str
    pullout_kN: float | None
    pullout_design_kN: float | None
    pullout_status: str
    side_face_blowout_kN: float | None
    side_face_blowout_design_kN: float | None
    side_face_blowout_status: str
    governing_mode: str | None
    governing_capacity_kN: float | None
    is_ok: bool | None
    missing_inputs: tuple[str, ...]
    notes: tuple[str, ...]
    phi_source: str = PHI_SOURCE

    def to_dict(self) -> dict:
        return {
            "Tu_kN": _round_or_none(self.Tu_kN, 2),
            "steel_capacity_kN": _round_or_none(self.steel_capacity_kN, 2),
            "steel_capacity_design_kN": _round_or_none(self.steel_capacity_design_kN, 2),
            "concrete_breakout_kN": _round_or_none(self.concrete_breakout_kN, 2),
            "concrete_breakout_design_kN": _round_or_none(
                self.concrete_breakout_design_kN, 2),
            "concrete_breakout_status": self.concrete_breakout_status,
            "pullout_kN": _round_or_none(self.pullout_kN, 2),
            "pullout_design_kN": _round_or_none(self.pullout_design_kN, 2),
            "pullout_status": self.pullout_status,
            "side_face_blowout_kN": _round_or_none(self.side_face_blowout_kN, 2),
            "side_face_blowout_design_kN": _round_or_none(
                self.side_face_blowout_design_kN, 2),
            "side_face_blowout_status": self.side_face_blowout_status,
            "governing_mode": self.governing_mode,
            "governing_capacity_kN": _round_or_none(self.governing_capacity_kN, 2),
            "is_ok": self.is_ok,
            "missing_inputs": list(self.missing_inputs),
            "notes": list(self.notes),
            "phi_source": self.phi_source,
        }


def _comprobar_anclajes_traccion(inp: "BaseColumnaInput",
                                 Tu_kN: float) -> AnchorTensionResult:
    """Aplica ACI 318-19 §17.6 y devuelve el modo GOBERNANTE (el minimo).

    Si falta cualquier dato requerido por un modo APLICABLE, ese modo sale
    ``None``/``NO_CALCULADO`` y ``is_ok`` es ``None``: nunca ``True``.
    """
    notes: list[str] = []
    missing: list[str] = []

    n_t = max(int(inp.n_anchors) // 2, 1)

    # ---- §17.6.1 ACERO ----------------------------------------------------
    # El modulo usa fluencia sobre area BRUTA: N = n_t * (pi*db^2/4) * fyb.
    # ACI 318-19 §17.6.1.2 usa N_sa = A_se,N * f_uta (ULTIMA sobre area
    # resistente a traccion, con f_uta <= min(1.9 f_ya, 860 MPa)). Son formulas
    # DISTINTAS y este modulo no recibe f_uta ni A_se,N: no se inventan. NO se
    # ha verificado en que direccion difieren -- depende del grado y del area
    # de rosca -- asi que no se afirma que la formula del modulo sea conservadora.
    A_bolt = pi * inp.db_anchor_mm ** 2 / 4.0
    if inp.futa_MPa is not None and inp.Ase_N_mm2 is not None:
        futa_eff = min(inp.futa_MPa, 1.9 * inp.fyb_MPa, 860.0)
        steel_kN = n_t * inp.Ase_N_mm2 * futa_eff / 1000.0
    else:
        steel_kN = n_t * A_bolt * inp.fyb_MPa / 1000.0
    steel_design = PHI_STEEL_TENSION * steel_kN
    notes.append(
        "Acero (§17.6.1): capacidad calculada como fluencia sobre area bruta "
        "(n/2 * pi*db^2/4 * fyb), NO como N_sa = A_se,N * f_uta de §17.6.1.2. "
        "El modulo no recibe f_uta ni A_se,N y no se inventan; la direccion de "
        "la diferencia NO esta verificada."
    )

    # ---- Datos geometricos disponibles -----------------------------------
    hef, ca1, ca2 = inp.hef_mm, inp.ca1_mm, inp.ca2_mm
    s, abrg = inp.s_anchor_mm, inp.Abrg_mm2
    for nombre, valor in (("hef_mm", hef), ("ca1_mm", ca1), ("ca2_mm", ca2)):
        if valor is None:
            missing.append(nombre)
    if n_t > 1 and s is None:
        missing.append("s_anchor_mm")
    if abrg is None:
        missing.append("Abrg_mm2")

    # ---- §17.6.2 ARRANCAMIENTO DEL CONO ----------------------------------
    breakout_kN: float | None = None
    breakout_status = CALC_NO_CALCULADO
    if hef is not None and ca1 is not None and ca2 is not None and (
            n_t == 1 or s is not None):
        Nb = Nb_kN(inp.fc_MPa, hef, cast_in=inp.cast_in, lambda_a=inp.lambda_a)
        A_Nc = ANc_mm2(hef, ca1, ca2, s, n_t)
        A_Nco = ANco_mm2(hef)
        # §17.6.2.3 Psi_ec,N: HIPOTESIS = 1.0. Grupo simetrico con la resultante
        # de traccion centrada en la fila traccionada (e'_N = 0). Es la geometria
        # declarada en ANc_mm2; con un reparto asimetrico NO seria 1.0.
        psi_ec = 1.0
        psi_ed = psi_ed_N(min(ca1, ca2), hef)
        # §17.6.2.5
        psi_c = 1.0 if inp.cracked_concrete else (
            PSI_C_N_UNCRACKED_CAST_IN if inp.cast_in else 1.0)
        # §17.6.2.6 Psi_cp,N: solo rige para POST-INSTALADOS en hormigon no
        # fisurado sin armadura suplementaria, y necesita c_ac, que el modulo no
        # recibe. Para coladeros es 1.0 POR REGLA (no por hipotesis).
        psi_cp = 1.0
        if not inp.cast_in and not inp.cracked_concrete:
            notes.append(
                "§17.6.2.6: Psi_cp,N se ha tomado 1.0 para un anclaje "
                "POST-INSTALADO en hormigon no fisurado. Eso solo es correcto si "
                "c_a,min >= c_ac; el modulo no recibe c_ac. Puede ser INSEGURO."
            )
        breakout_kN = (A_Nc / A_Nco) * psi_ec * psi_ed * psi_c * psi_cp * Nb
        breakout_status = CALC_APLICA
        notes.append(
            f"§17.6.2 (CCD): A_Nc={A_Nc:.0f} mm2, A_Nco={A_Nco:.0f} mm2, "
            f"Psi_ec,N={psi_ec:.3f} (HIPOTESIS: grupo simetrico, e'_N=0), "
            f"Psi_ed,N={psi_ed:.4f}, Psi_c,N={psi_c:.2f}, Psi_cp,N={psi_cp:.2f}, "
            f"N_b={Nb:.2f} kN con k_c="
            f"{KC_CAST_IN_SI if inp.cast_in else KC_POST_INSTALLED_SI:.0f} (SI)."
        )
    else:
        notes.append(
            "§17.6.2 NO CALCULADO: falta geometria del anclaje "
            f"({', '.join(n for n in missing if n != 'Abrg_mm2') or 'n/d'}). "
            "El arrancamiento del cono de hormigon suele ser el modo GOBERNANTE."
        )

    # ---- §17.6.3 EXTRACCION (pullout) ------------------------------------
    pullout_kN: float | None = None
    pullout_status = CALC_NO_CALCULADO
    if abrg is not None:
        # §17.6.3.2.2a  N_p = 8 * A_brg * f'c   (perno/stud con cabeza)
        # §17.6.3.1     N_pn = Psi_c,P * N_p ;  §17.6.3.3 Psi_c,P = 1.0 / 1.4
        psi_cp_pull = 1.0 if inp.cracked_concrete else PSI_C_P_UNCRACKED
        pullout_kN = n_t * psi_cp_pull * NP_HEAD_COEFF * abrg * inp.fc_MPa / 1000.0
        pullout_status = CALC_APLICA
    else:
        notes.append(
            "§17.6.3 (extraccion) NO CALCULADO: falta A_brg, el area de apoyo de "
            "la cabeza del perno. Es un modo del HORMIGON, no del acero."
        )

    # ---- §17.6.4 DESPRENDIMIENTO LATERAL (side-face blowout) -------------
    blowout_kN: float | None = None
    blowout_status = CALC_NO_CALCULADO
    if hef is not None and ca1 is not None:
        if hef <= 2.5 * ca1:
            # §17.6.4.1: el modo solo rige si h_ef > 2.5*ca1. NO APLICA != NO CALCULADO.
            blowout_status = CALC_NO_APLICA
        elif abrg is None:
            notes.append(
                "§17.6.4 APLICA (h_ef > 2.5*ca1) pero NO SE PUEDE CALCULAR: falta A_brg."
            )
        else:
            # N_sb = 13 * ca1 * sqrt(A_brg) * lambda_a * sqrt(f'c)   [N, mm, MPa]
            nsb = (NSB_COEFF_SI * ca1 * sqrt(abrg) * inp.lambda_a
                   * sqrt(inp.fc_MPa) / 1000.0)
            if ca2 is not None and ca2 < 3.0 * ca1:
                # §17.6.4.1: si ca2 < 3*ca1 se multiplica por (1 + ca2/ca1)/4
                nsb *= (1.0 + ca2 / ca1) / 4.0
            blowout_kN = nsb
            blowout_status = CALC_APLICA

    designs: dict[str, float] = {}
    incompletos: list[str] = []
    designs[MODE_STEEL] = steel_design
    breakout_design = None if breakout_kN is None else PHI_CONCRETE_TENSION * breakout_kN
    pullout_design = None if pullout_kN is None else PHI_CONCRETE_TENSION * pullout_kN
    blowout_design = None if blowout_kN is None else PHI_CONCRETE_TENSION * blowout_kN
    for modo, val, status in ((MODE_BREAKOUT, breakout_design, breakout_status),
                              (MODE_PULLOUT, pullout_design, pullout_status),
                              (MODE_BLOWOUT, blowout_design, blowout_status)):
        if status == CALC_NO_APLICA:
            continue
        if val is None:
            incompletos.append(modo)
        else:
            designs[modo] = val

    # ---- Veredicto --------------------------------------------------------
    if Tu_kN <= 0.0:
        # Sin demanda de traccion no hay modo de fallo a traccion que comprobar.
        # NO es una via para aprobar sin comprobar el hormigon: se declara.
        gov_mode: str | None = MODE_NO_DEMAND
        gov_cap: float | None = None
        is_ok: bool | None = True
        notes.append(
            "Tu = 0 kN: los anclajes no reciben traccion en esta combinacion, "
            "luego §17.6 no tiene demanda contra la que comprobarse. El veredicto "
            "NO significa que la capacidad del hormigon se haya calculado."
        )
    elif incompletos:
        gov_mode = None
        gov_cap = None
        is_ok = None
        notes.append(
            "NO VERIFICADO: modos de HORMIGON sin calcular ("
            + ", ".join(incompletos)
            + "). Solo se ha comprobado el ACERO (§17.6.1); el modo gobernante "
              "podria ser cualquiera de los del hormigon y ser mucho menor. "
              "Suministre: " + ", ".join(missing) + "."
        )
    else:
        gov_mode = min(designs, key=lambda k: designs[k])
        gov_cap = designs[gov_mode]
        is_ok = Tu_kN <= gov_cap
        notes.append(
            f"Modo gobernante a traccion: {gov_mode} con "
            f"{gov_cap:.2f} kN de diseno frente a Tu = {Tu_kN:.2f} kN."
        )

    notes.append(
        "ALCANCE: §17.7 (cortante en anclajes: acero, breakout y pryout) y §17.8 "
        "(interaccion traccion-cortante) NO se comprueban. Este modulo lleva todo "
        "el cortante a friccion + llave de cortante y no asigna cortante a los pernos."
    )

    return AnchorTensionResult(
        Tu_kN=Tu_kN,
        steel_capacity_kN=steel_kN,
        steel_capacity_design_kN=steel_design,
        concrete_breakout_kN=breakout_kN,
        concrete_breakout_design_kN=breakout_design,
        concrete_breakout_status=breakout_status,
        pullout_kN=pullout_kN,
        pullout_design_kN=pullout_design,
        pullout_status=pullout_status,
        side_face_blowout_kN=blowout_kN,
        side_face_blowout_design_kN=blowout_design,
        side_face_blowout_status=blowout_status,
        governing_mode=gov_mode,
        governing_capacity_kN=gov_cap,
        is_ok=is_ok,
        missing_inputs=tuple(missing),
        notes=tuple(notes),
    )


@dataclass(frozen=True)
class ShearLugResult:
    """Resultado de la comprobacion de la llave de cortante (shear lug).

    Las dimensiones NO se dimensionan (ver ``dims_source``): la altura y el
    espesor son constantes del modulo.
    """
    required: bool
    shear_demand_kN: float
    shear_friction_capacity_kN: float
    lug_width_mm: float | None
    lug_height_mm: float | None
    lug_thickness_mm: float | None
    bearing_capacity_kN: float | None
    shear_capacity_kN: float | None
    is_ok: bool | None
    dims_source: str = LUG_DIMS_SOURCE


def _round_or_none(x: float | None, n: int) -> float | None:
    return None if x is None else round(x, n)


@dataclass(frozen=True)
class BaseColumnaResult:
    """Resultado del diseno de la base.

    Los campos geometricos y de demanda son ``None`` cuando el estado de carga
    no permite calcularlos (p. ej. traccion neta): la ausencia se propaga como
    ausencia, nunca como un numero por defecto. En ese caso
    ``verification_status`` vale ``"NO_VERIFICADO"`` y ``cumple`` es ``False``.
    """
    N_mm: float | None
    B_mm: float | None
    t_mm: float | None
    Tu_anchor_kN: float | None
    e_mm: float | None
    shear_lug: ShearLugResult
    anchor_tension: AnchorTensionResult
    reactions: dict
    cumple: bool
    code: str
    verification_status: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "N_mm": _round_or_none(self.N_mm, 1),
            "B_mm": _round_or_none(self.B_mm, 1),
            "t_mm": _round_or_none(self.t_mm, 1),
            "Tu_anchor_kN": _round_or_none(self.Tu_anchor_kN, 2),
            "e_mm": _round_or_none(self.e_mm, 1),
            "shear_lug": {
                "required": self.shear_lug.required,
                "shear_demand_kN": self.shear_lug.shear_demand_kN,
                "shear_friction_capacity_kN": self.shear_lug.shear_friction_capacity_kN,
                "lug_width_mm": self.shear_lug.lug_width_mm,
                "lug_height_mm": self.shear_lug.lug_height_mm,
                "lug_thickness_mm": self.shear_lug.lug_thickness_mm,
                "bearing_capacity_kN": _round_or_none(
                    self.shear_lug.bearing_capacity_kN, 2),
                # shear_capacity_kN faltaba en esta serializacion: un campo
                # calculado que el consumidor de la API no llegaba a ver.
                "shear_capacity_kN": _round_or_none(
                    self.shear_lug.shear_capacity_kN, 2),
                "is_ok": self.shear_lug.is_ok,
                "dims_source": self.shear_lug.dims_source,
            },
            "anchor_tension": self.anchor_tension.to_dict(),
            "reactions": self.reactions,
            "cumple": self.cumple,
            "verification_status": self.verification_status,
            "notes": list(self.notes),
            "code": self.code,
        }


def disenar_base(inp: BaseColumnaInput) -> BaseColumnaResult:
    """Diseña placa base, pernos y llave de cortante según Salmon & Johnson (1996) / AISC Design Guide 1."""
    if inp.code not in {"EU", "AU", "SG", "US", "CO"}:
        raise ValueError(f"code invalido: {inp.code}")
    phi_c = 0.65 if inp.code in ("US", "CO") else 0.60
    phi_b = 0.90
    phi_v = 0.75

    fp_max = phi_c * 0.85 * inp.fc_MPa

    # Traccion neta (levantamiento) o axil nulo: estado de carga REAL y distinto,
    # no un caso degenerado de compresion. No hay area de aplastamiento que
    # dimensione la placa ni fuerza normal que genere friccion, y este modulo NO
    # dimensiona anclajes a levantamiento. Se devuelve NO VERIFICADO.
    if inp.P_kN <= 0.0:
        return _resultado_levantamiento(inp)

    # Dimensiones mínimas en planta según carga axial P (compresion)
    P_comp = inp.P_kN
    A_req = P_comp * 1000.0 / fp_max
    side = sqrt(A_req)
    N = max(side, inp.d_mm + 100.0)
    B = max(side, inp.bf_mm + 100.0)
    e_mm = abs(inp.M_kNm) * 1000.0 / P_comp

    # Caso pequeña vs gran excentricidad (Salmon & Johnson §14)
    if e_mm <= N / 6.0:
        fp = (P_comp * 1000.0 / (N * B)) + (6.0 * abs(inp.M_kNm) * 1e6 / (B * (N ** 2)))
        m = (N - 0.95 * inp.d_mm) / 2.0
        n = (B - 0.80 * inp.bf_mm) / 2.0
        l_crit = max(m, n, 1.0)
        t = l_crit * sqrt(2.0 * fp / (0.90 * inp.fy_MPa))
        Tu = 0.0
    else:
        # Gran excentricidad - tensión en anclajes
        lever_arm = max(N - 100.0, 50.0)
        Tu = max(abs(inp.M_kNm) * 1000.0 / lever_arm - P_comp / 2.0, 0.0)
        m = (N - 0.95 * inp.d_mm) / 2.0
        n = (B - 0.80 * inp.bf_mm) / 2.0
        l_crit = max(m, n, 1.0)
        t = l_crit * sqrt(2.0 * fp_max / (0.90 * inp.fy_MPa))

    # Capacidad de los anclajes a traccion: TODOS los modos de ACI 318-19 §17.6,
    # no solo la fluencia del acero. ``is_ok`` es None (nunca True) si falta
    # geometria para los modos del hormigon.
    anchor_tension = _comprobar_anclajes_traccion(inp, Tu)
    anchors_ok = anchor_tension.is_ok

    # Llave de cortante (Shear Lug) - AISC Design Guide 1 / Salmon & Johnson
    V_demand = abs(inp.V_kN)
    V_friction = inp.mu_friction * P_comp
    lug_req = V_demand > V_friction

    lug_w = min(B - 100.0, inp.bf_mm)
    # lug_h / lug_t: ENTRADA FIJA del modulo, no dimensionamiento (ver LUG_DIMS_SOURCE).
    lug_h = LUG_HEIGHT_MM
    lug_t = LUG_THICKNESS_MM
    # Capacidad por aplastamiento del hormigón contra el shear lug: φ_c · 0.85 · f'c · (w · h)
    A_bearing_lug = lug_w * lug_h
    lug_bearing_cap = (phi_c * 0.85 * inp.fc_MPa * A_bearing_lug) / 1000.0
    lug_shear_cap = (phi_v * 0.60 * inp.fy_MPa * (lug_w * lug_t)) / 1000.0

    if lug_req:
        lug_ok = (lug_bearing_cap >= V_demand) and (lug_shear_cap >= V_demand)
        shear_lug_res = ShearLugResult(
            required=True,
            shear_demand_kN=V_demand,
            shear_friction_capacity_kN=V_friction,
            lug_width_mm=lug_w,
            lug_height_mm=lug_h,
            lug_thickness_mm=lug_t,
            bearing_capacity_kN=lug_bearing_cap,
            shear_capacity_kN=lug_shear_cap,
            is_ok=lug_ok,
        )
    else:
        # Sin llave: no hay geometria ni capacidad de llave que reportar.
        lug_ok = True
        shear_lug_res = ShearLugResult(
            required=False,
            shear_demand_kN=V_demand,
            shear_friction_capacity_kN=V_friction,
            lug_width_mm=None,
            lug_height_mm=None,
            lug_thickness_mm=None,
            bearing_capacity_kN=None,
            shear_capacity_kN=None,
            is_ok=True,
        )

    reactions = {"P_kN": inp.P_kN, "V_kN": inp.V_kN, "M_kNm": inp.M_kNm}
    # anchors_ok es None cuando los modos del hormigon no se han podido calcular:
    # ``is True`` impide que la ausencia se lea como un aprobado.
    cumple = (anchors_ok is True) and (t > 0) and lug_ok
    status = STATUS_VERIFICADO if anchors_ok is not None else STATUS_NO_VERIFICADO

    notes = list(anchor_tension.notes)
    if lug_req:
        notes.append(LUG_DIMS_SOURCE)

    return BaseColumnaResult(
        N_mm=N,
        B_mm=B,
        t_mm=t,
        Tu_anchor_kN=Tu,
        e_mm=e_mm,
        shear_lug=shear_lug_res,
        anchor_tension=anchor_tension,
        reactions=reactions,
        cumple=cumple,
        code=inp.code,
        verification_status=status,
        notes=tuple(notes),
    )


def _resultado_levantamiento(inp: BaseColumnaInput) -> BaseColumnaResult:
    """Resultado honesto para traccion neta / axil nulo (P <= 0).

    Sin compresion sobre el hormigon:
      - no existe area de aplastamiento -> la placa no se puede dimensionar por
        el criterio de Salmon & Johnson §14 (espesor = None);
      - la excentricidad M/P de la teoria de aplastamiento pierde sentido
        (e_mm = None);
      - la friccion base es mu * N_compresion = mu * 0 = 0 kN, luego cualquier
        cortante exige llave o pernos a cortante;
      - la DEMANDA de traccion de anclaje bajo levantamiento (axil + momento)
        NO esta derivada en este modulo -> Tu_anchor_kN = None.

    Desde la implementacion de ACI 318-19 §17.6, la CAPACIDAD a traccion si esta
    disponible (acero, cono, extraccion, desprendimiento lateral). Lo que falta
    aqui es la DEMANDA, no la capacidad: sin Tu no hay nada contra lo que
    comprobarla, luego el resultado sigue siendo NO VERIFICADO.

    Las dimensiones en planta si son independientes de P: proceden del contorno
    de la columna (d+100, bf+100), un MINIMO geometrico, no un dimensionamiento.
    """
    V_demand = abs(inp.V_kN)
    notes = (
        f"NO VERIFICADO: P = {inp.P_kN:g} kN no es compresion. Traccion neta "
        f"(levantamiento) de {abs(min(inp.P_kN, 0.0)):g} kN que los anclajes deben "
        "resistir junto con el efecto del momento; este modulo no deriva la "
        "DEMANDA de traccion Tu bajo levantamiento ni dimensiona la placa bajo "
        "traccion.",
        "Matiz respecto a la version anterior de esta nota: la CAPACIDAD a "
        "traccion de los anclajes SI esta implementada (ACI 318-19 §17.6: acero, "
        "cono de hormigon, extraccion y desprendimiento lateral) y es accesible "
        "por la rama de compresion. Lo que falta en levantamiento es la DEMANDA, "
        "no la capacidad; sin Tu no hay comprobacion posible.",
        "Friccion base = mu * compresion = 0 kN: sin axil de compresion no hay "
        "transferencia de cortante por rozamiento.",
        "N_mm y B_mm son el MINIMO geometrico por contorno de columna "
        "(d+100, bf+100), no un dimensionamiento por aplastamiento.",
    )
    anchor_tension = AnchorTensionResult(
        Tu_kN=None,
        steel_capacity_kN=None,
        steel_capacity_design_kN=None,
        concrete_breakout_kN=None,
        concrete_breakout_design_kN=None,
        concrete_breakout_status=CALC_NO_CALCULADO,
        pullout_kN=None,
        pullout_design_kN=None,
        pullout_status=CALC_NO_CALCULADO,
        side_face_blowout_kN=None,
        side_face_blowout_design_kN=None,
        side_face_blowout_status=CALC_NO_CALCULADO,
        governing_mode=None,
        governing_capacity_kN=None,
        is_ok=None,
        missing_inputs=("Tu_kN (demanda de traccion bajo levantamiento)",),
        notes=("Sin demanda Tu derivada no se comprueba ningun modo de §17.6.",),
    )
    shear_lug_res = ShearLugResult(
        required=V_demand > 0.0,
        shear_demand_kN=V_demand,
        shear_friction_capacity_kN=0.0,
        lug_width_mm=None,
        lug_height_mm=None,
        lug_thickness_mm=None,
        bearing_capacity_kN=None,
        shear_capacity_kN=None,
        is_ok=None,
    )
    return BaseColumnaResult(
        N_mm=inp.d_mm + 100.0,
        B_mm=inp.bf_mm + 100.0,
        t_mm=None,
        Tu_anchor_kN=None,
        e_mm=None,
        shear_lug=shear_lug_res,
        anchor_tension=anchor_tension,
        reactions={"P_kN": inp.P_kN, "V_kN": inp.V_kN, "M_kNm": inp.M_kNm},
        cumple=False,
        code=inp.code,
        verification_status=STATUS_NO_VERIFICADO,
        notes=notes,
    )




def check_anchor_shear_aci318_17_7(
    Vu_kN: float,
    n_anchors: int,
    db_anchor_mm: float,
    futa_MPa: float,
    fc_MPa: float,
    hef_mm: float,
    ca1_mm: float,
    ca2_mm: float | None = None,
    cracked_concrete: bool = True,
    lambda_a: float = 1.0,
    Ase_V_mm2: float | None = None,
    Tu_kN: float = 0.0,
    phi_Nn_kN: float | None = None,
) -> dict:
    phi_v_steel = 0.65
    phi_v_conc = 0.70
    ase_v = Ase_V_mm2 if Ase_V_mm2 is not None else 0.785 * (pi * db_anchor_mm ** 2 / 4.0)
    futa_eff = min(futa_MPa, 860.0)
    Vsa_kN = n_anchors * 0.60 * ase_v * futa_eff / 1000.0
    Vsa_design_kN = phi_v_steel * Vsa_kN

    le = min(hef_mm, 8.0 * db_anchor_mm)
    Vb_kN = min(
        0.6 * ((le / db_anchor_mm) ** 0.2) * sqrt(db_anchor_mm) * lambda_a * sqrt(fc_MPa) * (ca1_mm ** 1.5),
        3.7 * lambda_a * sqrt(fc_MPa) * (ca1_mm ** 1.5),
    ) / 1000.0
    AVco = 4.5 * (ca1_mm ** 2)
    w_v = 2.0 * min(ca2_mm, 1.5 * ca1_mm) if ca2_mm is not None else 3.0 * ca1_mm
    h_v = 1.5 * ca1_mm
    AVc = min(w_v * h_v, n_anchors * AVco)
    psi_ed_v = 1.0 if (ca2_mm is None or ca2_mm >= 1.5 * ca1_mm) else (0.7 + 0.3 * ca2_mm / (1.5 * ca1_mm))
    psi_c_v = 1.0 if cracked_concrete else 1.4
    Vcb_kN = (AVc / AVco) * psi_ed_v * psi_c_v * Vb_kN
    Vcb_design_kN = phi_v_conc * Vcb_kN

    k_cp = 1.0 if hef_mm < 65.0 else 2.0
    Ncp_kN = n_anchors * Nb_kN(fc_MPa, hef_mm, cast_in=True, lambda_a=lambda_a)
    Vcp_kN = k_cp * Ncp_kN
    Vcp_design_kN = phi_v_conc * Vcp_kN

    phi_Vn_kN = min(Vsa_design_kN, Vcb_design_kN, Vcp_design_kN)
    v_ratio = abs(Vu_kN) / max(phi_Vn_kN, 1e-9)
    if Tu_kN > 0.0 and phi_Nn_kN is not None and phi_Nn_kN > 0.0:
        n_ratio = Tu_kN / phi_Nn_kN
        inter_17_8 = (n_ratio ** (5.0 / 3.0)) + (v_ratio ** (5.0 / 3.0))
    else:
        inter_17_8 = v_ratio

    return {
        "Vsa_kN": Vsa_kN,
        "Vsa_design_kN": Vsa_design_kN,
        "Vcb_kN": Vcb_kN,
        "Vcb_design_kN": Vcb_design_kN,
        "Vcp_kN": Vcp_kN,
        "Vcp_design_kN": Vcp_design_kN,
        "governing_shear_design_kN": phi_Vn_kN,
        "shear_utilization": v_ratio,
        "interaction_ratio_17_8": inter_17_8,
        "is_ok": v_ratio <= 1.0 and inter_17_8 <= 1.0,
    }

__all__ = [
    "check_anchor_shear_aci318_17_7",
    "BaseColumnaInput",
    "BaseColumnaResult",
    "ShearLugResult",
    "AnchorTensionResult",
    "disenar_base",
    "ANco_mm2",
    "ANc_mm2",
    "Nb_kN",
    "psi_ed_N",
    "KC_CAST_IN_SI",
    "KC_POST_INSTALLED_SI",
    "PHI_STEEL_TENSION",
    "PHI_CONCRETE_TENSION",
    "PHI_SOURCE",
    "MODE_STEEL",
    "MODE_BREAKOUT",
    "MODE_PULLOUT",
    "MODE_BLOWOUT",
    "CALC_APLICA",
    "CALC_NO_APLICA",
    "CALC_NO_CALCULADO",
    "LUG_HEIGHT_MM",
    "LUG_THICKNESS_MM",
    "LUG_DIMS_SOURCE",
    "STATUS_VERIFICADO",
    "STATUS_NO_VERIFICADO",
]
