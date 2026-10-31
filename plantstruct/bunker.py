"""Nucleo de calculo - BunkerDesignJm (backlog #38).

Diseno de muro resistente a explosion (estructura protectora) como SDOF
elasto-plastico perfecto sometido a una carga impulsiva.

Asintota impulsiva de la demanda de ductilidad
----------------------------------------------
En el regimen puramente impulsivo (duracion de la carga << periodo natural), toda
la energia cinetica inicial impartida por el impulso se disipa en el trabajo del
resorte resistente. Igualando la energia cinetica a la energia de deformacion
plastica se obtiene la forma usada por este modulo (la del enunciado):

        mu = 1 + i^2 / (2 * m * Rm * x_el)

donde:
    i    = impulso reflejado especifico [Pa*s]
    m    = masa por unidad de area      [kg/m^2]
    Rm   = resistencia ultima (plateau) [Pa]
    x_el = deflexion elastica = Rm / k  [m]

NOTA DE MODELADO: existe una variante de libro de texto que usa
`mu = 0.5 + i^2/(2*m*Rm*x_el)` (cuando la energia cinetica se iguala a la energia
de deformacion TOTAL, elastica + plastica). Este modulo implementa
deliberadamente la forma `1 + ...` del enunciado del backlog #38 (energia cinetica
igualada a la deformacion plastica medida desde el limite elastico). El test de
forma cerrada verifica exactamente esta expresion.

Rotacion de apoyo (opcional)
----------------------------
Si se entrega la luz L, la rotacion de apoyo (definicion UFC 3-340-02) es:
        theta = atan( x_max / (L/2) )
con x_max = mu * x_el.

Criterio pass/fail: el muro resiste si mu <= mu_admisible.

numpy se importa de forma perezosa dentro de las funciones.
"""
from __future__ import annotations

import math

from .bunker_schemas import BunkerIn, BunkerOut


def elastic_deflection(Rm: float, k: float) -> float:
    """Deflexion elastica x_el = Rm/k [m].

    Raises:
        ValueError: si Rm <= 0 o k <= 0.
    """
    if Rm <= 0.0:
        raise ValueError("La resistencia Rm debe ser positiva.")
    if k <= 0.0:
        raise ValueError("La rigidez k debe ser positiva.")
    return Rm / k


def ductility_impulsive(impulse: float, m: float, Rm: float, x_el: float) -> float:
    """Ductilidad demandada (asintota impulsiva) mu = 1 + i^2/(2*m*Rm*x_el).

    Args:
        impulse: impulso reflejado especifico i [Pa*s].
        m: masa por unidad de area [kg/m^2].
        Rm: resistencia ultima [Pa].
        x_el: deflexion elastica [m].

    Raises:
        ValueError: si algun parametro no es positivo.
    """
    if impulse <= 0.0:
        raise ValueError("El impulso debe ser positivo.")
    if m <= 0.0:
        raise ValueError("La masa m debe ser positiva.")
    if Rm <= 0.0:
        raise ValueError("La resistencia Rm debe ser positiva.")
    if x_el <= 0.0:
        raise ValueError("La deflexion elastica x_el debe ser positiva.")
    return 1.0 + (impulse * impulse) / (2.0 * m * Rm * x_el)


def support_rotation_deg(x_max: float, span: float) -> float:
    """Rotacion de apoyo theta = atan(x_max/(L/2)) en grados.

    Raises:
        ValueError: si span <= 0 o x_max < 0.
    """
    if span <= 0.0:
        raise ValueError("La luz span debe ser positiva.")
    if x_max < 0.0:
        raise ValueError("x_max no puede ser negativo.")
    return math.degrees(math.atan(x_max / (span / 2.0)))


def design_bunker(model: BunkerIn) -> BunkerOut:
    """Diseno completo del muro SDOF anti-explosion.

    Calcula x_el, la ductilidad demandada (asintota impulsiva), x_max, la rotacion
    de apoyo (si se da la luz) y el veredicto pass/fail contra mu_admisible.

    Raises:
        ValueError: si la fisica del problema es invalida.
    """
    # numpy disponible de forma perezosa para operaciones vectoriales futuras.
    import numpy as np

    x_el = elastic_deflection(model.Rm, model.k)
    mu = ductility_impulsive(model.impulse, model.m, model.Rm, x_el)
    x_max = mu * x_el

    rotation = None
    if model.span is not None:
        rotation = support_rotation_deg(x_max, model.span)

    # razon demanda/capacidad de ductilidad; np.float -> float nativo
    dcr = float(np.divide(mu, model.mu_allowable))
    passed = mu <= model.mu_allowable

    return BunkerOut(
        x_el=x_el,
        mu=mu,
        x_max=x_max,
        support_rotation_deg=rotation,
        mu_allowable=model.mu_allowable,
        passed=passed,
        demand_capacity_ratio=dcr,
    )


__all__ = [
    "elastic_deflection",
    "ductility_impulsive",
    "support_rotation_deg",
    "design_bunker",
]
