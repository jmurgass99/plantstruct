"""FastSAPTankBuilder debe reportar fallos OAPI, no tragarlos en silencio."""
from __future__ import annotations

from industrialjm.integration.fastsap_tank_parametric import (
    TankParametric, FastSAPTankBuilder,
)


class _StubSap:
    def __init__(self, raise_on=()):
        self.calls = []
        raise_on = set(raise_on)
        outer = self

        class _AreaObj:
            @staticmethod
            def AddByPoint(points, name, *a):
                outer.calls.append(name)
                if name in raise_on:
                    raise RuntimeError(f"OAPI error en {name}")
                return 0

        self.AreaObj = _AreaObj


def test_build_reports_failed_shells():
    # tanque pequeno: n_circ=2, n_vert=1 -> 2 shells: S_0_0, S_0_1
    sap = _StubSap(raise_on={"S_0_1"})
    b = FastSAPTankBuilder(client=sap, dry_run=False)

    res = b.build(TankParametric(D_m=5, H_m=4, n_circ=2, n_vert=1))

    assert res["applied"] == 1            # solo S_0_0 creado
    assert isinstance(res["failed"], dict)            # shape uniforme name->mensaje
    assert "OAPI error" in res["failed"]["S_0_1"]     # mensaje preservado
    assert "S_0_0" not in res["failed"]
