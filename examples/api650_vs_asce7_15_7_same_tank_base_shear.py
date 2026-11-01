"""El mismo tanque por API 650 Anexo E y por ASCE 7-22 §15.7.6: pesos, periodos y cortante basal.

Tanque de agua D = 20 m, H = 15 m, t_u = 8 mm, manto 631 kN y techo 123 kN. Espectro de diseño
S_DS = 1,0 g, S_D1 = 0,6 g, categoría de riesgo III (I_e = 1,25), anclado mecánicamente.

- ASCE 7-22: R_i = 3, R_c = 1,5; S_ai = S_DS (T_i en la meseta); S_ac = 1,5·S_D1/T_c <= 1,5·S_DS.
- API 650: R_wi = 4, R_wc = 2; A_i = S_DS·I/R_wi; A_c = K·S_D1/T_c·I/R_wc con K = 1,5 (T_c <= T_L).

Las fracciones de Housner y T_c coinciden (misma fuente, ACI 350.3); la diferencia en V viene
de los factores R, que no son los mismos en las dos normas.

Ejecutar:  python examples/api650_vs_asce7_15_7_same_tank_base_shear.py
"""
from plantstruct.asce7_15_7 import TankASCEInput, asce_15_7
from plantstruct.tanks import TankGeometry, housner_masses

D, H, T_U = 20.0, 15.0, 8.0
W_S, W_R = 631.0, 123.0
SDS, SD1, IE = 1.0, 0.6, 1.25


def main() -> None:
    a = asce_15_7(TankASCEInput(D_m=D, H_l_m=H, Sds=SDS, Sd1=SD1, Ie=IE, Ri=3.0, Rc=1.5,
                                t_shell_mm=T_U, W_s_kN=W_S, W_r_kN=W_R))
    g = TankGeometry(D_m=D, H_l_m=H, t_shell_mm=T_U)
    A_i = SDS * IE / 4.0
    T_c = a.Tc_s
    A_c = 1.5 * SD1 / T_c * IE / 2.0
    p = housner_masses(g, A_i, A_c, W_s_kN=W_S, X_s_m=8.0, W_r_kN=W_R, X_r_m=16.0)

    print(f"{'':28} {'ASCE 7-22 §15.7':>16} {'API 650 Anexo E':>16}")
    print(f"{'W_i [kN]':28} {a.Wi_kN:16,.0f} {p.W_i_kN:16,.0f}")
    print(f"{'W_c [kN]':28} {a.Wc_kN:16,.0f} {p.W_c_kN:16,.0f}")
    print(f"{'T_i [s]':28} {a.Ti_s:16.3f} {p.T_i_s:16.3f}")
    print(f"{'T_c [s]':28} {a.Tc_s:16.3f} {p.T_c_s:16.3f}")
    print(f"{'aceleración impulsiva [g]':28} {a.Sai_g * IE / 3.0:16.4f} {A_i:16.4f}   (S_ai·I_e/R_i frente a A_i = S_DS·I/R_wi)")
    print(f"{'aceleración convectiva [g]':28} {a.Sac_g * IE / 1.5:16.4f} {A_c:16.4f}   (S_ac·I_e/R_c frente a A_c)")
    print(f"{'V_i [kN]':28} {a.Vi_kN:16,.0f} {A_i * (p.W_i_kN + W_S + W_R):16,.0f}")
    print(f"{'V_c [kN]':28} {a.Vc_kN:16,.0f} {A_c * p.W_c_kN:16,.0f}")
    print(f"{'V = sqrt(V_i² + V_c²) [kN]':28} {a.V_total_kN:16,.0f} {p.V_base_kN:16,.0f}")
    print(f"\nRelación V_ASCE/V_API = {a.V_total_kN / p.V_base_kN:.2f}: es R_wi/R_i = 4/3 en el término impulsivo, que domina.")
    print("S_ac lleva el tope 1,5·S_DS; con T_c = 4,7 s está muy por debajo y manda 1,5·S_D1/T_c.")


if __name__ == "__main__":
    main()
