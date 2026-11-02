# plantstruct — estructuras de planta industrial: tanques API 650, silos EN 1991-4, chimeneas, esferas, pipe racks, bases de columna y vigas mixtas

**Español** · [English](README.en.md) · [Português](README.pt.md) · [Italiano](README.it.md)

Cálculo de estructuras de planta de proceso en Python puro con `numpy` como única dependencia: tanques atmosféricos API 650 (virolas por el método del pie, tracción anular, pandeo del manto, presión exterior, masas de Housner del Anexo E con periodos, cortante y momento SRSS, relación de anclaje J y pernos, memoria completa, modelo de barra para SAP2000 y la variante ASCE 7-22 §15.7), silos EN 1991-4 (Janssen, clases de esbeltez, factores de descarga, carga parcheada, canal de flujo y pandeo meridional EN 1993-1-6), chimeneas (desprendimiento de vórtices), esferas de GLP (ASME VIII), pipe racks, naves (viento EN 1991-1-4 y flexocompresión EN 1993-1-1), muros antiexplosión SDOF, bases de columna con los cuatro modos de anclaje de ACI 318-19 cap. 17 y llave de cortante, anclajes multinorma y vigas mixtas de entrepiso por AISC 360 y EN 1994. Cada resultado dice qué hipótesis lleva dentro y cuándo no ha podido verificar.

[![CI](https://github.com/jmurgass99/plantstruct/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/plantstruct/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Qué problema resuelve

Las estructuras de planta (tanques, silos, racks, chimeneas, bases de equipos) se calculan con fórmulas de norma que caben en una hoja pero que se rehacen a mano en cada proyecto, con unidades mixtas y sin trazabilidad. El paquete las reúne con las ecuaciones citadas por cláusula, valores de referencia calculados a mano en los tests y una política explícita contra el aprobado silencioso: si falta un dato, el modo correspondiente sale `NO_CALCULADO` y el veredicto no puede ser favorable.

**Úsalo cuando**

- dimensiones o compruebes un tanque API 650: espesor de virolas, tracción anular, compresión del manto, vacío, sismo del Anexo E (masas, periodos, momento volcante, anclaje J, pernos) y quieras la memoria en Markdown o alimentar un modelo de SAP2000;
- necesites las presiones de EN 1991-4 en un silo (llenado, descarga, carga parcheada, canal de flujo) y la resistencia a pandeo de su pared por clase de calidad;
- predimensiones chimeneas, esferas de GLP, pipe racks o un muro antiexplosión y quieras saber qué parte es norma y qué parte es estimación;
- compruebes una placa base con pernos a tracción por ACI 318-19 cap. 17 (acero, cono, extracción, desprendimiento lateral) y llave de cortante;
- diseñes vigas mixtas de entrepiso industrial por AISC 360-16 Cap. I o EN 1994-1-1 con conexión parcial.

**No lo uses para**

- tanques de más de 60 m (método del punto de diseño variable, API 650 §5.6.4), techos flotantes, fondos y cimentaciones de tanque;
- silos con tolva (presiones de la tolva, §6), descarga excéntrica detallada (§5.2.4.3) o silos de hormigón;
- amplitud de vibración por vórtices (número de Scruton, EN 1991-1-4 ec. E.7): `chimneys` solo da la condición de resonancia y está marcado experimental;
- cortante en pernos de anclaje (ACI 318-19 §17.7) dentro de `disenar_base`: lleva el cortante a fricción y llave; `check_anchor_shear_aci318_17_7` existe aparte y hay que llamarla a mano;
- esfuerzos en el casco de esferas por sismo o viento: `esferas_gpl` es espesor por presión y reparto a columnas.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/plantstruct.git
pip install "plantstruct[api] @ git+https://github.com/jmurgass99/plantstruct.git"   # API REST con FastAPI
```

Para desarrollo: `git clone`, `pip install -e ".[test,api]"`, `pytest -q` (28 ficheros de tests). En Windows, si la consola no es UTF-8, ejecuta los ejemplos con `python -X utf8 examples/<nombre>.py`.

## Capacidades

| Capacidad | Módulos | Norma o referencia | Casos de uso |
|---|---|---|---|
| Tanques API 650, manto: espesor de virolas por el método del pie, tracción anular, pandeo axial con α de imperfecciones y knockdown de Rotter, tracción anular frente a S_d, presión exterior y rigidizadores | `tanks.shell_design`, `tanks.shell_buckling`, `external_pressure` | API 650 §5.6.3.2, Tabla 5.6a, §5.10.3, §5.9.7; ASME VIII Div. 1 UG-28; Rotter 1997; fichas W01046/W01096/W01112 | [5 casos](#1-tanques-api-650-manto) |
| Tanques API 650, sismo: pesos de Housner, alturas, T_i y T_c, cortante y momento SRSS, relación J, pernos, memoria completa, modelo de barra para SAP2000, ASCE 7-22 §15.7 | `tanks.api650`, `tanks.anchorage`, `asce7_15_7`, `memos.tank_complete`, `integration.fastsap_tank_parametric` | API 650 Anexo E (§E.4.5, §E.6.1, §E.6.2); ASCE 7-22 §15.7.6; Housner 1963; Malhotra 2000 / EN 1998-4 Tabla A.2 | [7 casos](#2-tanques-api-650-sismo) |
| Silos EN 1991-4: Janssen, clases de esbeltez, C_h/C_w, carga parcheada, canal de flujo, pandeo meridional por clase de calidad | `silos_en1991_4`, `ec1_silos`, `silo_buckling` | EN 1991-4:2006 §1.5, §5.2, §5.3, Anexo G, Tabla E.1; EN 1993-1-6 Anexo D; ficha W00225 | [5 casos](#3-silos-en-1991-4) |
| Otras estructuras de planta: chimeneas, esferas de GLP, pipe racks, naves (viento y flexocompresión), muros antiexplosión SDOF | `chimneys`, `esferas_gpl`, `pipe_rack`, `portal_frame`, `bunker` | EN 1991-1-4 §7.13 y Anexo E; ASME VIII Div. 1 UG-32; EN 1991-1-4 Tabla 4.1; EN 1993-1-1 §6.3.3 y Anexo B; UFC 3-340-02; ficha W00262 | [5 casos](#4-otras-estructuras-de-planta) |
| Bases de columna y anclajes: placa por Salmon & Johnson / AISC DG1, pernos a tracción con los cuatro modos de ACI 318-19 §17.6, llave de cortante, cono multinorma | `bases_columna`, `anchor_codes` | Salmon & Johnson §14; AISC Design Guide 1; ACI 318-19 §17.6 (k_c = 10 en SI); EN 1992-4 §7.2.1.4; AS 5216 §6.2.1 | [6 casos](#5-bases-de-columna-y-anclajes) |
| Vigas mixtas de entrepiso industrial y API REST | `composite_beams` (rutinas vendorizadas en `_composite/`), `api` | AISC 360-16 Cap. I (§I3.2, §I3.2d); EN 1994-1-1 §6.2, §6.6.1.2, ec. 6.28; ASCE 7-16 / EN 1990 combinaciones | [5 casos](#6-vigas-mixtas-y-api-rest) |

Los 33 scripts de `examples/` se ejecutaron en un entorno limpio antes de publicarse; su salida está en `examples/output/` y es la que se reproduce aquí.

## Casos de uso

### 1. Tanques API 650, manto

#### Espesor de cada virola por el método del pie en un tanque de agua de 20 m y uno de crudo de 36 m

t_d = 4,9·D·(H − 0,3)·G/S_d + CA y t_t = 4,9·D·(H − 0,3)/S_t con el mínimo nominal de la Tabla 5.6a; `governing` dice qué manda en cada anillo.

<details><summary>Salida real de <code>python examples/api650_shell_courses_one_foot_method_water_and_oil_tanks.py</code></summary>

```text
Tanque A — agua, A36, CA 1,5 mm: D = 20 m, H = 15 m
  virola  H sobre fondo [m]  t_d [mm]  t_t [mm] t_min [mm] t_req [mm]  manda
       1              15.00     10.50      8.42        6.0      10.50  diseno
       2              12.50      8.97      6.99        6.0       8.97  diseno
       3              10.00      7.44      5.56        6.0       7.44  diseno
       4               7.50      5.91      4.13        6.0       6.00  minimo_nominal
       5               5.00      4.38      2.69        6.0       6.00  minimo_nominal
       6               2.50      2.85      1.26        6.0       6.00  minimo_nominal

Tanque B — crudo G 0,90, A573M-485, CA 3 mm: D = 36 m, H = 18 m
  virola  H sobre fondo [m]  t_d [mm]  t_t [mm] t_min [mm] t_req [mm]  manda
       1              18.00     17.56     15.01        8.0      17.56  diseno
       2              15.75     15.71     13.10        8.0      15.71  diseno
       3              13.50     13.86     11.19        8.0      13.86  diseno
       4              11.25     12.01      9.29        8.0      12.01  diseno
       5               9.00     10.16      7.38        8.0      10.16  diseno
       6               6.75      8.31      5.47        8.0       8.31  diseno
       7               4.50      6.45      3.56        8.0       8.00  minimo_nominal
       8               2.25      4.60      1.65        8.0       8.00  minimo_nominal

La prueba hidrostática (G = 1, sin CA) solo manda cuando el líquido es ligero y el CA pequeño; en las virolas altas manda el mínimo nominal por diámetro.
```

</details>

#### Tracción circunferencial de membrana: T = γ·(H − y)·r = 500 kN/m en la base (ficha W01046)

<details><summary>Salida real de <code>python examples/hoop_tension_cylindrical_tank_W01046_500kN_per_m.py</code></summary>

```text
Depósito H = 10 m, r = 5 m, γ = 10 kN/m³
  cota y [m]  T [kN/m]  T con p = 20 kPa [kN/m]  σ = T/t (t = 10 mm) [MPa]
         0.0     500.0                    600.0                       60.0
         2.5     375.0                    475.0                       47.5
         5.0     250.0                    350.0                       35.0
         7.5     125.0                    225.0                       22.5
        10.0       0.0                    100.0                       10.0

Ficha W01046: T_base = γ·H·r = 10000·10·5 = 500,000 N/m = 500 kN/m
Fórmula de membrana: válida lejos del fondo y del techo, donde la restricción de borde añade flexión local.
```

</details>

#### Manto a compresión y a tracción: pandeo axial API 650, brecha con Rotter según R/t y tracción anular frente a S_d

La tracción anular hidrostática se compara con la tensión admisible, no con una tensión crítica de pandeo; el DCR axial por la ruta de Rotter se publica junto al de la norma.

<details><summary>Salida real de <code>python examples/shell_buckling_basic_vs_full_rotter_gap_vs_R_over_t.py</code></summary>

```text
D = 20 m, H_manto = 16 m, H_líquido = 15 m, σ_axial = 15.0 MPa, σ_flexión = 10.0 MPa, S_d = 160 MPa

  t [mm]    R/t Fbi API [MPa]  DCR_ax α_Rotter DCR_ax,Rotter  brecha σ_hoop [MPa] DCR_hoop DCR_flex        manda seguro
       6   1667          72.0   0.208    0.107         1.167    5.60        245.2    1.533  222.222  interaction False
       8   1250          96.0   0.156    0.138         0.680    4.35        183.9    1.150  125.000  interaction False
      12    833         144.0   0.104    0.194         0.323    3.10        122.6    0.766   55.556  interaction False
      20    500         240.0   0.062    0.286         0.131    2.10         73.6    0.460   20.000  interaction False

`axial_basis` = API650_alpha_imperfection: el veredicto usa α = 0,6; la columna de Rotter es la otra lectura de la misma demanda.
Con 6 y 8 mm manda la tracción anular (σ_hoop > S_d: hace falta el espesor del método del pie, 10,5 mm en la primera virola); con 12 y 20 mm el manto cumple y el axial queda holgado por la ruta API, no tanto por la de Rotter.

F_C de API 650 §E.6.2.2.3 (sísmico, con F_y = 250 MPa; informativo: no entra en el veredicto):
  t =    6 mm: G·H·D²/t² =  166.7 → F_C =  24.9 MPa (a mano  24.9); σ_axial/F_C = 0.60
  t =    8 mm: G·H·D²/t² =   93.8 → F_C =  33.2 MPa (a mano  33.2); σ_axial/F_C = 0.45
  t =   12 mm: G·H·D²/t² =   41.7 → F_C =  49.0 MPa (a mano  49.0); σ_axial/F_C = 0.31
  t =   20 mm: G·H·D²/t² =   15.0 → F_C =  62.2 MPa (a mano  62.2); σ_axial/F_C = 0.24
```

</details>

#### Presión exterior (vacío): presión crítica, factor de seguridad por norma y distancia máxima entre rigidizadores

<details><summary>Salida real de <code>python examples/external_pressure_vacuum_stiffener_spacing_by_code.py</code></summary>

```text
D = 20 m, t = 8 mm, L = 5 m entre rigidizadores

  P_ext [kPa] código P_cr [kPa]     FS FS req. cumple   L_max sin rigidizar [m]
          1.0    USA       6.90   6.90     3.0   True                     11.27
          1.0     EU       6.90   6.90     1.5   True                     22.37
          1.0     CO       6.90   6.90     3.0   True                     11.27
          1.0     AU       6.90   6.90     3.0   True                     11.27
          1.0     SG       6.90   6.90     1.5   True                     22.37

          2.5    USA       6.90   2.76     3.0  False                      4.62
          2.5     EU       6.90   2.76     1.5   True                      9.05
          2.5     CO       6.90   2.76     3.0  False                      4.62
          2.5     AU       6.90   2.76     3.0  False                      4.62
          2.5     SG       6.90   2.76     1.5   True                      9.05

Con 2,5 kPa y FS = 3 el manto de 8 mm necesita rigidizadores cada ~2,8 m; con FS = 1,5 bastan ~5,7 m.
La fórmula es la del cilindro corto entre rigidizadores; no cubre el pandeo general con techo ni la combinación con viento.
```

</details>

#### Límite del método del pie (D ≤ 60 m) y cómo la memoria lo declara en vez de aprobar en silencio

<details><summary>Salida real de <code>python examples/one_foot_method_limit_D_over_60m_and_memo_not_evaluated.py</code></summary>

```text
shell_thickness_one_foot(D = 66 m) → ValueError: Metodo del Pie valido solo para D <= 60 m; usar Variable-Design-Point

shell_thickness en la memoria: {'t_required_mm': None, 'is_ok': None, 'governing': 'NO CALCULADO', 'not_evaluated_reason': 'Metodo del Pie valido solo para D <= 60 m; usar Variable-Design-Point'}
is_safe: False

Fragmento de la memoria (Paso 2 y Resultado):
   - Espesor manto: t = 12.0 mm
   ## Paso 2 — Verificacion de espesor (API 650 §5.6)
   - **NO CALCULADO**: Metodo del Pie valido solo para D <= 60 m; usar Variable-Design-Point
   - Espesor: NO CALCULADO
   - **VERIFICACION GLOBAL: NO CUMPLE**

Con D = 60 m el método sí aplica:
  t_d = 30.0 mm, t_t = 27.8 mm, mínimo nominal 10 mm → t_req = 30.0 mm (diseno)
```

</details>

### 2. Tanques API 650, sismo

#### Tanque de 20 m × 15 m: pesos de Housner, alturas, T_i y T_c, cortante y momento SRSS con manto y techo

Comprobado a mano: W_i/W_p = 0,7096, W_c/W_p = 0,3042, X_c/H = 0,6803, T_i = 0,227 s (hasta la 0.2.0 el paquete daba 0,006 s), T_c = 4,67 s.

<details><summary>Salida real de <code>python examples/api650_annex_e_housner_masses_periods_T_i_T_c_20m_tank.py</code></summary>

```text
Tanque D = 20 m, H = 15 m, t_u = 8 mm, agua: W_p = 46,213 kN; manto 631 kN, techo 123 kN
  W_i =    32,790 kN  (W_i/W_p = 0.7096)   X_i = 5.625 m  (X_i/H = 0.3750)
  W_c =    14,057 kN  (W_c/W_p = 0.3042)   X_c = 10.204 m  (X_c/H = 0.6803)
  T_i = 0.227 s  (C_i = 6.06, H/R = 1.50)      T_c = 4.67 s
  V   = sqrt([A_i·(W_s + W_r + W_i)]² + [A_c·W_c]²) = 10,161 kN
  M_rw = sqrt([A_i·(W_i·X_i + W_s·X_s + W_r·X_r)]² + [A_c·W_c·X_c]²) = 59,204 kN·m

Sin manto ni techo: V = 9,937 kN, M_rw = 57,162 kN·m (la suma lineal daría 69,677 kN·m).
T_i = 0,23 s cae en la meseta del espectro; T_c = 4,7 s está en la rama de periodo largo, de ahí que A_c sea tan pequeño.
```

</details>

#### Periodo impulsivo y convectivo para cinco tanques de H/D = 0,2 a 2,0 con el coeficiente C_i de la Fig. E.1

<details><summary>Salida real de <code>python examples/api650_impulsive_period_sweep_H_over_D_and_C_i_table.py</code></summary>

```text
  D [m] H [m] t_u [mm]   H/D   H/R   C_i T_i [s] T_c [s] W_i/W_p W_c/W_p  X_c/H
     40     8       10  0.20  0.40  8.51   0.215    8.31   0.231   0.719  0.521
     30    12       10  0.40  0.80  6.77   0.222    6.01   0.450   0.517  0.574
     20    15        8  0.75  1.50  6.06   0.227    4.67   0.710   0.304  0.680
     12    18        8  1.50  3.00  7.03   0.245    3.60   0.855   0.153  0.820
     10    20        8  2.00  4.00  7.03   0.249    3.29   0.891   0.115  0.864

T_i crece con H/√(t_u/D): un manto más grueso rigidiza y acorta el periodo; el convectivo solo depende de D y H/D.
Todos los T_i quedan por debajo de ~0,6 s: el impulsivo suele caer en la meseta del espectro y A_i = S_DS·I/R_wi.
```

</details>

#### El mismo tanque por API 650 Anexo E y por ASCE 7-22 §15.7: pesos iguales, cortantes distintos por los factores R

<details><summary>Salida real de <code>python examples/api650_vs_asce7_15_7_same_tank_base_shear.py</code></summary>

```text
                              ASCE 7-22 §15.7  API 650 Anexo E
W_i [kN]                               32,790           32,790
W_c [kN]                               14,059           14,057
T_i [s]                                 0.227            0.227
T_c [s]                                 4.696            4.671
aceleración impulsiva [g]              0.4167           0.3125   (S_ai·I_e/R_i frente a A_i = S_DS·I/R_wi)
aceleración convectiva [g]             0.1597           0.1198   (S_ac·I_e/R_c frente a A_c)
V_i [kN]                               13,977           10,483
V_c [kN]                                2,245            1,684
V = sqrt(V_i² + V_c²) [kN]             14,156           10,617

Relación V_ASCE/V_API = 1.33: es R_wi/R_i = 4/3 en el término impulsivo, que domina.
S_ac lleva el tope 1,5·S_DS; con T_c = 4,7 s está muy por debajo y manda 1,5·S_D1/T_c.
```

</details>

#### Relación de anclaje J (§E.6.2.1.1.1) con fuerzas por unidad de perímetro: de autoanclado a anclaje mecánico al crecer A_i

<details><summary>Salida real de <code>python examples/api650_anchorage_J_ratio_classification_vs_A_i.py</code></summary>

```text
W_t (manto + techo) = 755 kN → w_t = 12.0 kN/m
  A_i [g] A_v [g] w_a [kN/m] M_rw [kN·m]      J                   tipo  F_p [kN] pernos M36
     0.05   0.024       48.3       9,994  0.415          self-anchored     1,251          7
     0.10   0.047       48.0      19,988  0.835            conditioned     3,257         18
     0.15   0.070       47.8      29,982  1.260            conditioned     5,263         28
     0.20   0.094       47.6      39,976  1.690  mechanically-anchored     7,269         39
     0.25   0.117       47.3      49,970  2.125  mechanically-anchored     9,275         49
     0.30   0.141       47.1      59,964  2.565  mechanically-anchored    11,281         60
     0.40   0.188       46.6      79,952  3.461  mechanically-anchored    15,293         81

Con A_i >= 0,15 g el tanque ya necesita anclaje mecánico; entre 0,05 y 0,10 g es autoanclado con levantamiento y hay que comprobar L y t_a (§E.6.2.1.1.2).
  A_i = 0.05 g: L = 0,01723·t_a·√(F_y/(H·G_e)) = 0.565 m (a mano 0.565); límite 0,035·D = 0.70 m → dentro
  A_i = 0.10 g: L = 0,01723·t_a·√(F_y/(H·G_e)) = 0.568 m (a mano 0.568); límite 0,035·D = 0.70 m → dentro
F_p = 4·M_rw/D − W_t·(1 − 0,4·A_v) es el levantamiento total para anclaje mecánico (§E.6.2.1.2); el número de pernos usa φ·A_b·F_y.
```

</details>

#### Pernos de anclaje: carga por perno, capacidad y número necesario para tres disposiciones

<details><summary>Salida real de <code>python examples/api650_anchor_bolts_uplift_per_bolt_and_required_count.py</code></summary>

```text
M_rw = 29,601 kN·m, W_t = 900 kN → levantamiento total 4·M/D − W_t = 5,020 kN

   N_b  perno F_y [MPa] P_AB [kN] cap. [kN]    DCR seguro  N_b mínimo
    24    M30       250     209.2     106.0   1.97  False          48
    48    M36       250     104.6     152.7   0.69   True          33
    32    M36       400     156.9     244.3   0.64   True          21

W_tank_kN es el peso de manto + techo + accesorios: con el peso del líquido en su lugar el levantamiento sale cero y el anclaje «cumple» sin calcular nada.
```

</details>

#### Memoria completa en Markdown: geometría, Housner, espesor, anclaje, pandeo y veredicto

<details><summary>Salida real de <code>python examples/api650_complete_tank_memo_markdown.py</code></summary>

```text
# Memoria de calculo — Estanque API 650 §E

## Geometria
- Diametro: D = 20.0 m
- Altura liquido: H_l = 15.0 m
- Altura manto: H_shell = 16.0 m
- Espesor manto: t = 10.0 mm
- Volumen: V = 4712 m3
- Peso liquido: W_l = 46213 kN
- Peso manto + techo: W_t = 912 kN (estimado: manto de t_shell + techo plano de 5 mm, acero 78,5 kN/m3)

## Paso 1 — Masas Housner (impulsiva/convectiva)
- Masa impulsiva: W_i = 32790 kN (h_i = 5.62 m)
- Masa convectiva: W_c = 14057 kN (h_c = 10.20 m)
- **Periodo impulsivo: T_i = 0.203 s** (API 650 E.4.5.1, C_i = 6.06)
- **Periodo convectivo: T_c = 4.67 s**
- **Sismicidad:** A_i = 0.15 g, A_c = 0.05 g
- **Cortante basal (SRSS): V = 4969 kN**
- **Momento volcante (SRSS, base del manto): M_rw = 28581 kN*m**

## Paso 2 — Verificacion de espesor (API 650 §5.6)
- t_design = 9.0 mm (condicion diseno)
- t_test = 8.4 mm (prueba hidrostatica)
- t_requerido = 9.0 mm (gobernante: diseno)
- t_actual = 10.0 mm
- Verificacion: OK

## Paso 3 — Anclajes (API 650 §E.6.2)
- Uplift/perno = 100 kN
- Capacidad/perno = 153 kN
- DCR = 0.66
- w_t = 14.5 kN/m, w_a = 58.6 kN/m (anillo t_a = 10.0 mm)
- J-ratio = 0.982 -> conditioned
- Pernos requeridos (J): 26
- Silleta: t_base_plate = 36.0 mm, L_anchor = 225 mm

## Paso 4 — Pandeo del manto y traccion anular
- sigma_hoop = 147.2 MPa (admisible S_d = 160.0 MPa; traccion, no pandeo)
- DCR_axial = 0.000
- DCR_hoop (traccion anular) = 0.920
- DCR_interaction = 0.000
- Rotter alpha_diamond = 0.167
- Pandeo diamante: Fbi = 33.3 MPa
- Modo gobernante: hoop

## Resultado
- Espesor: OK
- Anclajes: OK
- Pandeo: OK
- **VERIFICACION GLOBAL: CUMPLE**

Diccionario de anclaje J: {'J': 0.982, 'anchorage_type': 'conditioned', 'N_bolts_required': 26, 'Ab_mm2': 1017.876, 'Fp_kN': 4829.317, 't_base_plate_mm': 36.0, 'L_anchor_mm': 225.0, 'is_self_anchored': False, 'w_t_kN_m': 14.523, 'w_a_kN_m': 58.641}
Espesor: {'t_design_mm': 9.0, 't_test_mm': 8.42, 't_required_mm': 9.0, 'governing': 'diseno', 'actual_mm': 10.0, 'is_ok': True}
is_safe: True
```

</details>

#### Modelo de barra de Housner para SAP2000 (masa convectiva sobre resorte k_c = m_c·ω_c²) y malla paramétrica del manto

<details><summary>Salida real de <code>python examples/housner_stick_model_for_sap2000_and_parametric_shell_mesh.py</code></summary>

```text
Nudos:
  BASE  z =  0.000 m  restricción = [True, True, True, True, True, True]
   IMP  z =  5.625 m  restricción = None
  CONV  z = 10.204 m  restricción = None
Masas [kN·s²/m]:
   IMP  m =    3343.7  (impulsiva (rígida al manto))
  CONV  m =    1433.4  (convectiva (sobre resorte T_c))
Resorte convectivo: k_c = 2593.1 kN/m en CONV → T = 2π·sqrt(m_c/k_c) = 4.671 s (T_c de Housner = 4.671 s)
Resumen sísmico: {'W_i_kN': 32790.273, 'W_c_kN': 14057.12, 'h_i_m': 5.625, 'h_c_m': 10.204, 'T_i_s': 0.227, 'T_c_s': 4.671, 'M_overturn_kNm': 57162.43, 'V_base_kN': 9937.012, 'C_i': 6.06}

Malla del manto: 216 nudos (25 anillos × 24), 192 áreas de 4 nudos; dry_run = True
  primera área: {'name': 'S_0_0', 'n1': 'J_0_0', 'n2': 'J_0_1', 'n3': 'J_1_1', 'n4': 'J_1_0'}
Para ejecutar contra SAP2000 real se pasa el objeto SapModel como `client`; los fallos de AddByPoint se devuelven en `failed`, no se tragan.
```

</details>

### 3. Silos EN 1991-4

#### Presiones de llenado de Janssen en un silo de trigo de 6 m × 18 m (ficha W00225)

<details><summary>Salida real de <code>python examples/silo_janssen_pressures_wheat_EN1991_4_W00225.py</code></summary>

```text
Silo D = 6 m, h_c = 18 m; trigo γ = 9.0 kN/m³, K = 0.54, μ = 0.38: z_o = 7.31 m, p_ho = 35.5 kPa
  z [m] p_hf [kPa] p_vf [kPa] p_wf [kPa] p_hf/p_ho
    0.0       0.00       0.00       0.00     0.000
    2.0       8.50      15.75       3.23     0.239
    4.0      14.97      27.73       5.69     0.421
    6.0      19.89      36.84       7.56     0.560
    9.0      25.15      46.58       9.56     0.708
   12.0      28.65      53.05      10.89     0.806
   15.0      30.96      57.34      11.77     0.872
   18.0      32.50      60.18      12.35     0.915

janssen_pressures (fondo): p_h = 32.498, p_v = 60.182, p_w = 12.349 kPa
janssen_pressure(z = 18):  p_h = 32.498, p_v = 60.182 kPa → diferencia 0.0e+00 kPa

A 18 m la presión horizontal ya es el 91 % de la asíntota; la vertical sobre el fondo, 60 kPa, es solo el 37 % de γ·h: el resto lo lleva la pared por rozamiento.
```

</details>

#### Clase de esbeltez y factores de descarga C_h, C_w para cuatro alturas del mismo silo

<details><summary>Salida real de <code>python examples/silo_slenderness_classes_and_discharge_factors_C_h_C_w.py</code></summary>

```text
  h_c [m] h_c/d_c        clase   C_h   C_w p_hf fondo [kPa] p_he = C_h·p_hf p_we = C_w·μ·p_hf
     18.0    3.00      slender  1.15  1.10            48.64           55.93             24.08
      9.0    1.50 intermediate  1.15  1.10            37.51           43.14             18.57
      4.0    0.67        squat  1.00  1.00            22.25           22.25             10.01
      2.0    0.33    retaining  1.00  1.00            12.62           12.62              5.68

La clase decide también la carga parcheada (§5.2.4) y si aplica el canal de flujo (Anexo G): ver el caso siguiente.
Los C_h/C_w son los valores recomendados de la Tabla 5.2 para clase de evaluación 2; la clase 3 exige el cálculo detallado de §5.3.2.
```

</details>

#### Carga parcheada de llenado y presión en el canal de flujo de un silo esbelto

<details><summary>Salida real de <code>python examples/silo_patch_load_and_flow_funnel_slender_silo.py</code></summary>

```text
Silo h_c/d_c = 3.0 → slender; z_o = 7.31 m; banda de la carga parcheada s = π·d_c/16 = 1.18 m
  z [m] p_hf [kPa] ±p_pf [kPa] p_pf/p_hf p_hce canal [kPa] reducción
    3.0      11.96        1.26     0.105             11.17      6.6 %
    6.0      19.89        2.09     0.105             19.02      4.4 %
    9.0      25.15        2.64     0.105             24.42      2.9 %
   12.0      28.65        3.01     0.105             28.09      1.9 %
   15.0      30.96        3.25     0.105             30.56      1.3 %
   18.0      32.50        3.41     0.105             32.22      0.9 %

La carga parcheada es la que produce flexión circunferencial en la pared (no la presión simétrica de Janssen);
en un silo achaparrado C_pf = 0 y el canal de flujo no se aplica (la función devuelve Janssen sin reducir).
Silo achaparrado h_c = 4 m: p_hce = 14.97 kPa = p_hf = 14.97 kPa
```

</details>

#### Pandeo meridional de la pared con la compresión que le transmite el rozamiento del grano, por clase de calidad A/B/C

<details><summary>Salida real de <code>python examples/silo_wall_meridional_buckling_EN1993_1_6_quality_classes.py</code></summary>

```text
Fuerza meridional en la pared a z = 18 m: n_x = 152.7 kN/m (el grano pesa γ·h_c·A/perímetro = 243.0 kN/m; la pared lleva el 63 %)

  t [mm] σ_x [MPa] σ_cr [MPa]    α_A  σ_Rd,A    α_B  σ_Rd,B    α_C  σ_Rd,C  utilización A/B/C
       4     38.18      169.4  0.294    45.3  0.195    30.0  0.121    18.6  0.84 / 1.27 / 2.06
       5     30.55      211.8  0.319    61.4  0.217    41.8  0.137    26.4  0.50 / 0.73 / 1.16
       6     25.45      254.1  0.339    78.4  0.236    54.5  0.151    35.0  0.32 / 0.47 / 0.73
       8     19.09      338.8  0.371   114.2  0.267    82.2  0.176    54.3  0.17 / 0.23 / 0.35

Sin clase de calidad: ValueError → quality_class or alpha must be provided explicitly (no default fabrication quality assumed…

Solo el peso del grano no agota la pared; el pandeo meridional lo deciden el viento con el silo vacío, la descarga excéntrica y la clase de fabricación (A frente a C: factor 2,2).
```

</details>

#### Sensibilidad a K y μ y coherencia de las dos rutinas de Janssen del paquete

<details><summary>Salida real de <code>python examples/silo_two_implementations_consistency_and_K_mu_sensitivity.py</code></summary>

```text
Mayor diferencia entre las dos rutinas sobre las 9 combinaciones: 2.8e-14 kPa

p_hf en el fondo [kPa] (filas K, columnas μ)      y      p_wf = μ·p_hf [kPa]
   K \ μ     0.25      0.4     0.55          0.25      0.4     0.55
    0.40     80.9     63.8     51.7          20.2     25.5     28.5
    0.50     91.3     69.2     54.5          22.8     27.7     30.0
    0.60     99.4     72.7     56.0          24.9     29.1     30.8

La presión horizontal máxima aparece con K = 0,60 y μ = 0,25; la fricción máxima (y con ella la compresión de la pared) con μ = 0,55.
Por eso la norma pide combinaciones distintas para dimensionar los anillos y para dimensionar la pared a compresión.
```

</details>

### 4. Otras estructuras de planta

#### Chimenea de 40 m: frecuencia propia, velocidad crítica de vórtices y banda de riesgo (experimental)

<details><summary>Salida real de <code>python examples/steel_chimney_vortex_shedding_critical_wind_speed.py</code></summary>

```text
Chimenea H = 40 m, D = 2,5 m, t = 10 mm, V_b = 26 m/s (experimental):
  f_1 = 1.560 Hz, T_1 = 0.641 s, v_crit = 21.7 m/s, banda [13.0, 32.5] m/s → en banda: True, H/D = 16, peso 6.05 kN/m

  D [m] t [mm] f_1 [Hz] v_crit [m/s] en banda   H/D
    1.5      8    0.936          7.8    False  26.7
    1.5     12    0.936          7.8    False  26.7
    2.0      8    1.248         13.9     True  20.0
    2.0     12    1.248         13.9     True  20.0
    2.5      8    1.560         21.7     True  16.0
    2.5     12    1.560         21.7     True  16.0
    3.0      8    1.872         31.2     True  13.3
    3.0     12    1.872         31.2     True  13.3

f_1 crece con D/H² y v_crit con D²/H²: a igual altura, las chimeneas anchas salen de la banda por arriba; las de 1,5–2,5 m quedan dentro.
Que la velocidad crítica esté en la banda no significa que la amplitud sea inadmisible: hace falta el número de Scruton y el amortiguamiento.
```

</details>

#### Esfera de GLP de 20 m a 17,5 bar: espesor ASME VIII UG-32, carga por columna y cortante basal preliminar

<details><summary>Salida real de <code>python examples/lpg_sphere_asme_viii_thickness_columns_and_base_shear.py</code></summary>

```text
  D [m] P [bar] código t_min [mm] W_total [kN] P columna [kN] V_basal [kN]
     20    17.5     US       63.5       26,402          2,640        5,280
     20    17.5     EU       63.5       26,402          2,640        3,960
     14    18.0     US       45.7        9,116          1,140        1,823
     14    18.0     EU       45.7        9,116          1,140        1,367

Comprobación UG-32 a mano para D = 20 m: t = 63.5 mm (paquete 63.5 mm)
El peso total es líquido al 85 % más el casco de espesor t_min; el cortante basal es C_s·W, un coeficiente de criba, no un espectro.
```

</details>

#### Pipe rack de dos y tres niveles: pesos, momento por fricción térmica y cortante basal de anteproyecto

<details><summary>Salida real de <code>python examples/pipe_rack_loads_thermal_moment_and_base_shear_preliminary.py</code></summary>

```text
  niveles código térmico W_total [kN] W/columna [kN] M_térmico [kN·m] V_basal [kN]
        2     US    True          720            180               72          108
        2     US   False          720            180                0          108
        2     EU    True          720            180               72           72
        2     EU   False          720            180                0           72
        3     US    True        1,080            270               72          162
        3     US   False        1,080            270                0          162
        3     EU    True        1,080            270               72          108
        3     EU   False        1,080            270                0          108

El reparto es a cuatro columnas por módulo; el peso de la propia estructura y las cargas de viento y amarre de tuberías no están incluidos.
```

</details>

#### Nave: presión de pico del viento por categoría de terreno y flexocompresión de un pilar IPE 400 con el k_y declarado

<details><summary>Salida real de <code>python examples/portal_frame_wind_pressure_terrain_categories_and_member_interaction_IPE400.py</code></summary>

```text
q_b = ½·1,25·26² = 0.422 kPa; q_p(z = 8 m) por categoría de terreno:
  categoría   0: q_p = 1.220 kPa
  categoría   I: q_p = 1.012 kPa
  categoría  II: q_p = 0.845 kPa
  categoría III: q_p = 0.719 kPa
  categoría  IV: q_p = 0.474 kPa

IPE 400 S275, N_Ed = 250 kN, M_y,Ed = 180 kN·m, χ_y = 0,80, χ_LT = 0,85:
  member_compression_capacity_kN   1858.120
  member_bending_capacity_kNm      270.215
  axial_utilization                0.135
  bending_utilization              0.666
  interaction_coefficient_ky       1.081
  combined_interaction_ratio       0.854
  status                           CUMPLE
  k_y_basis: EN 1993-1-1 Anexo B, Tabla B.1 (Metodo 2, clases 1-2) SIMPLIFICADA: k_y = min(1 + 0.6*n, 1.4), equivalente a C_my = 1.0 …

k_yy con la fórmula de la Tabla B.1 (pasando λ̄_y; C_my = 1) frente a la histórica:
  λ̄_y = 0.5: k_yy = 1.040 (a mano 1 + min(λ̄_y − 0,2; 0,8)·n_y = 1.040), ratio 0.828 frente a 0.854
  λ̄_y = 0.8: k_yy = 1.081 (a mano 1 + min(λ̄_y − 0,2; 0,8)·n_y = 1.081), ratio 0.854 frente a 0.854
  λ̄_y = 1.2: k_yy = 1.108 (a mano 1 + min(λ̄_y − 0,2; 0,8)·n_y = 1.108), ratio 0.872 frente a 0.854
  λ̄_y = 1.6: k_yy = 1.108 (a mano 1 + min(λ̄_y − 0,2; 0,8)·n_y = 1.108), ratio 0.872 frente a 0.854

tracción: ValueError → check_steel_member_interaction: N_Ed_kN=-300 kN es TRACCIÓN, y EN 1993-1-1 §6.3.3 cubre 'members in bending an…

χ_y ausente: ValueError → check_steel_member_interaction: chi_y debe proporcionarse explícitamente. No se asumen factores de reducción p…
```

</details>

#### Muro antiexplosión como SDOF elastoplástico: demanda de ductilidad en régimen impulsivo y rotación de apoyo

<details><summary>Salida real de <code>python examples/blast_wall_sdof_ductility_demand_impulsive_asymptote.py</code></summary>

```text
Muro: m = 600 kg/m², k = 2.0e+07 Pa/m, R_m = 150 kPa, L = 4 m, μ_adm = 3; T = 34.4 ms, x_el = 7.5 mm

  i [Pa·s]      μ x_max [mm] θ apoyo [°] μ/μ_adm cumple
       750   1.42       10.6        0.30    0.47 True
      1000   1.74       13.1        0.37    0.58 True
      1500   2.67       20.0        0.57    0.89 True
      2000   3.96       29.7        0.85    1.32 False
      2500   5.63       42.2        1.21    1.88 False

Comprobación a mano para i = 1 500 Pa·s: μ = 1 + i²/(2·m·R_m·x_el) = 2.667 (paquete 2.667)
La duración positiva de la onda debe ser << 34 ms para que valga la asíntota impulsiva; UFC 3-340-02 limita además θ a 2° (respuesta moderada) en hormigón armado.
```

</details>

### 5. Bases de columna y anclajes

#### Placa base con excentricidad pequeña (e ≤ N/6): dimensiones, espesor y sin tracción en los pernos

<details><summary>Salida real de <code>python examples/column_base_plate_small_eccentricity_salmon_johnson.py</code></summary>

```text
Placa: N = 400 mm, B = 400 mm, t = 29.2 mm; e = M/P = 33.3 mm (N/6 = 66.7 mm)
Tracción en pernos T_u = 0.0 kN → modo: sin_demanda_de_traccion, is_ok = True
Llave de cortante requerida: False (V = 60 kN, fricción μ·P = 600 kN)
Estado: VERIFICADO, cumple = True

Notas del resultado:
  - Acero (§17.6.1): capacidad calculada como fluencia sobre area bruta (n/2 * pi*db^2/4 * fyb), NO como N_sa = A_se,N * f_uta de §17.6.1.2. El modulo no …
  - §17.6.2 NO CALCULADO: falta geometria del anclaje (hef_mm, ca1_mm, ca2_mm, s_anchor_mm). El arrancamiento del cono de hormigon suele ser el modo GOBER…
  - §17.6.3 (extraccion) NO CALCULADO: falta A_brg, el area de apoyo de la cabeza del perno. Es un modo del HORMIGON, no del acero.
  - Tu = 0 kN: los anclajes no reciben traccion en esta combinacion, luego §17.6 no tiene demanda contra la que comprobarse. El veredicto NO significa que…
  - ALCANCE: §17.7 (cortante en anclajes: acero, breakout y pryout) y §17.8 (interaccion traccion-cortante) NO se comprueban. Este modulo lleva todo el co…
```

</details>

#### Gran excentricidad con geometría completa del anclaje: los cuatro modos de ACI 318-19 §17.6 y el que gobierna

<details><summary>Salida real de <code>python examples/column_base_plate_large_eccentricity_aci318_17_anchor_modes.py</code></summary>

```text
Placa: N = 400 mm, B = 400 mm, t = 31.7 mm; e = 650 mm > N/6 = 67 mm → T_u = 666.7 kN en los 2 pernos traccionados
  modo                   nominal [kN] diseño [kN] estado
  acero §17.6.1                 380.0       285.0 APLICA
  cono §17.6.2                  138.6        97.0 APLICA
  extracción §17.6.3            480.0       336.0 APLICA
  desprendimiento §17.6.4            —           — NO_APLICA
Gobierna: concrete_breakout con 97.0 kN frente a T_u = 666.7 kN → is_ok = False
Llave de cortante: requerida = False (fricción 160 kN frente a V = 80 kN)
Estado: VERIFICADO, cumple = False

N_b(f'c = 25 MPa, h_ef = 300 mm) = 259.81 kN (k_c = 10 SI; con el 24 de libras-pulgada saldría 2,4 veces más)
Los φ (0,75 acero, 0,70 hormigón) son entrada fija del módulo sin armadura suplementaria.

Acero del perno §17.6.1.2 con A_se,N = 353 mm² (M24) y f_uta = 620 MPa: N_sa = 437.7 kN (a mano 2·353·620 = 437.7) frente a 380.0 kN por fluencia sobre el área bruta
Cortante en anclajes §17.7 si el cortante lo toman los 4 pernos (sin fricción ni llave), V = 80 kN:
  acero φV_sa                        341.4 kN
  rotura de borde φV_cb               31.8 kN
  arrancamiento por palanca φV_cp    238.4 kN
  utilización a cortante 2.52; interacción §17.8 (exponente 5/3) 29.49 → is_ok = False
  V_cp = k_cp·N_cbg del grupo 2 × 2 (s = 200 mm): A_Nc = 752,500 mm², N_cbg = 170.3 kN (la suma 4·N_b daría 2091 kN, sin solape de conos ni bordes). Gobierna la rotura de borde.
```

</details>

#### La misma base sin la geometría del anclaje: NO_VERIFICADO con la lista exacta de lo que falta

<details><summary>Salida real de <code>python examples/column_base_missing_anchor_geometry_is_not_verified.py</code></summary>

```text
T_u = 666.7 kN; acero nominal 380.0 kN, diseño 285.0 kN
cono: NO_CALCULADO, extracción: NO_CALCULADO, desprendimiento lateral: NO_CALCULADO
governing_mode = None, is_ok = None
missing_inputs = ['hef_mm', 'ca1_mm', 'ca2_mm', 's_anchor_mm', 'Abrg_mm2']
verification_status = NO_VERIFICADO, cumple = False

Nota del módulo:
   NO VERIFICADO: modos de HORMIGON sin calcular (concrete_breakout, pullout, side_face_blowout). Solo se ha comprobado el ACERO (§17.6.1); el modo gobernante podria ser cualquiera de los del hormigon y ser mucho menor. Suministre: hef_mm, ca1_mm, ca2_mm, s_anchor_mm, Abrg_mm2.

Con la geometría completa (caso anterior) el mismo pilar sí obtiene veredicto: la diferencia es solo la información, no la carga.
```

</details>

#### Llave de cortante: cuándo hace falta y qué capacidad tiene (caso golden del paquete)

<details><summary>Salida real de <code>python examples/column_base_shear_lug_required_when_friction_insufficient.py</code></summary>

```text
μ = 0.20: fricción μ·P = 120 kN frente a V = 180 kN → llave requerida: True
  llave 200 × 75 × 25 mm: aplastamiento 207 kN, cortante chapa 562 kN → is_ok = True
  placa N = 400, B = 300, t = 24.5 mm; T_u = 0.0 kN; estado VERIFICADO, cumple = True

μ = 0.40: fricción μ·P = 240 kN frente a V = 180 kN → llave requerida: False
  placa N = 400, B = 300, t = 24.5 mm; T_u = 0.0 kN; estado VERIFICADO, cumple = True

dims_source: ENTRADA FIJA: altura 75 mm y espesor 25 mm son constantes del modulo, NO un dimensionamiento. Solo el ancho se ata a la geometria de la plac…
```

</details>

#### Cono de hormigón de un anclaje aislado en ACI 318-19, EN 1992-4 y AS 5216

<details><summary>Salida real de <code>python examples/anchor_concrete_cone_capacity_multi_code_US_EU_AU.py</code></summary>

```text
f'c = 30 MPa, 4 anclajes, capacidad de DISEÑO del grupo [kN] (φ·N o N/γ):
  h_ef [mm]  fisurado  US (ACI) EU (EN 1992-4) AU (AS 5216)
        200      True     402.8          318.1        318.7
        200     False     503.5          454.4        447.1
        300      True     740.0          584.4        585.5
        300     False     925.0          834.8        821.3
        400      True    1139.3          899.7        901.4
        400     False    1424.1         1285.3       1264.5

Un anclaje, f'c = 25, h_ef = 300: N_b = 259.81 kN (bases_columna) → φ·N_b = 168.87 kN; anchor_codes: 168.87 kN
EN 1992-4 con k_1 = 7,7 y γ_Mc = 1,5 da capacidades de diseño ~20 % por debajo de ACI con φ = 0,65 para el mismo cono.
```

</details>

#### Base con tracción neta (P ≤ 0): el módulo no dimensiona por aplastamiento y lo dice

<details><summary>Salida real de <code>python examples/column_base_uplift_P_le_0_honest_not_verified.py</code></summary>

```text
N = 300 mm, B = 300 mm (mínimo por contorno), t = None, e = None, T_u = None
fricción = 0 kN → llave requerida: True, is_ok = None
anclaje: is_ok = None, missing_inputs = ['Tu_kN (demanda de traccion bajo levantamiento)']
verification_status = NO_VERIFICADO, cumple = False

- NO VERIFICADO: P = -150 kN no es compresion. Traccion neta (levantamiento) de 150 kN que los anclajes deben resistir junto con el efecto del momento; este modul…
- Matiz respecto a la version anterior de esta nota: la CAPACIDAD a traccion de los anclajes SI esta implementada (ACI 318-19 §17.6: acero, cono de hormigon, extr…
- Friccion base = mu * compresion = 0 kN: sin axil de compresion no hay transferencia de cortante por rozamiento.
- N_mm y B_mm son el MINIMO geometrico por contorno de columna (d+100, bf+100), no un dimensionamiento por aplastamiento.
```

</details>

### 6. Vigas mixtas y API REST

#### Viga mixta de entrepiso industrial por AISC 360-16: W460x74 a 9 m con conectores dimensionados automáticamente

<details><summary>Salida real de <code>python examples/composite_mezzanine_beam_AISC_360_W460x74_auto_studs.py</code></summary>

```text
### Verificación de Viga Compuesta Industrial (AISC 360-16 (LRFD))
**Estado Global**: ✅ CUMPLE (DCR Gobernante = 0.47 por Flexión Compuesta)

| Comprobación | DCR | Capacidad | Solicitación | Estado |
| :--- | :---: | :---: | :---: | :---: |
| Flexión Compuesta | 0.47 | 1110.4 kN·m | 523.6 kN·m | OK |
| Cortante Compuesto | 0.27 | 851.4 kN | 232.7 kN | OK |
| Flexión Constructiva | 0.30 | - | - | OK |
| Flecha Sobrecarga (L/SLS) | 0.30 | - | 7.5 mm | OK |
| Flecha Total (L/SLS) | 0.32 | - | 11.8 mm | OK |

- **Conectores**: 70 pernos tipo stud (35 por semivano, paso ~129 mm)

M_u = 523.6 kN·m frente a φM_n = 1110.4 kN·m; V_u = 232.7 kN frente a φV_n = 851.4 kN
Flecha de sobrecarga 7.5 mm (L/360 = 25 mm); total 11.8 mm (L/240 = 37.5 mm)
Viable: True; gobierna Flexión Compuesta con DCR 0.47
```

</details>

#### Viga mixta por EN 1994-1-1: IPE 450 S355 con conexión parcial y el mínimo de §6.6.1.2

<details><summary>Salida real de <code>python examples/composite_mezzanine_beam_EN1994_IPE450_partial_interaction.py</code></summary>

```text
=== num_studs_total = 24 → 24 pernos (12 por semivano, paso 333 mm) ===
  M_Ed = 261.4 kN·m, M_Rd = 743.6 kN·m → DCR 0.35; V_Ed = 130.7 kN, V_Rd = 887.9 kN → DCR 0.15
  flecha sobrecarga 3.2 mm (DCR 0.14), total 5.8 mm (DCR 0.18)
  viable = False; gobierna Flexión Compuesta (0.35)
  · Aviso Eurocódigo 4 §6.6.1.2: Grado de conexión 0.39 < mínimo normativo 0.49.

=== num_studs_total = automático → 62 pernos (31 por semivano, paso 129 mm) ===
  M_Ed = 261.4 kN·m, M_Rd = 958.6 kN·m → DCR 0.27; V_Ed = 130.7 kN, V_Rd = 887.9 kN → DCR 0.15
  flecha sobrecarga 2.3 mm (DCR 0.10), total 4.2 mm (DCR 0.12)
  viable = True; gobierna Flexión Compuesta (0.27)

La flecha con interacción parcial usa I_eff = I_a + sqrt(η)·(I_tr − I_a), la aproximación de AISC I3.2; EN 1994 no la prescribe y hay que confirmarla con el método del fabricante de la chapa.
```

</details>

#### Desglose de cargas: fase constructiva frente a fase mixta, apuntalada o no, con carga puntual de equipo

<details><summary>Salida real de <code>python examples/composite_beam_loads_breakdown_construction_vs_composite_stage.py</code></summary>

```text
  magnitud                             AISC, sin apuntalar            AISC, apuntalada EN 1990/1994, sin apuntalar
  w_dead_construction_kN_m                             8.6                         8.6                         8.6
  w_dead_total_kN_m                                   13.1                        13.1                        13.1
  w_live_kN_m                                         22.5                        22.5                        22.5
  q_u_const_kN_m                                      15.1                        15.1                        16.1
  q_u_comp_kN_m                                       51.7                        51.7                        51.4
  M_u_const_kNm                                      153.0                         0.0                       163.0
  V_u_const_kN                                        68.0                         0.0                        72.4
  M_u_comp_kNm                                       946.6                       946.6                       942.5
  V_u_comp_kN                                        326.7                       326.7                       325.2

Peso propio del perfil: 0.728 kN/m (estimado de A·78,5 kN/m³); losa: espesor eficaz (t − h_deck/2)·s·24 kN/m³ + 0,15 kPa de chapa.
La carga puntual en centro de vano añade P·L/4 al momento y P/2 al cortante de la fase mixta.
```

</details>

#### Cuántos pernos hacen falta: capacidad, flecha y modo gobernante según el número de conectores

<details><summary>Salida real de <code>python examples/composite_beam_stud_count_sensitivity_and_governing_mode.py</code></summary>

```text
  pernos paso [mm] φM_n [kN·m] DCR flexión flecha L [mm] DCR flecha L viable  gobierna
      16       562         0.0      999.00           0.0         0.00  False  Flexión Compuesta
         · Error en dimensionamiento compuesto: AISC 360-16 §I3.2d violation: sum(Qn) = 765.5 kN is less than 25% of V'_full (815.9
      24       375       774.9        0.68          10.7         0.43   True  Flexión Compuesta
      32       281       812.8        0.64           9.7         0.39   True  Flexión Compuesta
      48       188       898.9        0.58           8.5         0.34   True  Flexión Compuesta
      64       141       981.1        0.53           7.6         0.31   True  Flexión Compuesta
      70       129      1110.4        0.47           7.5         0.30   True  Flexión Compuesta (automático)

AISC 360-16 §I3.2d exige ΣQ_n >= 0,25·min(A_s·F_y, 0,85·f'c·A_c) salvo justificación; por debajo la viga ya no es mixta a efectos de cálculo.
```

</details>

#### API REST sin servidor: Housner, anclaje, pandeo, diseño completo API 650 y Janssen de silos

<details><summary>Salida real de <code>python examples/rest_api_tanks_api650_full_design_and_silos_janssen_testclient.py</code></summary>

```text
GET  /api/tanks/health → 200
   {"status": "ok"}
POST /api/tanks/api650/housner → 200
   {"W_i_kN": 32790.273201916796, "W_c_kN": 14057.119611404065, "h_i_m": 5.625, "h_c_m": 10.203766918193702, "T_i_s": 0.22724999999999995, "T_c_s": 4.671486179330775, "M_overturn_kNm": 57162.429759888415, "V_base_kN": 9937.012006471767, "C_i": 6.06}
POST /api/tanks/anchorage → 200
   {"F_uplift_per_bolt_kN": 545.8333333333334, "F_allowable_per_bolt_kN": 106.02875205865551, "DCR": 5.1479747024785905, "is_safe": false, "n_bolts_required_min": 124}
POST /api/tanks/shell-buckling → 200
   {"sigma_axial_demand_MPa": 15.0, "sigma_hoop_demand_MPa": 147.15, "sigma_axial_critical_MPa": 120.0, "sigma_hoop_allowable_MPa": 160.0, "DCR_axial": 0.125, "DCR_hoop": 0.9196875, "DCR_interaction": 0.125, "is_safe": true}
POST /api/tanks/api650/full-design → 200
   {"masses": {"m_i": 32790.273201916796, "m_c": 14057.119611404065}, "periods": {"T_i": 0.20325857915473083, "T_c": 4.671486179330775}, "base_shear": 9937.012006471767, "overturning_moment": 57162.429759888415, "anchorage": {"J": 1.9141876855550746, "N_bolts": 80, "type": "mechanically-anchored", "t_base_plate_mm": 30.0, "L_anchor_mm": 187.5}, "buckling": {"ratio": 0.0, "status": "safe", "governing_mode": "hoop", "DCR_axial": 0.0, "DCR_hoop": 0.9196875, "alpha_diamond": 0.16666666666666666}, "memo_md": "<1632 caracteres de Markdown>"}
   periods: {'T_i': 0.203, 'T_c': 4.671} | anchorage: {'J': 1.914, 'N_bolts': 80, 'type': 'mechanically-anchored', 't_base_plate_mm': 30.0, 'L_anchor_mm': 187.5}
POST /api/industrial/silos/janssen → 200
   {"slenderness": "slender", "aspect_ratio_hc_over_dc": 3.0, "p_hf_filling_horizontal_kPa": 32.49840246130891, "p_vf_filling_vertical_kPa": 60.18222678020168, "C_h_discharge_factor": 1.15, "C_w_discharge_factor": 1.1, "p_he_discharge_horizontal_kPa": 37.373162830505244, "code": "EN 1991-4:2006 §1.5.31-33 / §5.2 / §5.3"}

D = 0 en full-design → 422 (validación Pydantic)
3 pernos en anchorage → 422 (422: n_bolts >= 4 en el esquema)
```

</details>

## Verificación

- Valores calculados a mano con las fórmulas de API 650 Anexo E: fracciones y alturas de Housner en las dos ramas de D/H, T_i de §E.4.5.1 con C_i interpolado (0,227 s para el tanque de 20 m × 15 m × 8 mm), T_c = 1,8·K_s·√D, SRSS del cortante y del momento, w_a del anillo de fondo y J con fuerzas por unidad de perímetro (`tests/test_api650_annex_e_closed_form.py`).
- Fichas del máster UPC: tracción anular 500 kN/m (W01046/W01096/W01112), Janssen con z_o, p_ho, p_hf, p_vf, p_wf (W00225), esfera ASME (W00262); método del pie y Tabla 5.6a; placa base con llave de cortante bajo P, V, M completos.
- ACI 318-19 cap. 17 con la derivación de k_c = 10 en SI (N_b = 259,8 kN para f'c = 25 MPa y h_ef = 300 mm) y los modos que no aplican distinguidos de los no calculados; tests de «no aprueba en silencio» para capacidades nulas, espesores negativos y estados de carga fuera del método.
- Correcciones de esta revisión (0.2.0, ver CHANGELOG): T_i sin el factor 1/√2000 ni √(t_u/D) (0,006 s); ramas de tanque esbelto y X_c de la norma; momentos sumados linealmente en vez de SRSS; J dividido por el peso total (factor π·D) y memoria que usaba el peso del líquido como peso estabilizante; fracción convectiva de ASCE 7 con D/H invertido y S_ac sin el factor 1,5; tracción anular comparada con una tensión crítica de pandeo a presión exterior; Janssen de `silos_en1991_4` sin el factor K; k_c = 17 para hormigón no fisurado en `anchor_codes`.

## Limitaciones

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

## Normas y referencias

- API 650 (13.ª ed., 2020): §5.6.3.2, Tabla 5.6a, §5.9.7, §5.10.3, Anexo E (§E.4.5.1, §E.4.5.2, §E.4.6, §E.6.1, §E.6.2).
- ASCE 7-22 §15.7.6; ACI 350.3-20 §9.3.
- Housner, G. W. (1963), BSSA 53(2); Malhotra, Wenk y Wieland (2000), SEI 10(3) (tabla de C_i, recogida en EN 1998-4 Anexo A Tabla A.2); Rotter, J. M. (1997).
- ASME BPVC Sección VIII Div. 1 UG-28 y UG-32.
- EN 1991-4:2006 §1.5.31-33, §5.2, §5.3, §5.2.4, Anexo G, Tabla E.1; EN 1993-1-6 Anexo D.
- EN 1991-1-4 §7.13, Tabla 4.1 y Anexo E; DIN EN 13084.
- EN 1993-1-1 §6.3.3 y Anexo B Tabla B.1.
- UFC 3-340-02 (respuesta SDOF de estructuras protectoras).
- Salmon, C. G. y Johnson, J. E., Steel Structures (1996) §14; AISC Design Guide 1; ACI 318-19 cap. 17; EN 1992-4; AS 5216.
- AISC 360-16 Cap. I; EN 1994-1-1 §6.2, §6.6.1.2; ASCE 7-16 y EN 1990 (combinaciones).
- Fichas del máster de Ingeniería Estructural y de la Construcción (UPC) citadas por WorkID en los docstrings de `tests/`.

## Licencia

MIT. Consulta [LICENSE](LICENSE).

---

Parte de **Loadpath**, la colección de librerías estructurales de código abierto de [Jesús Murgas](https://github.com/jmurgass99).
