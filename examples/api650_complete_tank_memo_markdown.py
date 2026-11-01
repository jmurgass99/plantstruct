"""Memoria completa de un tanque API 650 Anexo E en un paso: geometría, Housner, espesor, anclaje, pandeo y veredicto.

Tanque de agua D = 20 m, H_l = 15 m, manto de 16 m y 10 mm, 48 pernos M36, A_i = 0,15 g,
A_c = 0,05 g (sismicidad moderada: S_DS = 0,6 g con I/R_wi = 1/4). El peso de manto + techo se estima de la geometría (no se da `W_tank_kN`), el
anillo de fondo se toma igual al manto y A_v = 0,14 g. La memoria sale en Markdown y en
diccionarios por sección; `is_safe` solo es True si espesor, anclaje y pandeo cumplen y el
espesor se ha podido calcular.

Ejecutar:  python examples/api650_complete_tank_memo_markdown.py
"""
from plantstruct.memos import TankMemoInput, render_tank_memo


def main() -> None:
    r = render_tank_memo(TankMemoInput(
        D_m=20.0, H_l_m=15.0, H_shell_m=16.0, t_shell_mm=10.0,
        Sa_i_g=0.15, Sa_c_g=0.05, n_bolts=48, bolt_diameter_mm=36.0, A_v=0.07,
    ))
    print(r.markdown)
    print("Diccionario de anclaje J:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.anchorage_J.items()})
    print("Espesor:", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.shell_thickness.items()})
    print("is_safe:", r.is_safe)


if __name__ == "__main__":
    main()
