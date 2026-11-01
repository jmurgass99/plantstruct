"""Base con tracción neta (levantamiento): el módulo no dimensiona la placa por aplastamiento y lo dice.

Pilar de arriostramiento con P = −150 kN (tracción), V = 90 kN y M = 40 kN·m. Sin compresión
no hay área de aplastamiento que dimensione la placa (t = None), la excentricidad M/P pierde
sentido (e = None), la fricción es μ·0 = 0 kN y el módulo no deriva la demanda de tracción de
los pernos bajo levantamiento: devuelve NO_VERIFICADO, `cumple = False` y las dimensiones en
planta mínimas por contorno de columna (d + 100, b_f + 100), que no son un dimensionamiento.

Ejecutar:  python examples/column_base_uplift_P_le_0_honest_not_verified.py
"""
from plantstruct.bases_columna import BaseColumnaInput, disenar_base


def main() -> None:
    r = disenar_base(BaseColumnaInput(P_kN=-150.0, V_kN=90.0, M_kNm=40.0, bf_mm=200.0, d_mm=200.0, n_anchors=4, db_anchor_mm=24.0))
    print(f"N = {r.N_mm:.0f} mm, B = {r.B_mm:.0f} mm (mínimo por contorno), t = {r.t_mm}, e = {r.e_mm}, T_u = {r.Tu_anchor_kN}")
    print(f"fricción = {r.shear_lug.shear_friction_capacity_kN:.0f} kN → llave requerida: {r.shear_lug.required}, is_ok = {r.shear_lug.is_ok}")
    print(f"anclaje: is_ok = {r.anchor_tension.is_ok}, missing_inputs = {list(r.anchor_tension.missing_inputs)}")
    print(f"verification_status = {r.verification_status}, cumple = {r.cumple}\n")
    for n in r.notes:
        print("-", n[:160] + ("…" if len(n) > 160 else ""))


if __name__ == "__main__":
    main()
