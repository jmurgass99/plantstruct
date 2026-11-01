"""Presión exterior (vacío) sobre el manto: presión crítica, factor de seguridad por norma y separación de rigidizadores.

Tanque D = 20 m, t = 8 mm, 5 m entre rigidizadores, acero E = 200 000 MPa. Vacío de diseño
de 1,0 kPa (≈ 100 mm de columna de agua, el habitual en tanques con venteo) y de 2,5 kPa.

    P_cr = 2,6·E·(t/D)^2,5 / (L/D − 0,45·sqrt(t/D))      (ASME VIII Div. 1 UG-28 / API 650 §5.9.7, cilindro corto)

El factor de seguridad exigido depende del código: 3,0 en USA/ASME, NSR-10 y AS; 1,5 en EN
14015 / EN 1993-1-6 y BC 1 (Singapur). `max_unstiffened_length_m` invierte la fórmula para dar
la distancia máxima entre rigidizadores que cumple el factor.

Ejecutar:  python examples/external_pressure_vacuum_stiffener_spacing_by_code.py
"""
from plantstruct.external_pressure import ExtPressureInput, critical_external_pressure, max_unstiffened_length_m

D, T, L = 20.0, 8.0, 5.0


def main() -> None:
    print(f"D = {D:.0f} m, t = {T:.0f} mm, L = {L:.0f} m entre rigidizadores\n")
    print(f"  {'P_ext [kPa]':>11} {'código':>6} {'P_cr [kPa]':>10} {'FS':>6} {'FS req.':>7} cumple  {'L_max sin rigidizar [m]':>24}")
    for P in (1.0, 2.5):
        for code in ("USA", "EU", "CO", "AU", "SG"):
            r = critical_external_pressure(ExtPressureInput(D_m=D, t_mm=T, L_m=L, P_ext_kPa=P, code=code))
            Lmax = max_unstiffened_length_m(D, T, P, code=code)
            print(f"  {P:11.1f} {code:>6} {r.P_cr_kPa:10.2f} {r.factor_of_safety:6.2f} {r.required_FS:7.1f} {str(r.passes):>6}  {Lmax:24.2f}")
        print()
    print("Con 2,5 kPa y FS = 3 el manto de 8 mm necesita rigidizadores cada ~2,8 m; con FS = 1,5 bastan ~5,7 m.")
    print("La fórmula es la del cilindro corto entre rigidizadores; no cubre el pandeo general con techo ni la combinación con viento.")


if __name__ == "__main__":
    main()
