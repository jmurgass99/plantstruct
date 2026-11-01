"""Tracción circunferencial de membrana en un depósito cilíndrico (fichas W01046/W01096/W01112).

Depósito de H = 10 m y r = 5 m lleno de agua (γ = 10 kN/m³): T = γ·(H − y)·r, que en la base
vale 10·10·5 = 500 kN/m, el valor resuelto en la ficha. Se imprime el perfil con la cota y, el
efecto de una presión interior de gas de 20 kPa (T_int = p·r = 100 kN/m) y la tensión de
membrana σ = T/t para una pared de 10 mm.

Ejecutar:  python examples/hoop_tension_cylindrical_tank_W01046_500kN_per_m.py
"""
from plantstruct.tanks import hoop_tension

H, R, GAMMA = 10.0, 5.0, 10_000.0  # m, m, N/m³
T_MM = 10.0


def main() -> None:
    print(f"Depósito H = {H:.0f} m, r = {R:.0f} m, γ = {GAMMA / 1000:.0f} kN/m³")
    print(f"  {'cota y [m]':>10} {'T [kN/m]':>9} {'T con p = 20 kPa [kN/m]':>24} {'σ = T/t (t = 10 mm) [MPa]':>26}")
    for y in (0.0, 2.5, 5.0, 7.5, 10.0):
        T = hoop_tension(R, H, GAMMA, elevation_m=y) / 1000.0
        Tp = hoop_tension(R, H, GAMMA, elevation_m=y, internal_pressure_kPa=20.0) / 1000.0
        print(f"  {y:10.1f} {T:9.1f} {Tp:24.1f} {Tp / T_MM:26.1f}")
    T_base = hoop_tension(R, H, GAMMA)
    print(f"\nFicha W01046: T_base = γ·H·r = {GAMMA:.0f}·{H:.0f}·{R:.0f} = {T_base:,.0f} N/m = {T_base / 1000:.0f} kN/m")
    print("Fórmula de membrana: válida lejos del fondo y del techo, donde la restricción de borde añade flexión local.")


if __name__ == "__main__":
    main()
