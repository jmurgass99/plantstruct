"""Carga parcheada de llenado (EN 1991-4 §5.2.4) y presión en el canal de flujo (Anexo G) en un silo esbelto.

Silo de trigo D = 6 m, h_c = 18 m (esbelto), γ = 9 kN/m³, K = 0,54, μ = 0,38. La carga
parcheada son dos presiones opuestas ±p_pf sobre una banda de altura s = π·d_c/16 ≈ 1,2 m:
p_pf = C_pf·p_ho(z)·0,21 con C_pf = 0,5 en silos esbeltos. En descarga másica, el canal de
flujo reduce la presión sobre la pared: p_hce = p_hf·(1 − 0,1·e^(−z/z_o)) (G = 0,1, ec. G.7).

Ejecutar:  python examples/silo_patch_load_and_flow_funnel_slender_silo.py
"""
from math import pi

from plantstruct.ec1_silos import flow_pressure_funnel, janssen_pressure, patch_load, silo_slenderness_class

D, H_C = 6.0, 18.0
GAMMA, K, MU = 9.0, 0.54, 0.38


def main() -> None:
    cls = silo_slenderness_class(H_C, D)
    z_o = D / (4 * K * MU)
    print(f"Silo h_c/d_c = {H_C / D:.1f} → {cls}; z_o = {z_o:.2f} m; banda de la carga parcheada s = π·d_c/16 = {pi * D / 16:.2f} m")
    print(f"  {'z [m]':>5} {'p_hf [kPa]':>10} {'±p_pf [kPa]':>11} {'p_pf/p_hf':>9} {'p_hce canal [kPa]':>17} {'reducción':>9}")
    for z in (3.0, 6.0, 9.0, 12.0, 15.0, 18.0):
        p_h, _ = janssen_pressure(z, GAMMA, MU, K, D)
        p_pf, p_pf_op = patch_load(z, D, cls, GAMMA, K, z_o)
        p_ce = flow_pressure_funnel(z, H_C, D, GAMMA, MU, K)
        print(f"  {z:5.1f} {p_h:10.2f} {p_pf:11.2f} {p_pf / p_h:9.3f} {p_ce:17.2f} {(1 - p_ce / p_h) * 100:8.1f} %")
        assert p_pf_op == -p_pf
    print("\nLa carga parcheada es la que produce flexión circunferencial en la pared (no la presión simétrica de Janssen);")
    print("en un silo achaparrado C_pf = 0 y el canal de flujo no se aplica (la función devuelve Janssen sin reducir).")
    print(f"Silo achaparrado h_c = 4 m: p_hce = {flow_pressure_funnel(4.0, 4.0, D, GAMMA, MU, K):.2f} kPa = p_hf = {janssen_pressure(4.0, GAMMA, MU, K, D)[0]:.2f} kPa")


if __name__ == "__main__":
    main()
