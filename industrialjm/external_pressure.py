"""
Estabilidad de manto cilíndrico bajo presión externa / vacío (idea #17).

API 650 §5.9.7 y ASME VIII Div 1 UG-28: presión externa crítica
para cilindros cortos:

    P_cr = 2.6 * E * (t/D)^2.5 / (L/D - 0.45 * sqrt(t/D))

Pure Python. Soporta:
- USA (API 650 / ASME VIII)
- EU (EN 14015, EN 1993-1-6)
- AS 1170.4 (estanque AU)
- NSR-10 (CO) — adopta API 650
- SG (BC 1) — adopta ASME

Devuelve presión crítica y factor de seguridad vs presión externa aplicada.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ExtPressureInput:
    D_m: float            # diámetro
    t_mm: float           # espesor manto
    L_m: float            # longitud entre rigidizadores
    E_MPa: float = 200000.0
    P_ext_kPa: float = 1.0   # presión exterior aplicada (vacío típico = 1 atm)
    code: str = "USA"


@dataclass(frozen=True)
class ExtPressureResult:
    P_cr_kPa: float
    factor_of_safety: float
    required_FS: float
    passes: bool
    code: str


_FS = {
    "USA": 3.0, "API": 3.0, "ASME": 3.0,
    "EU": 1.5, "EUROCODE": 1.5,
    "NSR": 3.0, "CO": 3.0,
    "AS": 3.0, "AU": 3.0,
    "SG": 1.5, "SS": 1.5,
}


def critical_external_pressure(inp: ExtPressureInput) -> ExtPressureResult:
    if inp.D_m <= 0 or inp.t_mm <= 0 or inp.L_m <= 0:
        raise ValueError("D, t, L > 0 requeridos")
    c = inp.code.upper()
    if c not in _FS:
        raise ValueError(f"Código desconocido: {inp.code}")
    t_m = inp.t_mm / 1000.0
    tD = t_m / inp.D_m
    LD = inp.L_m / inp.D_m
    denom = LD - 0.45 * math.sqrt(tD)
    if denom <= 0:
        # Cilindro muy corto -> fórmula no aplicable; usamos límite
        denom = 0.01
    # Fórmula en MPa con t/D adimensional, devolvemos kPa
    P_cr_MPa = 2.6 * inp.E_MPa * (tD ** 2.5) / denom
    P_cr_kPa = P_cr_MPa * 1000.0
    fs = P_cr_kPa / max(inp.P_ext_kPa, 1e-9)
    req = _FS[c]
    return ExtPressureResult(P_cr_kPa=P_cr_kPa, factor_of_safety=fs,
                             required_FS=req, passes=(fs >= req), code=inp.code)


def max_unstiffened_length_m(D_m: float, t_mm: float, P_ext_kPa: float,
                             E_MPa: float = 200000.0, code: str = "USA") -> float:
    """Distancia máxima entre rigidizadores para resistir P_ext."""
    if D_m <= 0 or t_mm <= 0 or P_ext_kPa <= 0:
        raise ValueError("D, t, P_ext > 0")
    c = code.upper()
    if c not in _FS:
        raise ValueError(f"Código desconocido: {code}")
    fs = _FS[c]
    t_m = t_mm / 1000.0
    tD = t_m / D_m
    # Resolver L tal que P_cr = fs * P_ext
    P_target_MPa = fs * P_ext_kPa / 1000.0
    # 2.6 * E * (tD)^2.5 / (L/D - 0.45*sqrt(tD)) = P_target
    rhs = 2.6 * E_MPa * (tD ** 2.5) / P_target_MPa
    LD = rhs + 0.45 * math.sqrt(tD)
    return LD * D_m
