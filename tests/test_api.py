"""Test API PlantStruct."""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from plantstruct.api import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_health(client):
    assert client.get("/api/tanks/health").status_code == 200


def test_housner(client):
    r = client.post("/api/tanks/api650/housner", json={
        "D_m": 20, "H_l_m": 15, "Sa_i": 0.3, "Sa_c": 0.1,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["W_i_kN"] > 0


def test_anchorage(client):
    r = client.post("/api/tanks/anchorage", json={
        "D_m": 20, "W_tank_kN": 5000, "M_overturn_kNm": 500_000,
        "n_bolts": 12,
    })
    assert r.status_code == 200
    assert "DCR" in r.json()


def test_shell_buckling(client):
    r = client.post("/api/tanks/shell-buckling", json={
        "D_m": 20, "H_shell_m": 16, "H_liquid_m": 15, "t_shell_mm": 8,
    })
    assert r.status_code == 200
    assert r.json()["DCR_interaction"] >= 0


# ===========================================================================
# IN-005: POST /api/tanks/api650/full-design
# ===========================================================================

class TestFullDesign:
    """Endpoint de diseno completo API 650."""

    def test_full_design_respuesta_completa(self, client):
        """Request con datos validos retorna respuesta con todos los campos."""
        r = client.post("/api/tanks/api650/full-design", json={
            "D": 10, "H": 8, "t_shell": 8,
            "liquid_density": 1000, "Sa": 0.3, "Ss": 0.1,
        })
        assert r.status_code == 200
        body = r.json()

        # Masas
        assert "masses" in body
        assert body["masses"]["m_i"] > 0
        assert body["masses"]["m_c"] > 0

        # Periodos
        assert "periods" in body
        assert body["periods"]["T_i"] > 0
        assert body["periods"]["T_c"] > 0

        # Corte basal y momento
        assert "base_shear" in body
        assert body["base_shear"] > 0
        assert "overturning_moment" in body
        assert body["overturning_moment"] > 0

        # Anclaje
        assert "anchorage" in body
        assert "J" in body["anchorage"]
        assert "N_bolts" in body["anchorage"]
        assert body["anchorage"]["J"] > 0

        # Pandeo
        assert "buckling" in body
        assert "ratio" in body["buckling"]
        assert "status" in body["buckling"]
        assert body["buckling"]["status"] in ("safe", "unsafe")

        # Memo markdown
        assert "memo_md" in body
        assert len(body["memo_md"]) > 100
        assert "Housner" in body["memo_md"]

    def test_full_design_tanque_grande(self, client):
        """Tanque grande con sismo alto."""
        r = client.post("/api/tanks/api650/full-design", json={
            "D": 30, "H": 20, "t_shell": 12,
            "liquid_density": 850, "Sa": 0.5, "Ss": 0.15,
            "n_bolts": 32,
        })
        assert r.status_code == 200
        body = r.json()
        # Verificar que masas son significativas
        assert body["masses"]["m_i"] > 1000  # kN
        assert body["periods"]["T_c"] > 2  # largo para tanque grande

    def test_full_design_validation_D_zero(self, client):
        """D = 0 debe fallar con 422."""
        r = client.post("/api/tanks/api650/full-design", json={
            "D": 0, "H": 8, "t_shell": 8,
            "liquid_density": 1000, "Sa": 0.3, "Ss": 0.1,
        })
        assert r.status_code == 422

    def test_full_design_todos_los_campos_presentes(self, client):
        """Verifica que cada campo del schema existe en la respuesta."""
        r = client.post("/api/tanks/api650/full-design", json={
            "D": 15, "H": 12, "t_shell": 10,
            "liquid_density": 1000, "Sa": 0.4, "Ss": 0.12,
        })
        body = r.json()
        top_keys = {"masses", "periods", "base_shear", "overturning_moment",
                     "anchorage", "buckling", "memo_md"}
        assert top_keys.issubset(set(body.keys()))
