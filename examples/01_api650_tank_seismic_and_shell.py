"""Tanque API 650: espesores del manto por el método del pie, masas sísmicas y anclaje.

Tanque de agua D = 20 m, H = 15 m, acero A36 (S_d = 160 MPa, S_t = 171 MPa),
sobreespesor de corrosión 1,5 mm. Se calculan los espesores de las virolas,
las masas impulsiva y convectiva de Housner (API 650 §E.6.1) y se comprueba
el anclaje con pernos.

Ejecutar:  python examples/01_api650_tank_seismic_and_shell.py
"""
from dataclasses import asdict

from plantstruct.tanks import (
    AnchorageInput,
    TankGeometry,
    check_anchorage,
    housner_masses,
    shell_thickness_one_foot,
)

D, H = 20.0, 15.0
COURSE_H = 2.5   # altura de virola [m]


def main() -> None:
    print("Espesores por el método del pie (API 650 §5.6.3.2):")
    print(f"  {'virola':>6} {'H bajo fondo':>13} {'resultado'}")
    n_courses = int(H / COURSE_H)
    for i in range(n_courses):
        h_from_bottom = H - i * COURSE_H          # altura de líquido sobre el fondo de la virola
        r = shell_thickness_one_foot(D_m=D, H_m=h_from_bottom, G=1.0, Sd_MPa=160.0, St_MPa=171.0, CA_mm=1.5)
        print(f"  {i + 1:>6} {h_from_bottom:13.2f} {asdict(r)}")

    geom = TankGeometry(D_m=D, H_l_m=H, t_shell_mm=8.0)
    m = housner_masses(geom, Sa_i=0.30, Sa_c=0.10)
    print(f"\nMasas de Housner (Sa_i = 0,30 g, Sa_c = 0,10 g):")
    print(f"  peso del líquido      W_l = {geom.W_l_kN:10.0f} kN")
    print(f"  impulsiva W_i = {m.W_i_kN:10.0f} kN a h_i = {m.h_i_m:.2f} m, T_i = {m.T_i_s:.3f} s")
    print(f"  convectiva W_c = {m.W_c_kN:10.0f} kN a h_c = {m.h_c_m:.2f} m, T_c = {m.T_c_s:.2f} s")
    print(f"  momento volcante M = {m.M_overturn_kNm:10.0f} kN·m")

    W_tank = geom.W_l_kN + 1500.0   # líquido + manto/techo (estimado)
    anc = check_anchorage(AnchorageInput(D_m=D, W_tank_kN=W_tank, M_overturn_kNm=m.M_overturn_kNm,
                                         n_bolts=24, bolt_diameter_mm=30.0, bolt_Fy_MPa=250.0))
    print("\nAnclaje (24 pernos M30, F_y = 250 MPa):")
    for k, v in asdict(anc).items():
        print(f"  {k:<24} {v}")


if __name__ == "__main__":
    main()
