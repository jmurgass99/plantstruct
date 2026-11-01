"""Esfera de GLP: espesor mínimo del casco (ASME VIII Div. 1 UG-32), carga por columna y cortante basal preliminar.

Esfera de propano D = 20 m, presión de diseño 17,5 bar, llenado 85 %, SA-516 Gr. 70 a 38 °C
(S = 138 MPa), eficiencia de junta E = 1,0 radiografiada, 10 columnas:

    t = P·R / (2·S·E − 0,2·P) = 1,75·10 000 / (2·138·1,0 − 0,35) = 63,5 mm

Se compara con una esfera de 14 m y con el coeficiente sísmico preliminar por código
(C_s = 0,20 en US/CO y 0,15 en EU/AU/SG). Es una verificación de anteproyecto: sin
sobreespesor de corrosión, sin tolerancia de laminación y sin el peso de columnas y tirantes.

Ejecutar:  python examples/lpg_sphere_asme_viii_thickness_columns_and_base_shear.py
"""
from plantstruct.esferas_gpl import EsferaGLPInput, disenar_esfera


def main() -> None:
    print(f"  {'D [m]':>5} {'P [bar]':>7} {'código':>6} {'t_min [mm]':>10} {'W_total [kN]':>12} {'P columna [kN]':>14} {'V_basal [kN]':>12}")
    for D, P in ((20.0, 17.5), (14.0, 18.0)):
        for code in ("US", "EU"):
            r = disenar_esfera(EsferaGLPInput(D_m=D, P_design_bar=P, n_columnas=10 if D == 20.0 else 8, code=code))
            print(f"  {D:5.0f} {P:7.1f} {code:>6} {r.t_min_mm:10.1f} {r.W_total_kN:12,.0f} {r.P_col_kN:14,.0f} {r.V_basal_kN:12,.0f}")
    r = disenar_esfera(EsferaGLPInput(D_m=20.0, P_design_bar=17.5, n_columnas=10))
    t_mano = 1.75 * 10_000 / (2 * 138.0 * 1.0 - 0.2 * 1.75)
    print(f"\nComprobación UG-32 a mano para D = 20 m: t = {t_mano:.1f} mm (paquete {r.t_min_mm:.1f} mm)")
    print("El peso total es líquido al 85 % más el casco de espesor t_min; el cortante basal es C_s·W, un coeficiente de criba, no un espectro.")


if __name__ == "__main__":
    main()
