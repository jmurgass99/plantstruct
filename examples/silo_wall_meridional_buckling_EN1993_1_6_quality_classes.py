"""Pandeo meridional de la pared de un silo (EN 1993-1-6) con la compresión que le transmite el rozamiento del grano.

Silo de trigo D = 6 m, h_c = 18 m, γ = 9 kN/m³, K = 0,54, μ = 0,38. La fuerza vertical por
unidad de perímetro que acumula la pared a profundidad z es la integral del rozamiento:

    n_x(z) = ∫ p_wf dz = μ·γ·K·z_o·[z − z_o·(1 − e^(−z/z_o))]        σ_x = n_x / t

Se compara con la resistencia característica σ_Rk = α·σ_cr (σ_cr = 0,605·E·t/r; α según la
clase de calidad de fabricación A/B/C del Anexo D) y con σ_Rd = σ_Rk/γ_M1, γ_M1 = 1,1, para
t = 4, 5, 6 y 8 mm. Sin clase de calidad la función se niega a asumir una por defecto.

Ejecutar:  python examples/silo_wall_meridional_buckling_EN1993_1_6_quality_classes.py
"""
from math import exp

from plantstruct.silo_buckling import buckling_resistance

D, H_C = 6.0, 18.0
GAMMA, K, MU = 9.0, 0.54, 0.38
E = 210_000.0
GAMMA_M1 = 1.1


def n_x(z: float) -> float:
    z_o = D / (4 * K * MU)
    return MU * GAMMA * K * z_o * (z - z_o * (1 - exp(-z / z_o)))  # kN/m


def main() -> None:
    nx = n_x(H_C)
    print(f"Fuerza meridional en la pared a z = {H_C:.0f} m: n_x = {nx:.1f} kN/m "
          f"(el grano pesa γ·h_c·A/perímetro = {GAMMA * H_C * D / 4:.1f} kN/m; la pared lleva el {nx / (GAMMA * H_C * D / 4) * 100:.0f} %)\n")
    print(f"  {'t [mm]':>6} {'σ_x [MPa]':>9} {'σ_cr [MPa]':>10} {'α_A':>6} {'σ_Rd,A':>7} {'α_B':>6} {'σ_Rd,B':>7} {'α_C':>6} {'σ_Rd,C':>7}  utilización A/B/C")
    for t in (4.0, 5.0, 6.0, 8.0):
        sigma_x = nx / t  # kN/m / mm = MPa
        res = {q: buckling_resistance(E=E, t=t, r=D * 500.0, quality_class=q) for q in "ABC"}
        util = [sigma_x / (res[q]["sigma_Rk"] / GAMMA_M1) for q in "ABC"]
        print(f"  {t:6.0f} {sigma_x:9.2f} {res['A']['sigma_cr']:10.1f} "
              f"{res['A']['alpha']:6.3f} {res['A']['sigma_Rk'] / GAMMA_M1:7.1f} "
              f"{res['B']['alpha']:6.3f} {res['B']['sigma_Rk'] / GAMMA_M1:7.1f} "
              f"{res['C']['alpha']:6.3f} {res['C']['sigma_Rk'] / GAMMA_M1:7.1f}  "
              f"{util[0]:.2f} / {util[1]:.2f} / {util[2]:.2f}")
    try:
        buckling_resistance(E=E, t=6.0, r=3000.0)
    except ValueError as exc:
        print(f"\nSin clase de calidad: ValueError → {str(exc)[:90]}…")
    print("\nSolo el peso del grano no agota la pared; el pandeo meridional lo deciden el viento con el silo vacío, la descarga excéntrica y la clase de fabricación (A frente a C: factor 2,2).")


if __name__ == "__main__":
    main()
