"""Nave industrial: presión de pico del viento por categoría de terreno y flexocompresión del pilar (EN 1993-1-1 §6.3.3).

Presión de pico q_p(z) = c_e(z)·q_b con q_b = ½·ρ·v_b² para v_b = 26 m/s a z = 8 m (alero) en
las cinco categorías de terreno de EN 1991-1-4 Tabla 4.1 (0, I, II, III, IV).

Pilar IPE 400 S275 (A = 8 446 mm², W_el,y = 1 156·10³ mm³) con N_Ed = 250 kN y M_y,Ed = 180 kN·m,
χ_y = 0,80 y χ_LT = 0,85 obligatorios (no se asumen por defecto). La función declara en
`k_y_basis` que su k_y = min(1 + 0,6·n, 1,4) equivale a la Tabla B.1 con C_my = 1 y λ̄_y = 0,8
fijos: para pilares más esbeltos subestima k_yy. También se muestra que rechaza tracción y χ = 0.

Ejecutar:  python examples/portal_frame_wind_pressure_terrain_categories_and_member_interaction_IPE400.py
"""
from plantstruct.portal_frame import calculate_wind_pressure, check_steel_member_interaction

V_B, Z = 26.0, 8.0
IPE400 = dict(A_mm2=8446.0, Wel_y_mm3=1_156_000.0, fyi_MPa=275.0)


def main() -> None:
    print(f"q_b = ½·1,25·{V_B:.0f}² = {0.5 * 1.25 * V_B ** 2 / 1000:.3f} kPa; q_p(z = {Z:.0f} m) por categoría de terreno:")
    for cat in ("0", "I", "II", "III", "IV"):
        print(f"  categoría {cat:>3}: q_p = {calculate_wind_pressure(V_B, Z, cat):.3f} kPa")

    r = check_steel_member_interaction(N_Ed_kN=250.0, My_Ed_kNm=180.0, chi_y=0.80, chi_LT=0.85, **IPE400)
    print(f"\nIPE 400 S275, N_Ed = 250 kN, M_y,Ed = 180 kN·m, χ_y = 0,80, χ_LT = 0,85:")
    for k in ("member_compression_capacity_kN", "member_bending_capacity_kNm", "axial_utilization", "bending_utilization",
              "interaction_coefficient_ky", "combined_interaction_ratio", "status"):
        v = r[k]
        print(f"  {k:32} {v:.3f}" if isinstance(v, float) else f"  {k:32} {v}")
    print(f"  k_y_basis: {r['k_y_basis'][:120]}…")

    for kw, titulo in ((dict(N_Ed_kN=-300.0, My_Ed_kNm=180.0, chi_y=0.8, chi_LT=0.85), "tracción"),
                       (dict(N_Ed_kN=250.0, My_Ed_kNm=180.0, chi_y=None, chi_LT=0.85), "χ_y ausente")):
        try:
            check_steel_member_interaction(**kw, **IPE400)
        except ValueError as exc:
            print(f"\n{titulo}: ValueError → {str(exc)[:110]}…")


if __name__ == "__main__":
    main()
