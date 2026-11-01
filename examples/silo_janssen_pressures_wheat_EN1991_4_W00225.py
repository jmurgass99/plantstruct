"""Presiones de llenado de Janssen en un silo de trigo (EN 1991-4 §5.2, ficha W00225).

Silo cilíndrico de acero D = 6 m, h_c = 18 m (h_c/d_c = 3: esbelto). Trigo según EN 1991-4
Tabla E.1: γ = 9,0 kN/m³, K = 0,54, μ = 0,38 (pared D2, acero con corrosión ligera).

    z_o = d_c/(4·K·μ) = 6/(4·0,54·0,38) = 7,31 m          p_ho = γ·K·z_o = 35,5 kPa (asíntota)
    p_hf(z) = p_ho·(1 − e^(−z/z_o))      p_vf = p_hf/K      p_wf = μ·p_hf

Se imprime el perfil con la profundidad y se comprueba que `silos_en1991_4.janssen_pressures`
(entrada por ángulo de rozamiento) y `ec1_silos.janssen_pressure` (entrada por μ) coinciden.

Ejecutar:  python examples/silo_janssen_pressures_wheat_EN1991_4_W00225.py
"""
from math import atan, degrees

from plantstruct.ec1_silos import janssen_pressure
from plantstruct.silos_en1991_4 import SiloInput, janssen_pressures

D, H_C = 6.0, 18.0
GAMMA, K, MU = 9.0, 0.54, 0.38


def main() -> None:
    z_o = D / (4 * K * MU)
    print(f"Silo D = {D:.0f} m, h_c = {H_C:.0f} m; trigo γ = {GAMMA} kN/m³, K = {K}, μ = {MU}: z_o = {z_o:.2f} m, p_ho = {GAMMA * K * z_o:.1f} kPa")
    print(f"  {'z [m]':>5} {'p_hf [kPa]':>10} {'p_vf [kPa]':>10} {'p_wf [kPa]':>10} {'p_hf/p_ho':>9}")
    for z in (0.0, 2.0, 4.0, 6.0, 9.0, 12.0, 15.0, 18.0):
        p_h, p_v = janssen_pressure(z, GAMMA, MU, K, D)
        print(f"  {z:5.1f} {p_h:10.2f} {p_v:10.2f} {MU * p_h:10.2f} {p_h / (GAMMA * K * z_o):9.3f}")
    r = janssen_pressures(SiloInput(diameter_m=D, height_filled_m=H_C, bulk_density_kN_m3=GAMMA,
                                    friction_angle_wall_deg=degrees(atan(MU)), K_lateral=K))
    p_h18, p_v18 = janssen_pressure(H_C, GAMMA, MU, K, D)
    print(f"\njanssen_pressures (fondo): p_h = {r.p_horizontal_max_kPa:.3f}, p_v = {r.p_vertical_max_kPa:.3f}, p_w = {r.p_wall_friction_max_kPa:.3f} kPa")
    print(f"janssen_pressure(z = 18):  p_h = {p_h18:.3f}, p_v = {p_v18:.3f} kPa → diferencia {abs(p_h18 - r.p_horizontal_max_kPa):.1e} kPa")
    print(f"\nA 18 m la presión horizontal ya es el {p_h18 / (GAMMA * K * z_o) * 100:.0f} % de la asíntota; la vertical sobre el fondo, "
          f"{p_v18:.0f} kPa, es solo el {p_v18 / (GAMMA * H_C) * 100:.0f} % de γ·h: el resto lo lleva la pared por rozamiento.")


if __name__ == "__main__":
    main()
