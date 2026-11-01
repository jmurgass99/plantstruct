"""Llave de cortante: cuándo hace falta y qué capacidad tiene (AISC Design Guide 1 / Salmon & Johnson).

Pilar HEB 300 con P = 600 kN, V = 180 kN y M = 85 kN·m sobre hormigón f'c = 25 MPa con
μ = 0,20 (lámina de neopreno o lechada pobre): la fricción 0,2·600 = 120 kN no cubre los
180 kN y el módulo exige llave. Es el caso del test golden del paquete.

La llave tiene ancho atado a la placa y altura 75 mm y espesor 25 mm FIJOS del módulo (no se
dimensionan: `dims_source` lo repite en el resultado); se comprueban aplastamiento del
hormigón φ_c·0,85·f'c·(w·h) y cortante de la chapa φ_v·0,6·f_y·(w·t). Con μ = 0,40 la fricción
basta y la llave no se requiere.

Ejecutar:  python examples/column_base_shear_lug_required_when_friction_insufficient.py
"""
from plantstruct.bases_columna import BaseColumnaInput, disenar_base


def main() -> None:
    for mu in (0.20, 0.40):
        r = disenar_base(BaseColumnaInput(P_kN=600.0, V_kN=180.0, M_kNm=85.0, bf_mm=200.0, d_mm=300.0,
                                          fy_MPa=250.0, fc_MPa=25.0, fyb_MPa=420.0, n_anchors=4, db_anchor_mm=25.0, mu_friction=mu))
        s = r.shear_lug
        print(f"μ = {mu:.2f}: fricción μ·P = {s.shear_friction_capacity_kN:.0f} kN frente a V = {s.shear_demand_kN:.0f} kN → llave requerida: {s.required}")
        if s.required:
            print(f"  llave {s.lug_width_mm:.0f} × {s.lug_height_mm:.0f} × {s.lug_thickness_mm:.0f} mm: aplastamiento {s.bearing_capacity_kN:.0f} kN, cortante chapa {s.shear_capacity_kN:.0f} kN → is_ok = {s.is_ok}")
        print(f"  placa N = {r.N_mm:.0f}, B = {r.B_mm:.0f}, t = {r.t_mm:.1f} mm; T_u = {r.Tu_anchor_kN:.1f} kN; estado {r.verification_status}, cumple = {r.cumple}\n")
    print("dims_source:", r.shear_lug.dims_source[:140] + "…")


if __name__ == "__main__":
    main()
