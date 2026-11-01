"""Chimenea metálica autoportante: frecuencia propia, velocidad crítica de desprendimiento de vórtices y banda de riesgo.

Chimenea de 40 m, D = 2,5 m, t = 10 mm, viento básico V_b = 26 m/s (EN 1991-1-4 Anexo E y
§7.13; DIN EN 13084). Primer modo del tubo empotrado: f_1 = (1,875²/2π)·sqrt(E·I/(m·H⁴)) con
I = π·D³·t/8 y m = π·D·t·ρ, de modo que f_1 no depende de t (I/m = D²/(8ρ)). Velocidad
crítica v_crit = D·f_1/St con St = 0,18; el paquete marca riesgo si 0,5·V_b <= v_crit <= 1,25·V_b.

El módulo está declarado EXPERIMENTAL (`validation_level`): da la condición de resonancia, no
la amplitud (número de Scruton, ec. E.7) ni el amortiguador necesario.

Ejecutar:  python examples/steel_chimney_vortex_shedding_critical_wind_speed.py
"""
from plantstruct.chimneys import ChimneyInput, evaluate_chimney

H, V_B = 40.0, 26.0


def main() -> None:
    base = evaluate_chimney(ChimneyInput(D_outer_m=2.5, H_m=H, t_shell_mm=10.0, Vb_m_per_s=V_B))
    print(f"Chimenea H = {H:.0f} m, D = 2,5 m, t = 10 mm, V_b = {V_B:.0f} m/s ({base.validation_level}):")
    print(f"  f_1 = {base.f1_Hz:.3f} Hz, T_1 = {base.T1_s:.3f} s, v_crit = {base.v_critical_m_per_s:.1f} m/s, "
          f"banda [{0.5 * V_B:.1f}, {1.25 * V_B:.1f}] m/s → en banda: {base.in_vortex_band}, H/D = {base.aspect_ratio:.0f}, peso {base.self_weight_kN_per_m:.2f} kN/m")
    print(f"\n  {'D [m]':>5} {'t [mm]':>6} {'f_1 [Hz]':>8} {'v_crit [m/s]':>12} {'en banda':>8} {'H/D':>5}")
    for D in (1.5, 2.0, 2.5, 3.0):
        for t in (8.0, 12.0):
            r = evaluate_chimney(ChimneyInput(D_outer_m=D, H_m=H, t_shell_mm=t, Vb_m_per_s=V_B))
            print(f"  {D:5.1f} {t:6.0f} {r.f1_Hz:8.3f} {r.v_critical_m_per_s:12.1f} {str(r.in_vortex_band):>8} {r.aspect_ratio:5.1f}")
    print("\nf_1 crece con D/H² y v_crit con D²/H²: a igual altura, las chimeneas anchas salen de la banda por arriba; las de 1,5–2,5 m quedan dentro.")
    print("Que la velocidad crítica esté en la banda no significa que la amplitud sea inadmisible: hace falta el número de Scruton y el amortiguamiento.")


if __name__ == "__main__":
    main()
