# Limitaciones conocidas de plantstruct

Lo que el paquete no hace o hace de forma simplificada.

- `Sa_i` y `Sa_c` son los coeficientes A_i y A_c ya divididos por R_w/I: el paquete no construye el espectro de API 650 §E.4.6 a partir de S_S, S_1 y clase de sitio.
- El momento volcante es el de la base del manto (ringwall): no incluye la presión sobre el fondo (M_s de §E.6.1.5-2) ni el peso del fondo.
- `check_anchorage` usa 0,6·F_y como capacidad del perno (la norma admite 0,8·F_y) y `check_anchorage_J` dimensiona la silleta con fórmulas simplificadas. La longitud de levantamiento L de §E.6.2.1.1.2 está en `tanks.anchorage.self_anchored_uplift_length_api650` (no se exporta en `plantstruct.tanks`); el espesor t_a no se comprueba.
- El pandeo axial del manto es α·E·t/R con α = 0,6. F_C de §E.6.2.2.3 se calcula si se pasa `Fy_MPa` a `ShellBucklingFullInput`, pero es informativo: no entra en el veredicto. El knockdown de Rotter se publica pero no gobierna.
- `asce7_15_7` toma T_i = 0 si no se da el espesor y no evalúa S_ai por encima de T_L; los factores R son entrada.
- `chimneys`, `esferas_gpl` y `pipe_rack` son predimensionamiento con coeficientes sísmicos de criba (C_s fijo por código), sin espectro.
- `portal_frame.check_steel_member_interaction` usa por defecto k_y = min(1 + 0,6·n, 1,4), equivalente a la Tabla B.1 con C_my = 1 y λ̄_y = 0,8 fijos (subestima k_yy en pilares más esbeltos y lo declara en `k_y_basis`); con `lambda_y` (y `C_my`) aplica la Tabla B.1, Método 2, Clases 1-2.
- `bases_columna`: por defecto la capacidad del acero del perno es fluencia sobre área bruta; con `futa_MPa` y `Ase_N_mm2` usa A_se·f_uta de §17.6.1.2. La llave de cortante tiene altura y espesor fijos; con P ≤ 0 no se deriva la demanda de tracción. `check_anchor_shear_aci318_17_7` (§17.7 e interacción 5/3 de §17.8) no lo llama `disenar_base` y simplifica: el cono de V_cp (N_cbg de §17.6.2) supone una malla ⌈√n⌉ × ⌈n/⌈√n⌉⌉ con separación `s_anchor_mm` y el lado opuesto a c_a1 libre (sin `s_anchor_mm`, un solo cono: cota inferior); A_Vc no incluye la separación entre anclajes y no hay ψ_h,V. Hasta 0c7e004 V_cp usaba n·N_b (12 veces más en el caso de placa).
- `anchor_codes` cubre solo el cono de un anclaje sin bordes multiplicado por el número de anclajes.
- Las vigas mixtas suponen vano simple, carga uniforme más una puntual en el centro, chapa perpendicular con una línea de pernos; la flecha con conexión parcial usa la aproximación de AISC I3.2 también en la rama EN 1994.
- `report_api650` es un esqueleto de secciones del Anexo E, no un informe calculado: la memoria calculada es `memos.render_tank_memo`.
