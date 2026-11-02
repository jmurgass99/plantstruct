# Changelog

## 0.2.1 — 2026-11-02

- `bases_columna.check_anchor_shear_aci318_17_7` (añadida en 1cc2f67): el arrancamiento por palanca de §17.7.3 tomaba N_cp = n·N_b, sin solape de conos ni bordes. En el caso de la placa con gran excentricidad (4 × M24, h_ef = 450 mm, s = 200 mm) daba φV_cp = 2928 kN, 12 veces el valor con el cono de grupo. Ahora N_cpg = N_cbg de §17.6.2 (A_Nc/A_Nco·ψ_ed,N·ψ_c,N·N_b) con la malla declarada en el docstring; sin `s_anchor_mm` usa un solo cono (cota inferior). Se añaden `s_anchor_mm`, `fya_MPa` (f_uta ≤ 1,9·f_ya) y `cast_in` (`tests/test_anchor_pryout_group_cone.py`).

## 0.2.0 — 2026-11-01

Correcciones encontradas al ejecutar los casos de uso del README.

- `tanks.api650.housner_masses`: periodo impulsivo según API 650 §E.4.5.1, T_i = (1/√2000)·C_i·H/√(t_u/D)·√ρ/√E con C_i de la Fig. E.1 (tabla de Malhotra 2000 = EN 1998-4 Tabla A.2) interpolado en H/R; antes faltaban el 1/√2000 y el √(t_u/D) y salía 0,006 s para un tanque de 20 m (ahora 0,227 s). Ramas de tanque esbelto (D/H < 1,333) para W_i y X_i; X_c con la expresión de §E.6.1.2.1 (antes una fórmula propia acotada a 0,4–0,7·H); T_c = 1,8·K_s·√D (§E.4.5.2); cortante basal y momento volcante combinados en SRSS (§E.6.1, §E.6.1.5) con pesos de manto y techo opcionales. Nuevos helpers `impulsive_period_s`, `convective_period_s`, `impulsive_coefficient_Ci`, `estimate_shell_and_roof_weight_kN`; el resultado expone `V_base_kN` y `C_i`.
- `tanks.anchorage.check_anchorage_J`: la relación J de §E.6.2.1.1.1 se calcula con fuerzas por unidad de perímetro (w_t = W_t/(π·D)); antes dividía por el peso total (factor π·D) y todo tanque salía «autoanclado». Nuevas entradas `w_a_kN_m` (fuerza resistente del anillo, helper `annulus_resisting_force_kN_m` = 99·t_a·√(F_y·H·G_e) ≤ 201,1·H·D·G_e) y `A_v`. El test que calibraba J con el peso total se ha corregido.
- `memos.render_tank_memo` y `POST /api/tanks/api650/full-design`: W_t es el peso de manto + techo (estimado de la geometría si no se da), no 1,05 veces el peso del líquido, que anulaba siempre el levantamiento; el cortante basal de la API es el SRSS de Housner. La memoria imprime W_t, w_a, V y C_i.
- `asce7_15_7`: fracción convectiva 0,230·(D/H)·tanh(3,68·H/D) (antes tenía D/H invertido: 0,171 en vez de 0,304 para D/H = 1,33); rama de tanque esbelto; S_ac = 1,5·S_D1/T_c ≤ 1,5·S_DS (ec. 15.7-10) y rama T_c > T_L (15.7-11); S_ai cae con T_i > T_s; T_i de API 650 §E.4.5.1 si se da `t_shell_mm`; pesos de manto y techo opcionales; el resultado expone `Sai_g` y `Sac_g`.
- `tanks.shell_buckling`: la tracción anular hidrostática σ_hoop = γ·H·D/(2·t) se compara ahora con la tensión admisible del manto `Sd_MPa` (160 MPa por defecto; §E.6.1.4 admite 1,333·S_d en la combinación sísmica). Hasta ahora se comparaba con la tensión crítica de Donnell a presión EXTERIOR (0,92·E·(t/R)^1,5·R/L, de 2 a 4 MPa en un tanque de 20 m) y entraba al cuadrado en la interacción, de modo que cualquier tanque lleno daba DCR_hoop entre 40 y 150 y «NO CUMPLE» por pandeo. Campos renombrados: `sigma_hoop_critical_MPa` → `sigma_hoop_allowable_MPa` y `Fc_hoop_MPa` → `Fh_hoop_allowable_MPa`; la interacción de la comprobación básica es el DCR axial. El pandeo por vacío sigue en `external_pressure`.
- `silos_en1991_4.janssen_pressures`: la presión horizontal se calculaba sin el factor K (γ·z_o·(1 − e^(−z/z_o)) es la VERTICAL, 1/K ≈ 1,9–2,5 veces mayor) y p_v y p_w arrastraban el error; ahora coincide con `ec1_silos.janssen_pressure`, que siempre fue correcta (golden W00225).
- `anchor_codes.design_anchor_concrete_cone`: en US/CO el hormigón no fisurado entra con Ψ_c,N = 1,25 (ACI 318-19 §17.6.2.5) sobre k_c = 10; antes usaba k_c = 17, el valor en libras-pulgada de los anclajes post-instalados (1,7× en vez de 1,25×).
- 34 casos de uso ejecutados en `examples/` con su salida en `examples/output/`; README reescrito; versión 0.2.0 y `__version__`.

## 0.1.0

Publicación inicial como repositorio independiente (origen: IndustrialJm del monorepo Structural JM, con las rutinas de vigas mixtas de CompositeJm vendorizadas en `_composite/`).
