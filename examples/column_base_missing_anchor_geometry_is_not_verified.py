"""La misma base con gran excentricidad pero sin la geometría del anclaje: el módulo no aprueba, declara qué falta.

Mismas reacciones que el caso anterior (P = 400 kN, M = 260 kN·m) pero sin h_ef, c_a1, c_a2,
separación ni A_brg. Solo se puede calcular el acero (§17.6.1); los modos del hormigón salen
NO_CALCULADO, `is_ok` es None (nunca True), `cumple` es False y `verification_status` es
NO_VERIFICADO con la lista exacta de `missing_inputs`. Rellenar esos datos con «valores
típicos» fabricaría seguridad; el cono de hormigón suele ser el modo gobernante.

Ejecutar:  python examples/column_base_missing_anchor_geometry_is_not_verified.py
"""
from plantstruct.bases_columna import BaseColumnaInput, disenar_base


def main() -> None:
    r = disenar_base(BaseColumnaInput(P_kN=400.0, V_kN=80.0, M_kNm=260.0, bf_mm=300.0, d_mm=300.0,
                                      fy_MPa=235.0, fc_MPa=30.0, fyb_MPa=420.0, n_anchors=4, db_anchor_mm=24.0))
    a = r.anchor_tension
    print(f"T_u = {a.Tu_kN:.1f} kN; acero nominal {a.steel_capacity_kN:.1f} kN, diseño {a.steel_capacity_design_kN:.1f} kN")
    print(f"cono: {a.concrete_breakout_status}, extracción: {a.pullout_status}, desprendimiento lateral: {a.side_face_blowout_status}")
    print(f"governing_mode = {a.governing_mode}, is_ok = {a.is_ok}")
    print(f"missing_inputs = {list(a.missing_inputs)}")
    print(f"verification_status = {r.verification_status}, cumple = {r.cumple}")
    print("\nNota del módulo:")
    nota = next(n for n in a.notes if n.startswith("NO VERIFICADO"))
    print("  ", nota)
    print("\nCon la geometría completa (caso anterior) el mismo pilar sí obtiene veredicto: la diferencia es solo la información, no la carga.")


if __name__ == "__main__":
    main()
