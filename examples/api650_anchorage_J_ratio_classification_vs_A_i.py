"""Relación de anclaje J (API 650 §E.6.2.1.1.1): de autoanclado a anclaje mecánico al crecer la aceleración.

Tanque de agua D = 20 m, H = 15 m, manto 16 m de 8 mm, anillo de fondo t_a = 8 mm en acero
F_y = 250 MPa. Peso de manto + techo W_t = 755 kN → w_t = 12,0 kN/m; fuerza resistente del
anillo w_a = 99·t_a·√(F_y·H·G_e) = 48,5 kN/m (tope 201,1·H·D·G_e = 60,3 kN/m).

    J = M_rw / (D²·[w_t·(1 − 0,4·A_v) + w_a − 0,4·w_int])
    J <= 0,785 autoanclado · 0,785 < J <= 1,54 autoanclado con levantamiento · J > 1,54 anclaje mecánico

Se barre A_i de 0,05 a 0,40 g con A_c = 0,4·A_i y A_v = 0,47·A_i (§E.6.1.3 con S_DS). Hasta la
0.2.0 el paquete dividía por el peso total (factor π·D = 63) y todo salía «autoanclado».

Ejecutar:  python examples/api650_anchorage_J_ratio_classification_vs_A_i.py
"""
from plantstruct.tanks import (
    AnchorageJInput,
    TankGeometry,
    annulus_resisting_force_kN_m,
    check_anchorage_J,
    estimate_shell_and_roof_weight_kN,
    housner_masses,
)
from plantstruct.tanks.anchorage import self_anchored_uplift_length_api650

D, H, T_U, H_SHELL = 20.0, 15.0, 8.0, 16.0


def main() -> None:
    g = TankGeometry(D_m=D, H_l_m=H, t_shell_mm=T_U)
    W_t = estimate_shell_and_roof_weight_kN(D, H_SHELL, T_U)
    print(f"W_t (manto + techo) = {W_t:.0f} kN → w_t = {W_t / (3.141592653589793 * D):.1f} kN/m")
    print(f"  {'A_i [g]':>7} {'A_v [g]':>7} {'w_a [kN/m]':>10} {'M_rw [kN·m]':>11} {'J':>6} {'tipo':>22} {'F_p [kN]':>9} {'pernos M36':>10}")
    for A_i in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40):
        A_c, A_v = 0.4 * A_i, 0.47 * A_i
        m = housner_masses(g, A_i, A_c, W_s_kN=W_t - 123.3, X_s_m=8.0, W_r_kN=123.3, X_r_m=16.0)
        G_e = 1.0 - 0.4 * A_v
        w_a = annulus_resisting_force_kN_m(T_U, 250.0, H, G_e, D)
        r = check_anchorage_J(AnchorageJInput(D_m=D, M_rw_kNm=m.M_overturn_kNm, W_t_kN=W_t, w_a_kN_m=w_a, A_v=A_v,
                                              bolt_diameter_mm=36.0, bolt_Fy_MPa=250.0))
        print(f"  {A_i:7.2f} {A_v:7.3f} {w_a:10.1f} {m.M_overturn_kNm:11,.0f} {r.J:6.3f} {r.anchorage_type:>22} {r.Fp_kN:9,.0f} {r.N_bolts_required:10d}")
    print("\nCon A_i >= 0,15 g el tanque ya necesita anclaje mecánico; entre 0,05 y 0,10 g es autoanclado con levantamiento y hay que comprobar L y t_a (§E.6.2.1.1.2).")
    for A_i in (0.05, 0.10):
        G_e = 1.0 - 0.4 * 0.47 * A_i
        L = self_anchored_uplift_length_api650(T_U, 250.0, H, G_e, D)
        print(f"  A_i = {A_i:.2f} g: L = 0,01723·t_a·√(F_y/(H·G_e)) = {L['L_uplift_m']:.3f} m "
              f"(a mano {0.01723 * T_U * (250.0 / (H * G_e)) ** 0.5:.3f}); límite 0,035·D = {L['L_max_0035D_m']:.2f} m → "
              f"{'dentro' if L['within_0035D_limit'] else 'FUERA: hace falta engrosar el anillo'}")
    print("F_p = 4·M_rw/D − W_t·(1 − 0,4·A_v) es el levantamiento total para anclaje mecánico (§E.6.2.1.2); el número de pernos usa φ·A_b·F_y.")


if __name__ == "__main__":
    main()
