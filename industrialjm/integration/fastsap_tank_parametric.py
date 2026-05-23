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
        for s in shells:
            try:
                self.client.AreaObj.AddByPoint([s["n1"], s["n2"], s["n3"], s["n4"]], s["name"])
                created += 1
            except Exception:  # pragma: no cover
                pass
        return {"joints": joints, "shells": shells, "applied": created, "dry_run": False}


__all__ = ["TankParametric", "FastSAPTankBuilder"]
