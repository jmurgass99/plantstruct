# plantstruct

[Español](README.md) · **English**

Industrial plant structures in Python: API 650 tanks, EN 1991-4 silos, stacks, spheres, pipe racks, column bases and composite beams.

[![CI](https://github.com/jmurgass99/plantstruct/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/plantstruct/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What it does

- API 650 atmospheric tanks: shell courses, shell buckling, external pressure, Annex E Housner masses (seismic) and anchors.
- EN 1991-4 silos: Janssen pressures, slenderness classes, discharge factors and meridional buckling (EN 1993-1-6).
- Stacks (vortex shedding), LPG spheres (ASME VIII) and pipe racks.
- Column bases and composite beams.

Only base dependency: `numpy`.

## Install

```bash
pip install git+https://github.com/jmurgass99/plantstruct.git
```

Optional extra: `api`.

## Example

Janssen pressures in a wheat silo (D = 6 m, γ = 9 kN/m³, K = 0.54, μ = 0.38) at 18 m depth:

```python
from plantstruct.ec1_silos import janssen_pressure

p_h, p_v = janssen_pressure(18.0, 9.0, 0.38, 0.54, 6.0)
print(round(p_h, 2), round(p_v, 2))   # 32.5 60.18  (kPa)
```

More cases in [`examples/`](examples).

## What it does not do

- Tanks over 60 m (variable-design-point method), floating roofs, tank bottoms and foundations.
- Silos with a hopper, detailed eccentric discharge, or concrete silos.
- Vortex vibration amplitude: `chimneys` only gives the resonance condition and is marked experimental.
- Anchor bolt shear (ACI 318-19 §17.7) inside `disenar_base`: `check_anchor_shear_aci318_17_7` exists separately.

Details are in [docs/LIMITACIONES.md](docs/LIMITACIONES.md) (in Spanish).

## Tests

```bash
pip install -e ".[test]"
pytest -q
```

## License

MIT. See [LICENSE](LICENSE). Author: [Jesús Murgas](https://github.com/jmurgass99).
