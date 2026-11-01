"""Clase de esbeltez del silo (EN 1991-4 §1.5.31-33) y factores de descarga C_h, C_w (§5.3, Tabla 5.2).

Cuatro silos de 6 m de diámetro con la misma arena (γ = 16 kN/m³, K = 0,45, μ = 0,45) y
alturas de 18, 9, 4 y 2 m: esbelto (h_c/d_c >= 2), intermedio (1–2), achaparrado (0,4–1) y
depósito de retención (< 0,4). Para cada uno: presión de llenado en el fondo y presión de
descarga p_he = C_h·p_hf; en los esbeltos e intermedios C_h = 1,15 y C_w = 1,10 (clase de
evaluación 2), en los achaparrados 1,0.

Ejecutar:  python examples/silo_slenderness_classes_and_discharge_factors_C_h_C_w.py
"""
from plantstruct.ec1_silos import discharge_pressure_factors, janssen_pressure, silo_slenderness_class

D = 6.0
GAMMA, K, MU = 16.0, 0.45, 0.45


def main() -> None:
    print(f"  {'h_c [m]':>7} {'h_c/d_c':>7} {'clase':>12} {'C_h':>5} {'C_w':>5} {'p_hf fondo [kPa]':>16} {'p_he = C_h·p_hf':>15} {'p_we = C_w·μ·p_hf':>17}")
    for h_c in (18.0, 9.0, 4.0, 2.0):
        cls = silo_slenderness_class(h_c, D)
        C_h, C_w = discharge_pressure_factors(cls)
        p_h, _ = janssen_pressure(h_c, GAMMA, MU, K, D)
        print(f"  {h_c:7.1f} {h_c / D:7.2f} {cls:>12} {C_h:5.2f} {C_w:5.2f} {p_h:16.2f} {C_h * p_h:15.2f} {C_w * MU * p_h:17.2f}")
    print("\nLa clase decide también la carga parcheada (§5.2.4) y si aplica el canal de flujo (Anexo G): ver el caso siguiente.")
    print("Los C_h/C_w son los valores recomendados de la Tabla 5.2 para clase de evaluación 2; la clase 3 exige el cálculo detallado de §5.3.2.")


if __name__ == "__main__":
    main()
