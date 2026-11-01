"""Límite del método del pie (D <= 60 m) y cómo la memoria lo declara en vez de aprobar en silencio.

API 650 §5.6.3.2 limita el método del pie a D <= 60 m; por encima hay que usar el método del
punto de diseño variable (§5.6.4). `shell_thickness_one_foot` lanza ValueError y
`render_tank_memo` convierte esa excepción en un paso «NO CALCULADO» con `is_ok = None` y
un veredicto global NO CUMPLE: antes devolvía t_requerido = 0 e is_ok = True, es decir, un
aprobado fabricado justo en los tanques grandes.

Tanque de 66 m × 20 m de crudo con manto de 12 mm, A_i = 0,20 g, A_c = 0,06 g.

Ejecutar:  python examples/one_foot_method_limit_D_over_60m_and_memo_not_evaluated.py
"""
from plantstruct.memos import TankMemoInput, render_tank_memo
from plantstruct.tanks import shell_thickness_one_foot


def main() -> None:
    try:
        shell_thickness_one_foot(D_m=66.0, H_m=20.0, G=0.9)
    except ValueError as exc:
        print(f"shell_thickness_one_foot(D = 66 m) → ValueError: {exc}\n")

    r = render_tank_memo(TankMemoInput(D_m=66.0, H_l_m=20.0, H_shell_m=21.0, t_shell_mm=12.0,
                                       Sa_i_g=0.20, Sa_c_g=0.06, n_bolts=48, bolt_diameter_mm=36.0,
                                       rho_l_kg_m3=900.0, liquid_G=0.9))
    print("shell_thickness en la memoria:", r.shell_thickness)
    print("is_safe:", r.is_safe)
    print("\nFragmento de la memoria (Paso 2 y Resultado):")
    for linea in r.markdown.splitlines():
        if "Paso 2" in linea or "NO CALCULADO" in linea or "VERIFICACION GLOBAL" in linea or linea.startswith("- Espesor"):
            print("  ", linea)
    print("\nCon D = 60 m el método sí aplica:")
    r60 = shell_thickness_one_foot(D_m=60.0, H_m=20.0, G=0.9, Sd_MPa=193.0, St_MPa=208.0, CA_mm=3.0)
    print(f"  t_d = {r60.t_design_mm:.1f} mm, t_t = {r60.t_test_mm:.1f} mm, mínimo nominal {r60.t_min_nominal_mm:.0f} mm → t_req = {r60.t_required_mm:.1f} mm ({r60.governing})")


if __name__ == "__main__":
    main()
