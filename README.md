# plantstruct

**Español** · [English](README.en.md)

Estructuras de planta industrial en Python: tanques API 650, silos EN 1991-4, chimeneas, esferas, pipe racks, bases de columna y vigas mixtas.

[![CI](https://github.com/jmurgass99/plantstruct/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/plantstruct/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)

## Qué hace

- Tanques atmosféricos API 650: virolas, pandeo del manto, presión exterior, masas de Housner del Anexo E (sismo) y anclajes.
- Silos EN 1991-4: presiones de Janssen, clases de esbeltez, factores de descarga y pandeo meridional (EN 1993-1-6).
- Chimeneas (desprendimiento de vórtices), esferas de GLP (ASME VIII) y pipe racks.
- Bases de columna y vigas mixtas.

Única dependencia base: `numpy`.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/plantstruct.git
```

Extra opcional: `api`.

## Ejemplo

Presiones de Janssen en un silo de trigo (D = 6 m, γ = 9 kN/m³, K = 0,54, μ = 0,38) a 18 m de profundidad:

```python
from plantstruct.ec1_silos import janssen_pressure

p_h, p_v = janssen_pressure(18.0, 9.0, 0.38, 0.54, 6.0)
print(round(p_h, 2), round(p_v, 2))   # 32.5 60.18  (kPa)
```

Más casos en [`examples/`](examples).

## Qué no hace

- Tanques de más de 60 m (método del punto de diseño variable), techos flotantes, fondos y cimentaciones de tanque.
- Silos con tolva, descarga excéntrica detallada o silos de hormigón.
- Amplitud de vibración por vórtices: `chimneys` solo da la condición de resonancia y está marcado como experimental.
- Cortante en pernos de anclaje (ACI 318-19 §17.7) dentro de `disenar_base`: existe aparte `check_anchor_shear_aci318_17_7`.

El detalle está en [docs/LIMITACIONES.md](docs/LIMITACIONES.md).

## Pruebas

```bash
pip install -e ".[test]"
pytest -q
```

## Licencia

MIT. Ver [LICENSE](LICENSE). Autor: [Jesús Murgas](https://github.com/jmurgass99).
