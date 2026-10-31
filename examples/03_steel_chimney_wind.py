"""Chimenea metálica autoportante: evaluación bajo viento.

Chimenea de 40 m de altura, 2,5 m de diámetro exterior y manto de 10 mm, con
velocidad básica de viento de 30 m/s. Se evalúa con el módulo de chimeneas y
se repite para tres velocidades para ver la sensibilidad.

Ejecutar:  python examples/03_steel_chimney_wind.py
"""
from dataclasses import asdict

from plantstruct.chimneys import ChimneyInput, evaluate_chimney


def main() -> None:
    base = ChimneyInput(D_outer_m=2.5, H_m=40.0, t_shell_mm=10.0, Vb_m_per_s=30.0)
    res = evaluate_chimney(base)
    print("Chimenea 40 m, D = 2,5 m, t = 10 mm, V_b = 30 m/s:")
    for k, v in asdict(res).items():
        print(f"  {k:<26} {v}")

    print("\nSensibilidad a la velocidad básica:")
    for vb in (26.0, 30.0, 36.0, 42.0):
        r = evaluate_chimney(ChimneyInput(D_outer_m=2.5, H_m=40.0, t_shell_mm=10.0, Vb_m_per_s=vb))
        nums = [f"{k} = {v:.4g}" for k, v in asdict(r).items() if isinstance(v, (int, float))][:4]
        print(f"  V_b = {vb:4.0f} m/s → " + ", ".join(nums))


if __name__ == "__main__":
    main()
