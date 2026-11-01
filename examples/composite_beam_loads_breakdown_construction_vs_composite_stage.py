"""Desglose de cargas de una viga mixta: fase constructiva (acero solo, hormigón fresco) frente a fase mixta, apuntalada o no.

W460x74 a 9 m cada 3 m, losa 130/50 mm, 1,5 kPa superpuesta, 7,5 kPa de uso y un equipo en
centro de vano de 50 kN (muerta) + 80 kN (viva). `calculate_industrial_mezzanine_loads`
devuelve las cargas lineales, las combinaciones (AISC: 1,2D + 1,6L y 1,4D en construcción
con 1,0 kPa de sobrecarga de obra; EN 1990: 1,35G + 1,5Q) y los esfuerzos de cada fase.
Apuntalar anula los esfuerzos constructivos sobre el acero solo.

Ejecutar:  python examples/composite_beam_loads_breakdown_construction_vs_composite_stage.py
"""
from plantstruct import IndustrialMezzanineDemand, SteelBeamProfile, calculate_industrial_mezzanine_loads

W460X74 = SteelBeamProfile(name="W460x74", d_mm=457.0, bf_mm=190.0, tf_mm=14.5, tw_mm=9.0,
                           A_mm2=9460.0, Ix_mm4=333e6, Zx_mm3=1660e3, Fy_MPa=345.0)
CLAVES = ["w_dead_construction_kN_m", "w_dead_total_kN_m", "w_live_kN_m", "q_u_const_kN_m", "q_u_comp_kN_m",
          "M_u_const_kNm", "V_u_const_kN", "M_u_comp_kNm", "V_u_comp_kN"]


def main() -> None:
    casos = [
        ("AISC, sin apuntalar", dict(standard="AISC_360_16", shored_construction=False)),
        ("AISC, apuntalada", dict(standard="AISC_360_16", shored_construction=True)),
        ("EN 1990/1994, sin apuntalar", dict(standard="EUROCODE_4", shored_construction=False)),
    ]
    resultados = []
    for nombre, kw in casos:
        d = IndustrialMezzanineDemand(span_m=9.0, spacing_m=3.0, dead_load_superimposed_kpa=1.5, live_load_kpa=7.5,
                                      slab_thickness_mm=130.0, deck_height_mm=50.0, point_load_dead_kN=50.0, point_load_live_kN=80.0, **kw)
        resultados.append((nombre, calculate_industrial_mezzanine_loads(d, W460X74)))
    print(f"  {'magnitud':28}" + "".join(f"{n:>28}" for n, _ in resultados))
    for k in CLAVES:
        print(f"  {k:28}" + "".join(f"{r[k]:28.1f}" for _, r in resultados))
    print(f"\nPeso propio del perfil: {W460X74.self_weight_kN_per_m:.3f} kN/m (estimado de A·78,5 kN/m³); losa: espesor eficaz (t − h_deck/2)·s·24 kN/m³ + 0,15 kPa de chapa.")
    print("La carga puntual en centro de vano añade P·L/4 al momento y P/2 al cortante de la fase mixta.")


if __name__ == "__main__":
    main()
