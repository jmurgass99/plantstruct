"""API REST sin servidor: Housner, anclaje, pandeo, diseño completo API 650 y Janssen de silos con TestClient.

La aplicación (`plantstruct.api.create_app`, extra `api`) expone seis rutas. Aquí se llaman
con el TestClient de FastAPI, sin levantar uvicorn: tanque de 20 m × 15 m con t = 10 mm,
A_i = 0,30 g y A_c = 0,10 g; silo de trigo de 6 m × 18 m a z = 18 m. Se muestra también la
validación 422 (D = 0) y el 400 de una entrada físicamente inválida.

Ejecutar:  python examples/rest_api_tanks_api650_full_design_and_silos_janssen_testclient.py
"""
import json
import warnings

warnings.filterwarnings("ignore")
from fastapi.testclient import TestClient  # noqa: E402

from plantstruct.api import create_app  # noqa: E402


def show(titulo: str, r) -> None:
    body = r.json()
    if isinstance(body, dict) and "memo_md" in body:
        body = {k: v for k, v in body.items() if k != "memo_md"} | {"memo_md": f"<{len(r.json()['memo_md'])} caracteres de Markdown>"}
    print(f"{titulo} → {r.status_code}")
    print("  ", json.dumps(body, ensure_ascii=False, default=lambda o: round(o, 3) if isinstance(o, float) else o)[:600])


def main() -> None:
    c = TestClient(create_app())
    show("GET  /api/tanks/health", c.get("/api/tanks/health"))
    show("POST /api/tanks/api650/housner", c.post("/api/tanks/api650/housner", json={"D_m": 20, "H_l_m": 15, "t_shell_mm": 8, "Sa_i": 0.30, "Sa_c": 0.10}))
    show("POST /api/tanks/anchorage", c.post("/api/tanks/anchorage", json={"D_m": 20, "W_tank_kN": 900, "M_overturn_kNm": 70000, "n_bolts": 24, "bolt_diameter_mm": 30}))
    show("POST /api/tanks/shell-buckling", c.post("/api/tanks/shell-buckling", json={"D_m": 20, "H_shell_m": 16, "H_liquid_m": 15, "t_shell_mm": 10, "sigma_axial_imposed_MPa": 15}))
    r = c.post("/api/tanks/api650/full-design", json={"D": 20, "H": 15, "t_shell": 10, "liquid_density": 1000, "Sa": 0.30, "Ss": 0.10, "n_bolts": 24, "bolt_diameter_mm": 30})
    show("POST /api/tanks/api650/full-design", r)
    print("   periods:", {k: round(v, 3) for k, v in r.json()["periods"].items()}, "| anchorage:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.json()["anchorage"].items()})
    show("POST /api/industrial/silos/janssen", c.post("/api/industrial/silos/janssen", json={"height_m": 18, "diameter_m": 6, "depth_z_m": 18, "gamma_kN_m3": 9.0, "mu_friction": 0.38, "K_ratio": 0.54}))
    print(f"\nD = 0 en full-design → {c.post('/api/tanks/api650/full-design', json={'D': 0, 'H': 8, 't_shell': 8, 'Sa': 0.3, 'Ss': 0.1}).status_code} (validación Pydantic)")
    print(f"3 pernos en anchorage → {c.post('/api/tanks/anchorage', json={'D_m': 20, 'W_tank_kN': 900, 'M_overturn_kNm': 70000, 'n_bolts': 3}).status_code} (422: n_bolts >= 4 en el esquema)")


if __name__ == "__main__":
    main()
