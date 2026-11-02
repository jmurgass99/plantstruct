"""Manto a compresión y a tracción: pandeo axial API 650, brecha con Rotter según R/t y tracción anular frente a S_d.

Tanque D = 20 m, manto de 16 m, líquido 15 m, con 15 MPa de compresión axial impuesta (techo
y momento sísmico) y 10 MPa de flexión. Se recorre t = 6, 8, 12 y 20 mm.

- Pandeo axial: F_bi = α·E·t/R con α = 0,6 (API 650 §5.10.3). `check_shell_buckling_full`
  publica además `DCR_axial_diamond` con el knockdown de Rotter α_d = 1/(1 + 0,005·R/t); la
  brecha entre ambos es 0,6·(1 + 0,005·R/t): 2,1× a R/t = 500 y 5,6× a R/t = 1667. El veredicto
  `is_safe` va por la ruta API 650 (`axial_basis`); la otra se imprime para no perderla de vista.
- Tracción anular: σ_hoop = γ·H·D/(2·t) frente a la admisible S_d = 160 MPa (A36). Es tracción,
  no pandeo: hasta la 0.2.0 se comparaba con la tensión crítica a presión exterior (2–4 MPa) y
  cualquier tanque lleno daba DCR de 40 a 150.

Ejecutar:  python examples/shell_buckling_basic_vs_full_rotter_gap_vs_R_over_t.py
"""
from plantstruct.tanks import (
    ShellBucklingFullInput,
    ShellBucklingInput,
    check_shell_buckling,
    check_shell_buckling_full,
)
from plantstruct.tanks.shell_buckling import api650_allowable_shell_buckling_stress_fc
import math

D, H_SHELL, H_LIQ = 20.0, 16.0, 15.0
SIGMA_AX, SIGMA_B = 15.0, 10.0


def main() -> None:
    print(f"D = {D:.0f} m, H_manto = {H_SHELL:.0f} m, H_líquido = {H_LIQ:.0f} m, σ_axial = {SIGMA_AX} MPa, σ_flexión = {SIGMA_B} MPa, S_d = 160 MPa\n")
    print(f"  {'t [mm]':>6} {'R/t':>6} {'Fbi API [MPa]':>13} {'DCR_ax':>7} {'α_Rotter':>8} {'DCR_ax,Rotter':>13} {'brecha':>7} {'σ_hoop [MPa]':>12} {'DCR_hoop':>8} {'DCR_flex':>8} {'manda':>12} seguro")
    for t in (6.0, 8.0, 12.0, 20.0):
        b = check_shell_buckling(ShellBucklingInput(D, H_SHELL, H_LIQ, t, sigma_axial_imposed_MPa=SIGMA_AX))
        f = check_shell_buckling_full(ShellBucklingFullInput(D, H_SHELL, H_LIQ, t,
                                                             sigma_axial_imposed_MPa=SIGMA_AX, sigma_bending_MPa=SIGMA_B))
        Rt = D * 500.0 / t
        print(f"  {t:6.0f} {Rt:6.0f} {f.Fbi_axial_MPa:13.1f} {f.DCR_axial:7.3f} "
              f"{f.alpha_diamond:8.3f} {f.DCR_axial_diamond:13.3f} {f.DCR_axial_diamond / f.DCR_axial:7.2f} "
              f"{f.sigma_hoop_demand_MPa:12.1f} {f.DCR_hoop:8.3f} {f.DCR_bending:8.3f} {f.governing_mode:>12} {f.is_safe}")
        assert abs(b.DCR_axial - f.DCR_axial) < 1e-12 and abs(b.DCR_hoop - f.DCR_hoop) < 1e-12
    print(f"\n`axial_basis` = {f.axial_basis}: el veredicto usa α = 0,6; la columna de Rotter es la otra lectura de la misma demanda.")
    print("Con 6 y 8 mm manda la tracción anular (σ_hoop > S_d: hace falta el espesor del método del pie, 10,5 mm en la primera virola); "
          "con 12 y 20 mm el manto cumple y el axial queda holgado por la ruta API, no tanto por la de Rotter.")

    print("\nF_C de API 650 §E.6.2.2.3 (sísmico, con F_y = 250 MPa; informativo: no entra en el veredicto):")
    for t in (6.0, 8.0, 12.0, 20.0):
        f = check_shell_buckling_full(ShellBucklingFullInput(D, H_SHELL, H_LIQ, t, sigma_axial_imposed_MPa=SIGMA_AX,
                                                             sigma_bending_MPa=SIGMA_B, Fy_MPa=250.0))
        ghd = H_LIQ * D ** 2 / t ** 2
        hand = 83 * t / D if ghd >= 44 else 83 * t / (2.5 * D) + 7.5 * math.sqrt(H_LIQ)
        print(f"  t = {t:4.0f} mm: G·H·D²/t² = {ghd:6.1f} → F_C = {f.Fc_api650_e6223_MPa:5.1f} MPa (a mano {min(hand, 125.0):5.1f}); "
              f"σ_axial/F_C = {SIGMA_AX / f.Fc_api650_e6223_MPa:.2f}")
    assert abs(api650_allowable_shell_buckling_stress_fc(D, 12.0, H_LIQ, 250.0) - (83 * 12 / (2.5 * D) + 7.5 * math.sqrt(H_LIQ))) < 1e-9


if __name__ == "__main__":
    main()
