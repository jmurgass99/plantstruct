"""Muro antiexplosión como SDOF elastoplástico: demanda de ductilidad en régimen impulsivo y rotación de apoyo.

Muro de hormigón de 250 mm (m = 600 kg/m²), rigidez k = 2·10⁷ Pa/m, resistencia última
R_m = 150 kPa, luz 4 m, ductilidad admisible μ_adm = 3 (UFC 3-340-02, respuesta moderada).
Impulso reflejado de 1 500 Pa·s (sobrepresión pico 200 kPa, informativa).

    x_el = R_m/k = 7,5 mm        μ = 1 + i²/(2·m·R_m·x_el)        θ = atan(x_max/(L/2))

La asíntota impulsiva vale cuando la duración de la carga es mucho menor que el periodo
(T = 2π·sqrt(m/k) = 34 ms aquí). Se barre el impulso hasta ver dónde se pierde el criterio.

Ejecutar:  python examples/blast_wall_sdof_ductility_demand_impulsive_asymptote.py
"""
from math import pi, sqrt

from plantstruct import BunkerIn, design_bunker

M, K, RM, SPAN, MU_ADM = 600.0, 2.0e7, 1.5e5, 4.0, 3.0


def main() -> None:
    T = 2 * pi * sqrt(M / K)
    print(f"Muro: m = {M:.0f} kg/m², k = {K:.1e} Pa/m, R_m = {RM / 1000:.0f} kPa, L = {SPAN:.0f} m, μ_adm = {MU_ADM:.0f}; T = {T * 1000:.1f} ms, x_el = {RM / K * 1000:.1f} mm\n")
    print(f"  {'i [Pa·s]':>8} {'μ':>6} {'x_max [mm]':>10} {'θ apoyo [°]':>11} {'μ/μ_adm':>7} cumple")
    for i in (750.0, 1000.0, 1500.0, 2000.0, 2500.0):
        r = design_bunker(BunkerIn(pr=200e3, impulse=i, m=M, k=K, Rm=RM, mu_allowable=MU_ADM, span=SPAN))
        print(f"  {i:8.0f} {r.mu:6.2f} {r.x_max * 1000:10.1f} {r.support_rotation_deg:11.2f} {r.demand_capacity_ratio:7.2f} {r.passed}")
    r = design_bunker(BunkerIn(impulse=1500.0, m=M, k=K, Rm=RM, mu_allowable=MU_ADM, span=SPAN))
    mu_mano = 1 + 1500.0 ** 2 / (2 * M * RM * (RM / K))
    print(f"\nComprobación a mano para i = 1 500 Pa·s: μ = 1 + i²/(2·m·R_m·x_el) = {mu_mano:.3f} (paquete {r.mu:.3f})")
    print("La duración positiva de la onda debe ser << 34 ms para que valga la asíntota impulsiva; UFC 3-340-02 limita además θ a 2° (respuesta moderada) en hormigón armado.")


if __name__ == "__main__":
    main()
