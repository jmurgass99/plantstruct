"""Pernos de anclaje: carga por perno, capacidad y número necesario para tres disposiciones (API 650 §E.6.2.1.2).

Tanque de agua D = 20 m, H = 15 m, t_u = 8 mm, A_i = 0,15 g, A_c = 0,05 g, manto 631 kN y
techo 123 kN; W_t = 900 kN incluye accesorios. Carga por perno:

    P_AB = (4·M_rw/D − W_t) / N_b          capacidad = 0,6·F_y·A_b (más conservadora que el 0,8·F_y de la norma)

Disposiciones: 24 × M30 F_y 250 (A36), 48 × M36 F_y 250, 32 × M36 F_y 400 (ASTM A449).

Ejecutar:  python examples/api650_anchor_bolts_uplift_per_bolt_and_required_count.py
"""
from plantstruct.tanks import AnchorageInput, TankGeometry, check_anchorage, housner_masses

D, H, T_U = 20.0, 15.0, 8.0
W_T = 900.0
DISPOSICIONES = [(24, 30.0, 250.0), (48, 36.0, 250.0), (32, 36.0, 400.0)]


def main() -> None:
    g = TankGeometry(D_m=D, H_l_m=H, t_shell_mm=T_U)
    m = housner_masses(g, 0.15, 0.05, W_s_kN=631.0, X_s_m=8.0, W_r_kN=123.0, X_r_m=16.0)
    print(f"M_rw = {m.M_overturn_kNm:,.0f} kN·m, W_t = {W_T:.0f} kN → levantamiento total 4·M/D − W_t = {4 * m.M_overturn_kNm / D - W_T:,.0f} kN\n")
    print(f"  {'N_b':>4} {'perno':>6} {'F_y [MPa]':>9} {'P_AB [kN]':>9} {'cap. [kN]':>9} {'DCR':>6} seguro  {'N_b mínimo':>10}")
    for n, db, fy in DISPOSICIONES:
        r = check_anchorage(AnchorageInput(D_m=D, W_tank_kN=W_T, M_overturn_kNm=m.M_overturn_kNm,
                                           n_bolts=n, bolt_diameter_mm=db, bolt_Fy_MPa=fy))
        print(f"  {n:4d} {'M' + str(int(db)):>6} {fy:9.0f} {r.F_uplift_per_bolt_kN:9.1f} {r.F_allowable_per_bolt_kN:9.1f} {r.DCR:6.2f} {str(r.is_safe):>6}  {r.n_bolts_required_min:10d}")
    print("\nW_tank_kN es el peso de manto + techo + accesorios: con el peso del líquido en su lugar el levantamiento sale cero y el anclaje «cumple» sin calcular nada.")


if __name__ == "__main__":
    main()
