# IndustrialJm

Estanques metálicos API 650 + estructuras industriales (IEG 3280).

## Scope

- **`industrialjm.tanks.api650`** — Masas impulsiva/convectiva (Housner),
  periodo convectivo, momento volcante, pandeo elástico del manto.
- *(roadmap)* `tanks.anchorage` — Diseño de anclajes según API 650 §E.6.2.
- *(roadmap)* `tanks.sap_bridge` — Generación paramétrica del estanque en
  SAP2000 vía `fastsap` OAPI (manto + techo + fondo + masas).

## Quick start

```python
from industrialjm.tanks import TankGeometry, housner_masses

g = TankGeometry(D_m=20, H_l_m=15)
result = housner_masses(g, Sa_i=0.3, Sa_c=0.10)
print(result.to_dict())
```

## Tests

```bash
pip install -e .[test]
pytest -q
```
