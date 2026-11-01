"""Arrancamiento del cono de hormigón de un anclaje aislado en tres normas: ACI 318-19, EN 1992-4 y AS 5216.

Anclaje embebido en hormigón f'c = 30 MPa, h_ef = 200, 300 y 400 mm, fisurado y no fisurado,
grupo de 4 anclajes sin interacción de bordes (A_Nc = A_Nco):

    US/CO  N_cb = Ψ_c,N·k_c·√f'c·h_ef^1,5, k_c = 10 (SI), Ψ_c,N = 1,25 no fisurado; φ = 0,65
    EU/SG  N_Rk,c = k_1·√f_ck·h_ef^1,5, k_1 = 7,7 / 11,0; γ_Mc = 1,5
    AU     N_Rk,c = k·√f'c·h_ef^1,5, k = 7,2 / 10,1; γ_M = 1,4

Hasta la 0.2.0 el caso no fisurado US usaba k_c = 17 (el valor en libras-pulgada de los
post-instalados), un 1,7× en vez del 1,25× de Ψ_c,N. Para grupos con bordes y separaciones
use `bases_columna` (A_Nc/A_Nco, Ψ_ed,N).

Ejecutar:  python examples/anchor_concrete_cone_capacity_multi_code_US_EU_AU.py
"""
from plantstruct.anchor_codes import AnchorInput, design_anchor_concrete_cone
from plantstruct.bases_columna import Nb_kN

FC = 30.0


def main() -> None:
    print(f"f'c = {FC:.0f} MPa, 4 anclajes, capacidad de DISEÑO del grupo [kN] (φ·N o N/γ):")
    print(f"  {'h_ef [mm]':>9} {'fisurado':>9} {'US (ACI)':>9} {'EU (EN 1992-4)':>14} {'AU (AS 5216)':>12}")
    for h in (200.0, 300.0, 400.0):
        for cracked in (True, False):
            vals = [design_anchor_concrete_cone(AnchorInput(fc_MPa=FC, h_ef_mm=h, n_anchors=4, cracked_concrete=cracked), code=c).N_design_kN
                    for c in ("US", "EU", "AU")]
            print(f"  {h:9.0f} {str(cracked):>9} {vals[0]:9.1f} {vals[1]:14.1f} {vals[2]:12.1f}")
    us = design_anchor_concrete_cone(AnchorInput(fc_MPa=25.0, h_ef_mm=300.0, n_anchors=1), code="US")
    print(f"\nUn anclaje, f'c = 25, h_ef = 300: N_b = {Nb_kN(25.0, 300.0):.2f} kN (bases_columna) → φ·N_b = {0.65 * Nb_kN(25.0, 300.0):.2f} kN; anchor_codes: {us.N_design_kN:.2f} kN")
    print("EN 1992-4 con k_1 = 7,7 y γ_Mc = 1,5 da capacidades de diseño ~20 % por debajo de ACI con φ = 0,65 para el mismo cono.")


if __name__ == "__main__":
    main()
