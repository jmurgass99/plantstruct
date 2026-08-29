"""Esquemas Pydantic v2 - BunkerDesignJm (backlog #38).

Diseno de muro resistente a explosion (estructura protectora / bunker) modelado
como un sistema de un grado de libertad (SDOF) elasto-plastico perfecto. Se
evalua la demanda de ductilidad ante una carga impulsiva y se compara contra una
ductilidad admisible.

Unidades (SI consistente):
    pr     [Pa]   sobrepresion reflejada pico (informativa; el diseno usa el impulso)
    impulse[N*s/m^2 = Pa*s] -> impulso reflejado especifico por unidad de area
    m      [kg/m^2] masa por unidad de area del muro
    k      [N/m / m^2 = Pa/m] rigidez del SDOF por unidad de area
    Rm     [Pa]   resistencia ultima (plateau plastico) por unidad de area
    span   [m]    luz del muro (opcional, para la rotacion de apoyo)
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BunkerIn(BaseModel):
    """Entrada del diseno SDOF de muro anti-explosion.

    El impulso especifico `impulse` es el motor del calculo (asintota impulsiva);
    `pr` (presion reflejada pico) se transporta como dato informativo. La
    deflexion elastica se obtiene de x_el = Rm/k.
    """

    model_config = ConfigDict(extra="forbid")

    pr: float = Field(
        0.0,
        ge=0.0,
        description="Sobrepresion reflejada pico pr [Pa] (informativa).",
    )
    impulse: float = Field(
        ...,
        gt=0.0,
        description="Impulso reflejado especifico i [Pa*s] (= N*s/m^2).",
    )
    m: float = Field(
        ...,
        gt=0.0,
        description="Masa por unidad de area del muro m [kg/m^2].",
    )
    k: float = Field(
        ...,
        gt=0.0,
        description="Rigidez del SDOF por unidad de area k [Pa/m].",
    )
    Rm: float = Field(
        ...,
        gt=0.0,
        description="Resistencia ultima (plateau plastico) Rm [Pa].",
    )
    mu_allowable: float = Field(
        ...,
        ge=1.0,
        description="Ductilidad admisible mu_adm (>= 1). Criterio pass/fail.",
    )
    span: float | None = Field(
        None,
        gt=0.0,
        description="Luz del muro L [m] (opcional). Si se da, calcula la rotacion de apoyo.",
    )


class BunkerOut(BaseModel):
    """Resultados del diseno SDOF de muro anti-explosion."""

    x_el: float = Field(
        ...,
        description="Deflexion elastica x_el = Rm/k [m].",
    )
    mu: float = Field(
        ...,
        description="Ductilidad demandada mu = 1 + i^2/(2*m*Rm*x_el) (asintota impulsiva).",
    )
    x_max: float = Field(
        ...,
        description="Deflexion maxima x_max = mu * x_el [m].",
    )
    support_rotation_deg: float | None = Field(
        None,
        description="Rotacion de apoyo theta = atan(x_max/(L/2)) [grados] (si se dio span).",
    )
    mu_allowable: float = Field(..., description="Ductilidad admisible usada en el criterio.")
    passed: bool = Field(
        ...,
        description="True si mu <= mu_allowable (el muro resiste la demanda).",
    )
    demand_capacity_ratio: float = Field(
        ...,
        description="Razon demanda/capacidad mu / mu_allowable (<= 1 -> pasa).",
    )


__all__ = ["BunkerIn", "BunkerOut"]
