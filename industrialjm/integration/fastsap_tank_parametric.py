"""Bridge IndustrialJm -> FastSAP: generacion parametrica de modelo de tanque."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TankParametric:
    D_m: float
    H_m: float
    n_circ: int = 16
    n_vert: int = 10
    t_shell_mm: float = 8.0
    material: str = "A36"


class FastSAPTankBuilder:
    def __init__(self, client: Any = None, dry_run: bool = False):
        self.client = client
        self.dry_run = dry_run

    def build(self, tank: TankParametric) -> dict:
        from math import cos, pi, sin
        joints, shells = [], []
        for j in range(tank.n_vert + 1):
            z = j * tank.H_m / tank.n_vert
            for i in range(tank.n_circ):
                theta = 2 * pi * i / tank.n_circ
                x = (tank.D_m / 2) * cos(theta)
                y = (tank.D_m / 2) * sin(theta)
                joints.append({"name": f"J_{j}_{i}", "x": x, "y": y, "z": z})
        for j in range(tank.n_vert):
            for i in range(tank.n_circ):
                n1 = f"J_{j}_{i}"
                n2 = f"J_{j}_{(i + 1) % tank.n_circ}"
                n3 = f"J_{j+1}_{(i + 1) % tank.n_circ}"
                n4 = f"J_{j+1}_{i}"
                shells.append({"name": f"S_{j}_{i}", "n1": n1, "n2": n2, "n3": n3, "n4": n4})
        if self.dry_run or self.client is None:
            return {"joints": joints, "shells": shells, "dry_run": True}
        created = 0
        failed: dict[str, str] = {}
        for s in shells:
            try:
                self.client.AreaObj.AddByPoint([s["n1"], s["n2"], s["n3"], s["n4"]], s["name"])
                created += 1
            except Exception as exc:  # registra el fallo, no lo traga en silencio
                failed[s["name"]] = str(exc)
        return {"joints": joints, "shells": shells,
                "applied": created, "failed": failed, "dry_run": False}


def build_housner_stick_model(geom: Any, Sa_i: float, Sa_c: float,
                              g: float = 9.80665) -> dict:
    """Modelo "stick" Housner del líquido para SAP (idea #11): conecta
    ``api650.housner_masses`` con un modelo de masas concentradas.

    Representación production-correct del oleaje (API 650 §E): la masa impulsiva
    (W_i/g) va rígida a la altura ``h_i``; la convectiva (W_c/g) cuelga de un
    resorte horizontal de rigidez ``k_c = m_c·ω_c²`` (ω_c = 2π/T_c) a ``h_c`` —
    así el modal reproduce el periodo de sloshing ``T_c``. Es uno de los casos
    legítimos de masa concentrada (componente inercial discreto), no masa nodal
    arbitraria.

    Devuelve ``{nodes, masses, convective_spring, seismic}`` (en unidades kN-m:
    masa en kN·s²/m, rigidez en kN/m)."""
    from math import pi
    from ..tanks.api650 import housner_masses

    sm = housner_masses(geom, Sa_i, Sa_c)
    m_i = sm.W_i_kN / g
    m_c = sm.W_c_kN / g
    omega_c = (2.0 * pi / sm.T_c_s) if sm.T_c_s > 0 else 0.0
    k_c = m_c * omega_c ** 2

    return {
        "nodes": [
            {"name": "BASE", "x": 0.0, "y": 0.0, "z": 0.0, "restraint": [True] * 6},
            {"name": "IMP", "x": 0.0, "y": 0.0, "z": sm.h_i_m, "restraint": None},
            {"name": "CONV", "x": 0.0, "y": 0.0, "z": sm.h_c_m, "restraint": None},
        ],
        "masses": [
            {"node": "IMP", "mass": m_i, "note": "impulsiva (rígida al manto)"},
            {"node": "CONV", "mass": m_c, "note": "convectiva (sobre resorte T_c)"},
        ],
        "convective_spring": {"node": "CONV", "k_kN_m": k_c, "T_c_s": sm.T_c_s},
        "seismic": sm.to_dict(),
    }


__all__ = ["TankParametric", "FastSAPTankBuilder", "build_housner_stick_model"]
