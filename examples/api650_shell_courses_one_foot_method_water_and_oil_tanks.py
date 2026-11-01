"""Espesor de cada virola por el método del pie (API 650 §5.6.3.2) en dos tanques reales.

Tanque A: agua, D = 20 m, H = 15 m, seis virolas de 2,5 m, acero A36 (S_d = 160 MPa,
S_t = 171 MPa, Tabla 5-2a), sobreespesor de corrosión 1,5 mm.
Tanque B: crudo (G = 0,90), D = 36 m, H = 18 m, ocho virolas de 2,25 m, A573M-485
(S_d = 193 MPa, S_t = 208 MPa), CA = 3,0 mm. Con D >= 36 m el mínimo nominal de la
Tabla 5.6a sube a 8 mm.

    t_d = 4,9·D·(H − 0,3)·G/S_d + CA        t_t = 4,9·D·(H − 0,3)/S_t

donde H es la altura de líquido sobre el fondo de la virola. El espesor requerido es el
mayor de t_d, t_t y el mínimo nominal, y `governing` dice cuál manda.

Ejecutar:  python examples/api650_shell_courses_one_foot_method_water_and_oil_tanks.py
"""
from plantstruct.tanks import shell_thickness_one_foot

TANQUES = [
    ("A — agua, A36, CA 1,5 mm", 20.0, 15.0, 2.5, 1.0, 160.0, 171.0, 1.5),
    ("B — crudo G 0,90, A573M-485, CA 3 mm", 36.0, 18.0, 2.25, 0.90, 193.0, 208.0, 3.0),
]


def main() -> None:
    for nombre, D, H, h_virola, G, Sd, St, CA in TANQUES:
        print(f"Tanque {nombre}: D = {D:.0f} m, H = {H:.0f} m")
        print(f"  {'virola':>6} {'H sobre fondo [m]':>18} {'t_d [mm]':>9} {'t_t [mm]':>9} {'t_min [mm]':>10} {'t_req [mm]':>10}  manda")
        n = round(H / h_virola)
        for i in range(n):
            h = H - i * h_virola
            r = shell_thickness_one_foot(D_m=D, H_m=h, G=G, Sd_MPa=Sd, St_MPa=St, CA_mm=CA)
            print(f"  {i + 1:>6} {h:18.2f} {r.t_design_mm:9.2f} {r.t_test_mm:9.2f} {r.t_min_nominal_mm:10.1f} "
                  f"{r.t_required_mm:10.2f}  {r.governing}")
        print()
    print("La prueba hidrostática (G = 1, sin CA) solo manda cuando el líquido es ligero y el CA pequeño; "
          "en las virolas altas manda el mínimo nominal por diámetro.")


if __name__ == "__main__":
    main()
