"""Golden test para diseño de bases de columna (Salmon & Johnson / AISC DG1).

Requisitos:
1. Reacciones completas de apoyo (P, V, M) recibidas como ENTRADA.
2. Comprobación de placa base, tracción en pernos de anclaje y llave de cortante (shear lug).
3. Verificación de capacidad cuando el cortante excede la fricción base.
"""
from __future__ import annotations

import pytest
from plantstruct.bases_columna import (
    BaseColumnaInput,
    disenar_base,
)


def test_golden_column_base_with_shear_lug_and_reactions():
    """GOLDEN. Verificación de placa base, anclajes y llave de cortante bajo solicitaciones completas."""
    # Reacciones en la base: P = 600 kN, V = 180 kN, M = 85 kNm
    inp = BaseColumnaInput(
        P_kN=600.0,
        V_kN=180.0,
        M_kNm=85.0,
        bf_mm=200.0,
        d_mm=300.0,
        fy_MPa=250.0,
        fc_MPa=25.0,
        fyb_MPa=420.0,
        n_anchors=4,
        db_anchor_mm=25.0,
        mu_friction=0.20,  # Fricción disponible = 0.20 * 600 = 120 kN < V = 180 kN -> Requiere shear lug
        code="US",
    )

    res = disenar_base(inp)

    # 1. Reacciones de entrada preservadas
    assert res.reactions["P_kN"] == 600.0
    assert res.reactions["V_kN"] == 180.0
    assert res.reactions["M_kNm"] == 85.0

    # 2. Geometría de placa
    assert res.N_mm >= 400.0
    assert res.B_mm >= 300.0
    assert res.t_mm > 15.0

    # 3. Llave de cortante requerida y con capacidad suficiente
    assert res.shear_lug.required is True
    assert res.shear_lug.shear_demand_kN == 180.0
    assert res.shear_lug.shear_friction_capacity_kN == 120.0
    assert res.shear_lug.lug_width_mm > 0.0
    assert res.shear_lug.bearing_capacity_kN >= 180.0
    assert res.shear_lug.is_ok is True

    # 4. Cumplimiento global
    assert res.cumple is True
