"""Viga mixta por EN 1994-1-1: IPE 450 S355 a 8 m con conexión parcial y el mínimo de §6.6.1.2.

Entrepiso de equipos con sobrecarga 5,0 kPa y 1,2 kPa de cargas muertas superpuestas, vigas
cada 2,5 m, losa 130/50 mm, C25/30 (f_ck = 25 MPa). Primero con 24 pernos de 19 mm (12 por
semivano): el grado de conexión η = N_c/min(N_pl,a, N_cf) queda por debajo del mínimo
η_min = max(0,40; 1 − (355/f_y)·(0,75 − 0,03·L_e)) y el módulo lo avisa y no da la viga por
viable aunque los DCR cumplan. Después sin fijar pernos: el módulo pone los necesarios para
conexión completa.

    M_Rd = M_pl,a,Rd + η·(M_pl,Rd − M_pl,a,Rd)      (ec. 6.28, interacción parcial)

Ejecutar:  python examples/composite_mezzanine_beam_EN1994_IPE450_partial_interaction.py
"""
from plantstruct import IndustrialMezzanineDemand, SteelBeamProfile, design_industrial_composite_beam

IPE450 = SteelBeamProfile(name="IPE 450 S355", d_mm=450.0, bf_mm=190.0, tf_mm=14.6, tw_mm=9.4,
                          A_mm2=9880.0, Ix_mm4=337.4e6, Zx_mm3=1702e3, Fy_MPa=355.0)


def main() -> None:
    demand = IndustrialMezzanineDemand(span_m=8.0, spacing_m=2.5, dead_load_superimposed_kpa=1.2, live_load_kpa=5.0,
                                       slab_thickness_mm=130.0, deck_height_mm=50.0, concrete_f_c_MPa=25.0,
                                       standard="EUROCODE_4")
    for studs in (24, None):
        r = design_industrial_composite_beam(demand, IPE450, num_studs_total=studs)
        print(f"=== num_studs_total = {studs if studs else 'automático'} → {r.num_studs_total} pernos ({r.num_studs_half_span} por semivano, paso {r.stud_spacing_mm:.0f} mm) ===")
        print(f"  M_Ed = {r.applied_moment_kNm:.1f} kN·m, M_Rd = {r.moment_capacity_kNm:.1f} kN·m → DCR {r.dcr_flexure_composite:.2f}; "
              f"V_Ed = {r.applied_shear_kN:.1f} kN, V_Rd = {r.shear_capacity_kN:.1f} kN → DCR {r.dcr_shear_composite:.2f}")
        print(f"  flecha sobrecarga {r.deflection_live_mm:.1f} mm (DCR {r.dcr_deflection_live:.2f}), total {r.deflection_total_mm:.1f} mm (DCR {r.dcr_deflection_total:.2f})")
        print(f"  viable = {r.is_viable}; gobierna {r.governing_mode} ({r.governing_dcr:.2f})")
        for d in r.diagnostics:
            print("  ·", d)
        print()
    print("La flecha con interacción parcial usa I_eff = I_a + sqrt(η)·(I_tr − I_a), la aproximación de AISC I3.2; EN 1994 no la prescribe y hay que confirmarla con el método del fabricante de la chapa.")


if __name__ == "__main__":
    main()
