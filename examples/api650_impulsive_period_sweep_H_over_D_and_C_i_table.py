"""Periodo impulsivo T_i (API 650 §E.4.5.1) y convectivo T_c (§E.4.5.2) para tanques de esbeltez creciente.

Cinco tanques de agua desde H/D = 0,2 (tanque de crudo bajo) hasta 2,0 (torre de agua). El
coeficiente C_i sale de la Fig. E.1 de API 650 (interpolación de la tabla de Malhotra 2000,
que es la misma curva en H/R): vale 9,3 en tanques muy bajos, mínimo 6,06 en H/R = 1,5 y
vuelve a subir en los esbeltos.

    T_i = (1/√2000)·C_i·H/√(t_u/D)·√ρ/√E          T_c = 1,8·K_s·√D,  K_s = 0,578/√tanh(3,68·H/D)

Ejecutar:  python examples/api650_impulsive_period_sweep_H_over_D_and_C_i_table.py
"""
from plantstruct.tanks import TankGeometry, convective_period_s, housner_masses, impulsive_coefficient_Ci, impulsive_period_s

TANQUES = [  # D, H, t_u
    (40.0, 8.0, 10.0), (30.0, 12.0, 10.0), (20.0, 15.0, 8.0), (12.0, 18.0, 8.0), (10.0, 20.0, 8.0),
]


def main() -> None:
    print(f"  {'D [m]':>5} {'H [m]':>5} {'t_u [mm]':>8} {'H/D':>5} {'H/R':>5} {'C_i':>5} {'T_i [s]':>7} {'T_c [s]':>7} {'W_i/W_p':>7} {'W_c/W_p':>7} {'X_c/H':>6}")
    for D, H, t in TANQUES:
        g = TankGeometry(D_m=D, H_l_m=H, t_shell_mm=t)
        m = housner_masses(g, 0.25, 0.08)
        print(f"  {D:5.0f} {H:5.0f} {t:8.0f} {H / D:5.2f} {2 * H / D:5.2f} {impulsive_coefficient_Ci(2 * H / D):5.2f} "
              f"{m.T_i_s:7.3f} {m.T_c_s:7.2f} {m.W_i_kN / g.W_l_kN:7.3f} {m.W_c_kN / g.W_l_kN:7.3f} {m.h_c_m / H:6.3f}")
    assert abs(impulsive_period_s(20.0, 15.0, 8.0) - 0.2272) < 5e-4
    assert abs(convective_period_s(20.0, 15.0) - 4.6715) < 5e-3
    print("\nT_i crece con H/√(t_u/D): un manto más grueso rigidiza y acorta el periodo; el convectivo solo depende de D y H/D.")
    print("Todos los T_i quedan por debajo de ~0,6 s: el impulsivo suele caer en la meseta del espectro y A_i = S_DS·I/R_wi.")


if __name__ == "__main__":
    main()
