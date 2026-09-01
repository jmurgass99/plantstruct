"""Bases de columna - diseno placa base por Salmon & Johnson.

Considera carga axial + momento, dimensiona placa, anclajes y rigidizadores.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


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
                "is_ok": self.shear_lug.is_ok,
                "dims_source": self.shear_lug.dims_source,
            },
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

    # Capacidad anclajes a tracción
    import math
    A_anchor = math.pi * (inp.db_anchor_mm ** 2) / 4.0
    cap_anchor = (inp.n_anchors / 2.0) * A_anchor * inp.fyb_MPa / 1000.0
    anchors_ok = Tu <= cap_anchor

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
    cumple = anchors_ok and (t > 0) and lug_ok

    notes = [
        "Capacidad de anclajes a traccion = fluencia de los pernos unicamente; "
        "NO incluye arrancamiento del cono de hormigon ni extraccion (ACI 318 Cap. 17).",
    ]
    if lug_req:
        notes.append(LUG_DIMS_SOURCE)

    return BaseColumnaResult(
        N_mm=N,
        B_mm=B,
        t_mm=t,
        Tu_anchor_kN=Tu,
        e_mm=e_mm,
        shear_lug=shear_lug_res,
        reactions=reactions,
        cumple=cumple,
        code=inp.code,
        verification_status=STATUS_VERIFICADO,
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
      - la traccion de anclaje bajo levantamiento (axil + momento) NO esta
        implementada en este modulo -> Tu_anchor_kN = None.

    Las dimensiones en planta si son independientes de P: proceden del contorno
    de la columna (d+100, bf+100), un MINIMO geometrico, no un dimensionamiento.
    """
    V_demand = abs(inp.V_kN)
    notes = (
        f"NO VERIFICADO: P = {inp.P_kN:g} kN no es compresion. Traccion neta "
        f"(levantamiento) de {abs(min(inp.P_kN, 0.0)):g} kN que los anclajes deben "
        "resistir junto con el efecto del momento; este modulo no dimensiona "
        "anclajes a levantamiento ni la placa bajo traccion.",
        "Friccion base = mu * compresion = 0 kN: sin axil de compresion no hay "
        "transferencia de cortante por rozamiento.",
        "N_mm y B_mm son el MINIMO geometrico por contorno de columna "
        "(d+100, bf+100), no un dimensionamiento por aplastamiento.",
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
        reactions={"P_kN": inp.P_kN, "V_kN": inp.V_kN, "M_kNm": inp.M_kNm},
        cumple=False,
        code=inp.code,
        verification_status=STATUS_NO_VERIFICADO,
        notes=notes,
    )


__all__ = [
    "BaseColumnaInput",
    "BaseColumnaResult",
    "ShearLugResult",
    "disenar_base",
    "LUG_HEIGHT_MM",
    "LUG_THICKNESS_MM",
    "LUG_DIMS_SOURCE",
    "STATUS_VERIFICADO",
    "STATUS_NO_VERIFICADO",
]

