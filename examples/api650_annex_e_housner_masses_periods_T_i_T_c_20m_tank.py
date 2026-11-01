"""Tanque API 650 de 20 m × 15 m: pesos efectivos de Housner, alturas, periodos, cortante y momento (Anexo E).

Agua, manto de espesor uniforme t_u = 8 mm, manto de 16 m. Coeficientes de aceleración ya
reducidos por R_w e I: A_i = 0,30 g, A_c = 0,10 g (§E.4.6.1). El peso del manto y del techo
se estima de la geometría (manto 631 kN a 8 m, techo plano de 5 mm 123 kN a 16 m) y entra en
V y M_rw con A_i.

Comprobación a mano (D/H = 1,333, rama tanh):
    W_i/W_p = tanh(0,866·1,333)/(0,866·1,333) = 0,7096        X_i = 0,375·H = 5,625 m
    W_c/W_p = 0,230·1,333·tanh(2,7525) = 0,3042               X_c/H = 1 − (cosh a − 1)/(a·sinh a) = 0,6803
    T_i = (1/√2000)·(6,06·15/√(8/20))·(√1000/√200000) = 0,227 s      T_c = 1,8·0,5803·√20 = 4,67 s

Hasta la 0.2.0 el paquete daba T_i = 0,006 s (faltaban el 1/√2000 y el √(t_u/D)).

Ejecutar:  python examples/api650_annex_e_housner_masses_periods_T_i_T_c_20m_tank.py
"""
from plantstruct.tanks import TankGeometry, estimate_shell_and_roof_weight_kN, housner_masses

D, H, T_U, H_SHELL = 20.0, 15.0, 8.0, 16.0
A_I, A_C = 0.30, 0.10


def main() -> None:
    g = TankGeometry(D_m=D, H_l_m=H, t_shell_mm=T_U)
    W_shell = 3.141592653589793 * D * H_SHELL * (T_U / 1000.0) * 78.5
    W_roof = estimate_shell_and_roof_weight_kN(D, H_SHELL, T_U) - W_shell
    m = housner_masses(g, A_I, A_C, W_s_kN=W_shell, X_s_m=H_SHELL / 2, W_r_kN=W_roof, X_r_m=H_SHELL)

    print(f"Tanque D = {D:.0f} m, H = {H:.0f} m, t_u = {T_U:.0f} mm, agua: W_p = {g.W_l_kN:,.0f} kN; manto {W_shell:.0f} kN, techo {W_roof:.0f} kN")
    print(f"  W_i = {m.W_i_kN:9,.0f} kN  (W_i/W_p = {m.W_i_kN / g.W_l_kN:.4f})   X_i = {m.h_i_m:.3f} m  (X_i/H = {m.h_i_m / H:.4f})")
    print(f"  W_c = {m.W_c_kN:9,.0f} kN  (W_c/W_p = {m.W_c_kN / g.W_l_kN:.4f})   X_c = {m.h_c_m:.3f} m  (X_c/H = {m.h_c_m / H:.4f})")
    print(f"  T_i = {m.T_i_s:.3f} s  (C_i = {m.C_i:.2f}, H/R = {2 * H / D:.2f})      T_c = {m.T_c_s:.2f} s")
    print(f"  V   = sqrt([A_i·(W_s + W_r + W_i)]² + [A_c·W_c]²) = {m.V_base_kN:,.0f} kN")
    print(f"  M_rw = sqrt([A_i·(W_i·X_i + W_s·X_s + W_r·X_r)]² + [A_c·W_c·X_c]²) = {m.M_overturn_kNm:,.0f} kN·m")
    sin_sc = housner_masses(g, A_I, A_C)
    print(f"\nSin manto ni techo: V = {sin_sc.V_base_kN:,.0f} kN, M_rw = {sin_sc.M_overturn_kNm:,.0f} kN·m "
          f"(la suma lineal daría {A_I * sin_sc.W_i_kN * sin_sc.h_i_m + A_C * sin_sc.W_c_kN * sin_sc.h_c_m:,.0f} kN·m).")
    print("T_i = 0,23 s cae en la meseta del espectro; T_c = 4,7 s está en la rama de periodo largo, de ahí que A_c sea tan pequeño.")


if __name__ == "__main__":
    main()
