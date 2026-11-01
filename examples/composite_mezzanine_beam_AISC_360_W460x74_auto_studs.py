"""Viga mixta de entrepiso industrial por AISC 360-16 Cap. I: W460x74 a 9 m con conectores dimensionados automáticamente.

Entrepiso de almacén con sobrecarga de uso de 7,5 kPa (estanterías) y 1,5 kPa de cargas
muertas superpuestas (instalaciones, protección al fuego), vigas cada 3 m, losa de 130 mm sobre
chapa colaborante de 50 mm, hormigón f'c = 28 MPa, construcción sin apuntalar. Perfil
W460x74 (A992, F_y = 345 MPa). Si no se da `num_studs_total` el módulo estima los pernos de
19 mm para interacción completa (ΣQ_n >= A_s·F_y) y comprueba flexión y cortante en fase
constructiva y mixta y las flechas L/360 y L/240.

Ejecutar:  python examples/composite_mezzanine_beam_AISC_360_W460x74_auto_studs.py
"""
from plantstruct import IndustrialMezzanineDemand, SteelBeamProfile, design_industrial_composite_beam

W460X74 = SteelBeamProfile(name="W460x74", d_mm=457.0, bf_mm=190.0, tf_mm=14.5, tw_mm=9.0,
                           A_mm2=9460.0, Ix_mm4=333e6, Zx_mm3=1660e3, Fy_MPa=345.0)


def main() -> None:
    demand = IndustrialMezzanineDemand(span_m=9.0, spacing_m=3.0, dead_load_superimposed_kpa=1.5, live_load_kpa=7.5,
                                       slab_thickness_mm=130.0, deck_height_mm=50.0, concrete_f_c_MPa=28.0,
                                       shored_construction=False, standard="AISC_360_16")
    r = design_industrial_composite_beam(demand, W460X74)
    print(r.summary_markdown())
    print(f"\nM_u = {r.applied_moment_kNm:.1f} kN·m frente a φM_n = {r.moment_capacity_kNm:.1f} kN·m; V_u = {r.applied_shear_kN:.1f} kN frente a φV_n = {r.shear_capacity_kN:.1f} kN")
    print(f"Flecha de sobrecarga {r.deflection_live_mm:.1f} mm (L/360 = {9000 / 360:.0f} mm); total {r.deflection_total_mm:.1f} mm (L/240 = {9000 / 240:.1f} mm)")
    print(f"Viable: {r.is_viable}; gobierna {r.governing_mode} con DCR {r.governing_dcr:.2f}")


if __name__ == "__main__":
    main()
