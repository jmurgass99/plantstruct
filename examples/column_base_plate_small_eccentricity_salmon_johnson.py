"""Placa base de pilar con excentricidad pequeña (e <= N/6): dimensiones y espesor por Salmon & Johnson / AISC DG1.

Pilar HEB 300 (b_f = 300, d = 300 mm) con P = 1 500 kN de compresión, V = 60 kN y M = 50 kN·m;
placa S235 (f_y = 235 MPa), hormigón f'c = 30 MPa, 4 pernos M24, μ = 0,40.

    f_p,max = φ_c·0,85·f'c       A_req = P/f_p,max       e = M/P = 33 mm <= N/6 → toda la placa comprimida
    t = l·sqrt(2·f_p/(0,9·f_y)) con l = max(m, n) y m = (N − 0,95·d)/2, n = (B − 0,8·b_f)/2

Sin tracción en los pernos (T_u = 0) el anclaje no tiene demanda y la fricción 0,4·P = 600 kN
cubre el cortante: no hace falta llave.

Ejecutar:  python examples/column_base_plate_small_eccentricity_salmon_johnson.py
"""
from plantstruct.bases_columna import BaseColumnaInput, disenar_base


def main() -> None:
    r = disenar_base(BaseColumnaInput(P_kN=1500.0, V_kN=60.0, M_kNm=50.0, bf_mm=300.0, d_mm=300.0,
                                      fy_MPa=235.0, fc_MPa=30.0, fyb_MPa=420.0, n_anchors=4, db_anchor_mm=24.0, mu_friction=0.40))
    print(f"Placa: N = {r.N_mm:.0f} mm, B = {r.B_mm:.0f} mm, t = {r.t_mm:.1f} mm; e = M/P = {r.e_mm:.1f} mm (N/6 = {r.N_mm / 6:.1f} mm)")
    print(f"Tracción en pernos T_u = {r.Tu_anchor_kN:.1f} kN → modo: {r.anchor_tension.governing_mode}, is_ok = {r.anchor_tension.is_ok}")
    print(f"Llave de cortante requerida: {r.shear_lug.required} (V = {r.shear_lug.shear_demand_kN:.0f} kN, fricción μ·P = {r.shear_lug.shear_friction_capacity_kN:.0f} kN)")
    print(f"Estado: {r.verification_status}, cumple = {r.cumple}")
    print("\nNotas del resultado:")
    for n in r.notes:
        print("  -", n[:150] + ("…" if len(n) > 150 else ""))


if __name__ == "__main__":
    main()
