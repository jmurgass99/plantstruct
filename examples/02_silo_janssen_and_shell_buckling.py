"""Silo de acero: presiones de Janssen (EN 1991-4) y pandeo meridional del manto.

Silo cilíndrico de 6 m de diámetro y 18 m de altura de llenado con cemento.
Se obtienen las presiones de Janssen y después se comprueba la resistencia a
pandeo del manto para tres espesores y dos clases de calidad de fabricación.

Ejecutar:  python examples/02_silo_janssen_and_shell_buckling.py
"""
from dataclasses import asdict

from plantstruct import silo_buckling
from plantstruct.silos_en1991_4 import SiloInput, janssen_pressures

E = 210_000.0   # MPa


def main() -> None:
    silo = SiloInput(diameter_m=6.0, height_filled_m=18.0, bulk_density_kN_m3=16.0, friction_angle_wall_deg=25.0, K_lateral=0.40)
    res = janssen_pressures(silo)
    print("Presiones de Janssen (EN 1991-4):")
    for k, v in asdict(res).items():
        print(f"  {k:<28} {v}")

    r_mm = silo.diameter_m * 1000.0 / 2.0
    print("\nPandeo meridional del manto (EN 1993-1-6, enfoque simplificado):")
    print(f"  {'t [mm]':>6} {'clase':>8} {'σ_cr [MPa]':>11} {'α':>7} {'resultado'}")
    for t in (6.0, 8.0, 10.0):
        for quality in ("A", "B", "C"):
            sig_cr = silo_buckling.meridional_critical_stress(E, t, r_mm)
            alpha = silo_buckling.imperfection_alpha(r_mm, t, quality)
            br = silo_buckling.buckling_resistance(E, t, r_mm, quality_class=quality)
            print(f"  {t:6.1f} {quality:>8} {sig_cr:11.1f} {alpha:7.3f} {br}")


if __name__ == "__main__":
    main()
