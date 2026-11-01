"""Pipe rack de planta: peso total, carga por columna, momento por fricción térmica y cortante basal de anteproyecto.

Rack de dos y tres niveles, tramo de 6 m, ancho 6 m, 5 m entre niveles; tuberías 8 kN/m y
bandejas de cables 2 kN/m por metro de ancho (valores típicos de PIP STC01015 para racks de
proceso). El momento térmico es una estimación de la fricción de las tuberías al dilatar
(0,3·w·L·H) y el cortante basal usa C_s = 0,15 (US/CO) o 0,10 (EU). Todo es de anteproyecto:
sirve para predimensionar columnas y zapatas antes del modelo.

Ejecutar:  python examples/pipe_rack_loads_thermal_moment_and_base_shear_preliminary.py
"""
from plantstruct.pipe_rack import PipeRackInput, evaluar_pipe_rack


def main() -> None:
    print(f"  {'niveles':>7} {'código':>6} {'térmico':>7} {'W_total [kN]':>12} {'W/columna [kN]':>14} {'M_térmico [kN·m]':>16} {'V_basal [kN]':>12}")
    for n in (2, 3):
        for code in ("US", "EU"):
            for th in (True, False):
                r = evaluar_pipe_rack(PipeRackInput(n_niveles=n, L_tramo_m=6.0, B_rack_m=6.0, H_nivel_m=5.0,
                                                    w_tuberias_kN_m=8.0, w_cable_tray_kN_m=2.0, incluir_thermal=th, code=code))
                print(f"  {n:7d} {code:>6} {str(th):>7} {r.W_total_kN:12,.0f} {r.W_por_columna_kN:14,.0f} {r.M_termico_kNm:16,.0f} {r.cortante_basal_kN:12,.0f}")
    print("\nEl reparto es a cuatro columnas por módulo; el peso de la propia estructura y las cargas de viento y amarre de tuberías no están incluidos.")


if __name__ == "__main__":
    main()
