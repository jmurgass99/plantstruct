"""Modelo de barra («stick») de Housner para SAP2000 y malla paramétrica del manto, sin abrir SAP.

`build_housner_stick_model` traduce las masas de API 650 Anexo E a un modelo de masas
concentradas: la impulsiva rígida a X_i y la convectiva colgada de un resorte horizontal
k_c = m_c·ω_c² a X_c, de modo que el análisis modal reproduce T_c. `FastSAPTankBuilder` en
modo `dry_run` genera los nudos y las áreas del manto (n_circ × n_vert) sin cliente COM.

Tanque D = 20 m, H_l = 15 m, t = 8 mm, A_i = 0,30 g, A_c = 0,10 g; malla 24 × 8.

Ejecutar:  python examples/housner_stick_model_for_sap2000_and_parametric_shell_mesh.py
"""
from math import pi

from plantstruct.integration.fastsap_tank_parametric import FastSAPTankBuilder, TankParametric, build_housner_stick_model
from plantstruct.tanks import TankGeometry

G = 9.80665


def main() -> None:
    geom = TankGeometry(D_m=20.0, H_l_m=15.0, t_shell_mm=8.0)
    model = build_housner_stick_model(geom, Sa_i=0.30, Sa_c=0.10)
    print("Nudos:")
    for n in model["nodes"]:
        print(f"  {n['name']:>4}  z = {n['z']:6.3f} m  restricción = {n['restraint']}")
    print("Masas [kN·s²/m]:")
    for m in model["masses"]:
        print(f"  {m['node']:>4}  m = {m['mass']:9.1f}  ({m['note']})")
    s = model["convective_spring"]
    m_c = next(m["mass"] for m in model["masses"] if m["node"] == "CONV")
    T_c = 2 * pi * (m_c / s["k_kN_m"]) ** 0.5
    print(f"Resorte convectivo: k_c = {s['k_kN_m']:.1f} kN/m en {s['node']} → T = 2π·sqrt(m_c/k_c) = {T_c:.3f} s (T_c de Housner = {s['T_c_s']:.3f} s)")
    print("Resumen sísmico:", {k: round(v, 3) for k, v in model["seismic"].items()})

    mesh = FastSAPTankBuilder(dry_run=True).build(TankParametric(D_m=20.0, H_m=16.0, n_circ=24, n_vert=8, t_shell_mm=8.0))
    print(f"\nMalla del manto: {len(mesh['joints'])} nudos ({25} anillos × 24), {len(mesh['shells'])} áreas de 4 nudos; dry_run = {mesh['dry_run']}")
    print("  primera área:", mesh["shells"][0])
    print("Para ejecutar contra SAP2000 real se pasa el objeto SapModel como `client`; los fallos de AddByPoint se devuelven en `failed`, no se tragan.")


if __name__ == "__main__":
    main()
