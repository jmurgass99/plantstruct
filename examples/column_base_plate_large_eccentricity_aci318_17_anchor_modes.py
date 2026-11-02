"""Placa base con gran excentricidad: tracción en pernos y los cuatro modos de ACI 318-19 §17.6 con geometría completa.

Pilar HEB 300 con P = 400 kN, V = 80 kN y M = 260 kN·m (e = 650 mm >> N/6): la resultante sale
de la placa y los pernos del lado opuesto trabajan a tracción. Con la geometría del anclaje
dada (h_ef = 450 mm, c_a1 = 200, c_a2 = 250, s = 200 mm, A_brg = 1 000 mm², hormigón fisurado,
pernos embebidos) el módulo calcula acero (§17.6.1), arrancamiento del cono (§17.6.2, método
CCD con A_Nc/A_Nco y Ψ_ed,N), extracción (§17.6.3) y desprendimiento lateral (§17.6.4), y
elige el mínimo. N_b = k_c·√f'c·h_ef^1,5 con k_c = 10 en SI: para f'c = 25 y h_ef = 300 da
259,8 kN, la derivación escrita en el módulo.

Ejecutar:  python examples/column_base_plate_large_eccentricity_aci318_17_anchor_modes.py
"""
from plantstruct.bases_columna import BaseColumnaInput, Nb_kN, check_anchor_shear_aci318_17_7, disenar_base


def main() -> None:
    r = disenar_base(BaseColumnaInput(P_kN=400.0, V_kN=80.0, M_kNm=260.0, bf_mm=300.0, d_mm=300.0,
                                      fy_MPa=235.0, fc_MPa=30.0, fyb_MPa=420.0, n_anchors=4, db_anchor_mm=24.0,
                                      hef_mm=450.0, ca1_mm=200.0, ca2_mm=250.0, s_anchor_mm=200.0, Abrg_mm2=1000.0,
                                      cracked_concrete=True, cast_in=True))
    print(f"Placa: N = {r.N_mm:.0f} mm, B = {r.B_mm:.0f} mm, t = {r.t_mm:.1f} mm; e = {r.e_mm:.0f} mm > N/6 = {r.N_mm / 6:.0f} mm → T_u = {r.Tu_anchor_kN:.1f} kN en los 2 pernos traccionados")
    a = r.anchor_tension
    print(f"  {'modo':22} {'nominal [kN]':>12} {'diseño [kN]':>11} estado")
    print(f"  {'acero §17.6.1':22} {a.steel_capacity_kN:12.1f} {a.steel_capacity_design_kN:11.1f} APLICA")
    print(f"  {'cono §17.6.2':22} {a.concrete_breakout_kN:12.1f} {a.concrete_breakout_design_kN:11.1f} {a.concrete_breakout_status}")
    print(f"  {'extracción §17.6.3':22} {a.pullout_kN:12.1f} {a.pullout_design_kN:11.1f} {a.pullout_status}")
    sfb = f"{a.side_face_blowout_kN:12.1f} {a.side_face_blowout_design_kN:11.1f}" if a.side_face_blowout_kN is not None else f"{'—':>12} {'—':>11}"
    print(f"  {'desprendimiento §17.6.4':22} {sfb} {a.side_face_blowout_status}")
    print(f"Gobierna: {a.governing_mode} con {a.governing_capacity_kN:.1f} kN frente a T_u = {a.Tu_kN:.1f} kN → is_ok = {a.is_ok}")
    print(f"Llave de cortante: requerida = {r.shear_lug.required} (fricción {r.shear_lug.shear_friction_capacity_kN:.0f} kN frente a V = {r.shear_lug.shear_demand_kN:.0f} kN)")
    print(f"Estado: {r.verification_status}, cumple = {r.cumple}")
    print(f"\nN_b(f'c = 25 MPa, h_ef = 300 mm) = {Nb_kN(25.0, 300.0):.2f} kN (k_c = 10 SI; con el 24 de libras-pulgada saldría 2,4 veces más)")
    print("Los φ (0,75 acero, 0,70 hormigón) son entrada fija del módulo sin armadura suplementaria.")

    kw = dict(P_kN=400.0, V_kN=80.0, M_kNm=260.0, bf_mm=300.0, d_mm=300.0, fy_MPa=235.0, fc_MPa=30.0, fyb_MPa=420.0,
              n_anchors=4, db_anchor_mm=24.0, hef_mm=450.0, ca1_mm=200.0, ca2_mm=250.0, s_anchor_mm=200.0,
              Abrg_mm2=1000.0, cracked_concrete=True, cast_in=True)
    r2 = disenar_base(BaseColumnaInput(**kw, futa_MPa=620.0, Ase_N_mm2=353.0))
    print(f"\nAcero del perno §17.6.1.2 con A_se,N = 353 mm² (M24) y f_uta = 620 MPa: N_sa = {r2.anchor_tension.steel_capacity_kN:.1f} kN "
          f"(a mano 2·353·620 = {2 * 353 * 620 / 1000:.1f}) frente a {a.steel_capacity_kN:.1f} kN por fluencia sobre el área bruta")
    v = check_anchor_shear_aci318_17_7(Vu_kN=80.0, n_anchors=4, db_anchor_mm=24.0, futa_MPa=620.0, fc_MPa=30.0, hef_mm=450.0,
                                       ca1_mm=200.0, ca2_mm=250.0, Ase_V_mm2=353.0, Tu_kN=r2.Tu_anchor_kN,
                                       phi_Nn_kN=r2.anchor_tension.governing_capacity_kN, s_anchor_mm=200.0, fya_MPa=420.0)
    print("Cortante en anclajes §17.7 si el cortante lo toman los 4 pernos (sin fricción ni llave), V = 80 kN:")
    for k, lbl in (("Vsa_design_kN", "acero φV_sa"), ("Vcb_design_kN", "rotura de borde φV_cb"), ("Vcp_design_kN", "arrancamiento por palanca φV_cp")):
        print(f"  {lbl:31} {v[k]:8.1f} kN")
    print(f"  utilización a cortante {v['shear_utilization']:.2f}; interacción §17.8 (exponente 5/3) {v['interaction_ratio_17_8']:.2f} → is_ok = {v['is_ok']}")
    print(f"  V_cp = k_cp·N_cbg del grupo 2 × 2 (s = 200 mm): A_Nc = {v['ANc_pryout_mm2']:,.0f} mm², N_cbg = {v['Ncpg_kN']:.1f} kN "
          f"(la suma 4·N_b daría {4 * Nb_kN(30.0, 450.0):.0f} kN, sin solape de conos ni bordes). Gobierna la rotura de borde.")


if __name__ == "__main__":
    main()
