"""Cuántos pernos hacen falta: capacidad a flexión, flecha y modo gobernante de la W460x74 según el número de conectores (AISC 360-16 Cap. I).

Mismo entrepiso del caso AISC (9 m, 3 m, 7,5 kPa). Se fija `num_studs_total` en 16, 24, 32,
48 y 64 pernos de 19 mm y se compara con el automático. Con pocos pernos el grado de conexión
baja, φM_n cae hacia el del perfil solo y la flecha sube (I_eff con sqrt(ΣQ_n/C_f)); el modo
gobernante pasa de flecha a flexión.

Ejecutar:  python examples/composite_beam_stud_count_sensitivity_and_governing_mode.py
"""
from plantstruct import IndustrialMezzanineDemand, SteelBeamProfile, design_industrial_composite_beam

W460X74 = SteelBeamProfile(name="W460x74", d_mm=457.0, bf_mm=190.0, tf_mm=14.5, tw_mm=9.0,
                           A_mm2=9460.0, Ix_mm4=333e6, Zx_mm3=1660e3, Fy_MPa=345.0)


def main() -> None:
    demand = IndustrialMezzanineDemand(span_m=9.0, spacing_m=3.0, dead_load_superimposed_kpa=1.5, live_load_kpa=7.5,
                                       slab_thickness_mm=130.0, deck_height_mm=50.0, concrete_f_c_MPa=28.0, standard="AISC_360_16")
    print(f"  {'pernos':>6} {'paso [mm]':>9} {'φM_n [kN·m]':>11} {'DCR flexión':>11} {'flecha L [mm]':>13} {'DCR flecha L':>12} {'viable':>6}  gobierna")
    for n in (16, 24, 32, 48, 64, None):
        r = design_industrial_composite_beam(demand, W460X74, num_studs_total=n)
        print(f"  {r.num_studs_total:6d} {r.stud_spacing_mm:9.0f} {r.moment_capacity_kNm:11.1f} {r.dcr_flexure_composite:11.2f} "
              f"{r.deflection_live_mm:13.1f} {r.dcr_deflection_live:12.2f} {str(r.is_viable):>6}  {r.governing_mode}{' (automático)' if n is None else ''}")
        if r.diagnostics and n in (16, None):
            for d in r.diagnostics[:2]:
                print("         ·", d[:120])
    print("\nAISC 360-16 §I3.2d exige ΣQ_n >= 0,25·min(A_s·F_y, 0,85·f'c·A_c) salvo justificación; por debajo la viga ya no es mixta a efectos de cálculo.")


if __name__ == "__main__":
    main()
