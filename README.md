# plantstruct

Estructuras de planta industrial: tanques API 650 (masas impulsiva y convectiva de Housner, momento volcante, pandeo del manto, espesor por el método del pie, anclaje), silos (EN 1991-4, pandeo), chimeneas, pipe racks, pórticos, búnkeres, esferas de GLP, bases de columna y vigas mixtas de entrepiso (AISC 360 y EN 1994).

[![CI](https://github.com/jmurgass99/plantstruct/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/plantstruct/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Paquete independiente. Única dependencia obligatoria: `numpy`. El cálculo de vigas mixtas lleva su propia copia de las rutinas AISC/EN 1994 (`plantstruct/_composite`), sin dependencias externas.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/plantstruct.git
```

Extras: `api` (REST con FastAPI), `test`.

```bash
git clone https://github.com/jmurgass99/plantstruct.git
cd plantstruct
pip install -e ".[test,api]"
pytest -q
```

## Inicio rápido

### Masas sísmicas de Housner en un tanque API 650 (§E.6.1)

```python
from plantstruct.tanks import TankGeometry, housner_masses

g = TankGeometry(D_m=20.0, H_l_m=15.0, t_shell_mm=8.0)
m = housner_masses(g, Sa_i=0.30, Sa_c=0.10)   # aceleraciones espectrales impulsiva y convectiva (g)
print(m)
```

### Espesor del manto por el método del pie (API 650 §5.6.3)

```python
from plantstruct.tanks import shell_thickness_one_foot
help(shell_thickness_one_foot)
```

### Silos según EN 1991-4 y pandeo del manto

```python
from plantstruct import silos_en1991_4, silo_buckling
```

## Módulos

| Módulo | Contenido |
|---|---|
| `tanks/` | API 650: `api650` (Housner, pandeo axial), `shell_design` (espesores, tensión anular), `shell_buckling` (pandeo del manto, Rotter), `anchorage` (anclaje y método J) |
| `report_api650`, `external_pressure`, `anchor_codes` | Informe, presión exterior, anclajes multinorma |
| `silos_en1991_4`, `ec1_silos`, `silo_buckling` | Acciones en silos y pandeo |
| `chimneys`, `esferas_gpl`, `bunker`, `pipe_rack`, `portal_frame`, `bases_columna` | Otras estructuras industriales |
| `asce7_15_7` | Componentes no estructurales y tanques según ASCE 7 cap. 15 |
| `composite_beams` | Vigas mixtas de entrepiso industrial (AISC 360 y EN 1994, rutinas vendorizadas en `_composite/`) |
| `integration/fastsap_tank_parametric` | Modelo de barras tipo Housner para exportar a SAP2000 si `fastsap` está disponible (opcional) |
| `api/` | REST API con FastAPI (extra `api`) |

## Estado

Versión 0.1: el núcleo de tanques (Housner, manto, anclaje) y silos está cubierto por tests; otras estructuras están en distinto grado de madurez. Consulta los tests para saber qué está verificado.

## Licencia

MIT. Consulta [LICENSE](LICENSE).

---

Parte del toolkit estructural de código abierto **Loadpath**, de [Jesús Murgas](https://github.com/jmurgass99).
