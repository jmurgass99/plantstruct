"""Sensibilidad de la presión de Janssen a K y μ, y coherencia de las dos rutinas del paquete.

El paquete tiene dos entradas a Janssen: `silos_en1991_4.janssen_pressures` (ángulo de
rozamiento con la pared) y `ec1_silos.janssen_pressure` (μ directo). Se comprueba que dan lo
mismo con μ = tan φ_w y se tabula la presión horizontal en el fondo de un silo D = 8 m,
h_c = 20 m, γ = 16 kN/m³ para K ∈ {0,40; 0,50; 0,60} y μ ∈ {0,25; 0,40; 0,55}: EN 1991-4
exige combinar los valores característicos superiores e inferiores de K y μ (Tabla 3.1)
porque la presión horizontal máxima sale con K alto y μ bajo, y la fricción con μ alto.

Ejecutar:  python examples/silo_two_implementations_consistency_and_K_mu_sensitivity.py
"""
from math import atan, degrees

from plantstruct.ec1_silos import janssen_pressure
from plantstruct.silos_en1991_4 import SiloInput, janssen_pressures

D, H_C, GAMMA = 8.0, 20.0, 16.0


def main() -> None:
    peor = 0.0
    for K in (0.40, 0.50, 0.60):
        for mu in (0.25, 0.40, 0.55):
            a = janssen_pressures(SiloInput(D, H_C, GAMMA, degrees(atan(mu)), K))
            b_h, b_v = janssen_pressure(H_C, GAMMA, mu, K, D)
            peor = max(peor, abs(a.p_horizontal_max_kPa - b_h), abs(a.p_vertical_max_kPa - b_v))
    print(f"Mayor diferencia entre las dos rutinas sobre las 9 combinaciones: {peor:.1e} kPa\n")
    print(f"p_hf en el fondo [kPa] (filas K, columnas μ)      y      p_wf = μ·p_hf [kPa]")
    print(f"  {'K \\ μ':>6} {0.25:>8} {0.40:>8} {0.55:>8}      {0.25:>8} {0.40:>8} {0.55:>8}")
    for K in (0.40, 0.50, 0.60):
        ph = [janssen_pressure(H_C, GAMMA, mu, K, D)[0] for mu in (0.25, 0.40, 0.55)]
        pw = [mu * p for mu, p in zip((0.25, 0.40, 0.55), ph)]
        print(f"  {K:6.2f} {ph[0]:8.1f} {ph[1]:8.1f} {ph[2]:8.1f}      {pw[0]:8.1f} {pw[1]:8.1f} {pw[2]:8.1f}")
    print("\nLa presión horizontal máxima aparece con K = 0,60 y μ = 0,25; la fricción máxima (y con ella la compresión de la pared) con μ = 0,55.")
    print("Por eso la norma pide combinaciones distintas para dimensionar los anillos y para dimensionar la pared a compresión.")


if __name__ == "__main__":
    main()
