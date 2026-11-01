# plantstruct — strutture di impianti industriali: serbatoi API 650, silos EN 1991-4, ciminiere, sfere, pipe rack, basi di colonna e travi composte

[Español](README.md) · [English](README.en.md) · [Português](README.pt.md) · **Italiano**

Calcolo delle strutture di impianti di processo in Python puro con `numpy` come unica dipendenza: serbatoi atmosferici API 650 (virole con il metodo del piede, trazione anulare, instabilità del mantello, pressione esterna, masse di Housner dell'Allegato E con periodi, taglio e momento SRSS, rapporto di ancoraggio J e tirafondi, relazione completa, modello a stick per SAP2000 e la variante ASCE 7-22 §15.7), silos EN 1991-4 (Janssen, classi di snellezza, fattori di scarico, carico localizzato, canale di flusso e instabilità meridiana EN 1993-1-6), ciminiere (distacco di vortici), sfere di GPL (ASME VIII), pipe rack, capannoni (vento EN 1991-1-4 e pressoflessione EN 1993-1-1), muri antiesplosione SDOF, basi di colonna con i quattro modi di rottura dell'ancoraggio della ACI 318-19 cap. 17 e tacco a taglio, ancoraggi multinorma e travi composte di soppalco secondo AISC 360 ed EN 1994. Ogni risultato dice quali ipotesi contiene e quando non ha potuto verificare.

[![CI](https://github.com/jmurgass99/plantstruct/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/plantstruct/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Quale problema risolve

Le strutture degli impianti (serbatoi, silos, rack, ciminiere, basamenti di apparecchiature) si calcolano con formule di norma che stanno in un foglio di calcolo ma che si rifanno a mano in ogni progetto, con unità miste e senza tracciabilità. Il pacchetto le raccoglie con le equazioni citate per clausola, valori di riferimento calcolati a mano nei test e una politica esplicita contro l'approvazione silenziosa: se manca un dato, il modo corrispondente esce `NO_CALCULADO` e il giudizio non può essere favorevole.

**Usalo quando**

- dimensioni o verifichi un serbatoio API 650: spessore delle virole, trazione anulare, compressione del mantello, vuoto, sisma dell'Allegato E (masse, periodi, momento ribaltante, ancoraggio J, tirafondi) e vuoi la relazione in Markdown o alimentare un modello SAP2000;
- ti servono le pressioni della EN 1991-4 in un silo (riempimento, scarico, carico localizzato, canale di flusso) e la resistenza all'instabilità della parete per classe di qualità;
- predimensioni ciminiere, sfere di GPL, pipe rack o un muro antiesplosione e vuoi sapere quale parte è norma e quale è stima;
- verifichi una piastra di base con tirafondi a trazione secondo ACI 318-19 cap. 17 (acciaio, cono, sfilamento, rottura laterale) e tacco a taglio;
- progetti travi composte di soppalco industriale secondo AISC 360-16 Cap. I o EN 1994-1-1 con connessione parziale.

**Non usarlo per**

- serbatoi oltre i 60 m (metodo del punto di progetto variabile, API 650 §5.6.4), tetti galleggianti, fondi e fondazioni dei serbatoi;
- silos con tramoggia (pressioni nella tramoggia, §6), scarico eccentrico dettagliato (§5.2.4.3) o silos in calcestruzzo;
- ampiezza della vibrazione da vortici (numero di Scruton, EN 1991-1-4 eq. E.7): `chimneys` dà solo la condizione di risonanza ed è marcato sperimentale;
- taglio sui tirafondi (ACI 318-19 §17.7) e interazione trazione-taglio (§17.8): il modulo affida il taglio all'attrito e al tacco;
- sollecitazioni nel guscio delle sfere per sisma o vento: `esferas_gpl` copre lo spessore per pressione e la ripartizione alle colonne.

## Installazione

```bash
pip install git+https://github.com/jmurgass99/plantstruct.git
pip install "plantstruct[api] @ git+https://github.com/jmurgass99/plantstruct.git"   # API REST con FastAPI
```

Per lo sviluppo: `git clone`, `pip install -e ".[test,api]"`, `pytest -q` (25 file di test). Su Windows, se la console non è UTF-8, esegui gli esempi con `python -X utf8 examples/<nome>.py`.

## Funzionalità

| Funzionalità | Moduli | Norma o riferimento | Casi d'uso |
|---|---|---|---|
| Serbatoi API 650, mantello: spessore delle virole con il metodo del piede, trazione anulare, instabilità assiale con α delle imperfezioni e knockdown di Rotter, trazione anulare contro S_d, pressione esterna e irrigidimenti | `tanks.shell_design`, `tanks.shell_buckling`, `external_pressure` | API 650 §5.6.3.2, Tabella 5.6a, §5.10.3, §5.9.7; ASME VIII Div. 1 UG-28; Rotter 1997; schede W01046/W01096/W01112 | [5 casi](#1-serbatoi-api-650-mantello) |
| Serbatoi API 650, sisma: pesi di Housner, altezze, T_i e T_c, taglio e momento SRSS, rapporto J, tirafondi, relazione completa, modello a stick per SAP2000, ASCE 7-22 §15.7 | `tanks.api650`, `tanks.anchorage`, `asce7_15_7`, `memos.tank_complete`, `integration.fastsap_tank_parametric` | API 650 Allegato E (§E.4.5, §E.6.1, §E.6.2); ASCE 7-22 §15.7.6; Housner 1963; Malhotra 2000 / EN 1998-4 Tabella A.2 | [7 casi](#2-serbatoi-api-650-sisma) |
| Silos EN 1991-4: Janssen, classi di snellezza, C_h/C_w, carico localizzato, canale di flusso, instabilità meridiana per classe di qualità | `silos_en1991_4`, `ec1_silos`, `silo_buckling` | EN 1991-4:2006 §1.5, §5.2, §5.3, Allegato G, Tabella E.1; EN 1993-1-6 Allegato D; scheda W00225 | [5 casi](#3-silos-en-1991-4) |
| Altre strutture di impianto: ciminiere, sfere di GPL, pipe rack, capannoni (vento e pressoflessione), muri antiesplosione SDOF | `chimneys`, `esferas_gpl`, `pipe_rack`, `portal_frame`, `bunker` | EN 1991-1-4 §7.13 e Allegato E; ASME VIII Div. 1 UG-32; EN 1991-1-4 Tabella 4.1; EN 1993-1-1 §6.3.3 e Allegato B; UFC 3-340-02; scheda W00262 | [5 casi](#4-altre-strutture-di-impianto) |
| Basi di colonna e ancoraggi: piastra secondo Salmon & Johnson / AISC DG1, tirafondi a trazione con i quattro modi della ACI 318-19 §17.6, tacco a taglio, cono multinorma | `bases_columna`, `anchor_codes` | Salmon & Johnson §14; AISC Design Guide 1; ACI 318-19 §17.6 (k_c = 10 in SI); EN 1992-4 §7.2.1.4; AS 5216 §6.2.1 | [6 casi](#5-basi-di-colonna-e-ancoraggi) |
| Travi composte di soppalco industriale e API REST | `composite_beams` (routine incluse in `_composite/`), `api` | AISC 360-16 Cap. I (§I3.2, §I3.2d); EN 1994-1-1 §6.2, §6.6.1.2, eq. 6.28; ASCE 7-16 / EN 1990 combinazioni | [5 casi](#6-travi-composte-e-api-rest) |

I 33 script di `examples/` sono stati eseguiti in un ambiente pulito prima della pubblicazione; il loro output è in `examples/output/` ed è quello riprodotto qui.

## Casi d'uso

Gli output sono riportati esattamente come li stampano gli script, in spagnolo.

### 1. Serbatoi API 650, mantello

#### Spessore di ogni virola con il metodo del piede in un serbatoio d'acqua da 20 m e in uno di greggio da 36 m

t_d = 4,9·D·(H − 0,3)·G/S_d + CA e t_t = 4,9·D·(H − 0,3)/S_t con il minimo nominale della Tabella 5.6a; `governing` dice cosa governa in ogni anello.

<details><summary>Output reale di <code>python examples/api650_shell_courses_one_foot_method_water_and_oil_tanks.py</code></summary>

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

#### Trazione circonferenziale di membrana: T = γ·(H − y)·r = 500 kN/m alla base (scheda W01046)

<details><summary>Output reale di <code>python examples/hoop_tension_cylindrical_tank_W01046_500kN_per_m.py</code></summary>

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

#### Mantello in compressione e in trazione: instabilità assiale API 650, scarto rispetto a Rotter in funzione di R/t e trazione anulare contro S_d

La trazione anulare idrostatica si confronta con la tensione ammissibile, non con una tensione critica di instabilità; il DCR assiale per la via di Rotter si pubblica accanto a quello della norma.

<details><summary>Output reale di <code>python examples/shell_buckling_basic_vs_full_rotter_gap_vs_R_over_t.py</code></summary>

```text
D = 20 m, H_manto = 16 m, H_líquido = 15 m, σ_axial = 15.0 MPa, σ_flexión = 10.0 MPa, S_d = 160 MPa

  t [mm]    R/t Fbi API [MPa]  DCR_ax α_Rotter DCR_ax,Rotter  brecha σ_hoop [MPa] DCR_hoop DCR_flex        manda seguro
       6   1667          72.0   0.208    0.107         1.167    5.60        245.2    1.533  222.222  interaction False
       8   1250          96.0   0.156    0.138         0.680    4.35        183.9    1.150  125.000  interaction False
      12    833         144.0   0.104    0.194         0.323    3.10        122.6    0.766   55.556  interaction False
      20    500         240.0   0.062    0.286         0.131    2.10         73.6    0.460   20.000  interaction False

`axial_basis` = API650_alpha_imperfection: el veredicto usa α = 0,6; la columna de Rotter es la otra lectura de la misma demanda.
Con 6 y 8 mm manda la tracción anular (σ_hoop > S_d: hace falta el espesor del método del pie, 10,5 mm en la primera virola); con 12 y 20 mm el manto cumple y el axial queda holgado por la ruta API, no tanto por la de Rotter.
```

</details>

#### Pressione esterna (vuoto): pressione critica, coefficiente di sicurezza per norma e distanza massima tra gli irrigidimenti

<details><summary>Output reale di <code>python examples/external_pressure_vacuum_stiffener_spacing_by_code.py</code></summary>

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

#### Limite del metodo del piede (D ≤ 60 m) e come la relazione lo dichiara invece di approvare in silenzio

<details><summary>Output reale di <code>python examples/one_foot_method_limit_D_over_60m_and_memo_not_evaluated.py</code></summary>

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

### 2. Serbatoi API 650, sisma

#### Serbatoio di 20 m × 15 m: pesi di Housner, altezze, T_i e T_c, taglio e momento SRSS con mantello e tetto

Verificato a mano: W_i/W_p = 0,7096, W_c/W_p = 0,3042, X_c/H = 0,6803, T_i = 0,227 s (fino alla 0.2.0 il pacchetto dava 0,006 s), T_c = 4,67 s.

<details><summary>Output reale di <code>python examples/api650_annex_e_housner_masses_periods_T_i_T_c_20m_tank.py</code></summary>

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

#### Periodo impulsivo e convettivo per cinque serbatoi con H/D da 0,2 a 2,0 e il coefficiente C_i della Fig. E.1

<details><summary>Output reale di <code>python examples/api650_impulsive_period_sweep_H_over_D_and_C_i_table.py</code></summary>

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

#### Lo stesso serbatoio con API 650 Allegato E e con ASCE 7-22 §15.7: pesi uguali, tagli diversi per i fattori R

<details><summary>Output reale di <code>python examples/api650_vs_asce7_15_7_same_tank_base_shear.py</code></summary>

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

#### Rapporto di ancoraggio J (§E.6.2.1.1.1) con forze per unità di circonferenza: da autoancorato ad ancoraggio meccanico al crescere di A_i

<details><summary>Output reale di <code>python examples/api650_anchorage_J_ratio_classification_vs_A_i.py</code></summary>

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
F_p = 4·M_rw/D − W_t·(1 − 0,4·A_v) es el levantamiento total para anclaje mecánico (§E.6.2.1.2); el número de pernos usa φ·A_b·F_y.
```

</details>

#### Tirafondi: carico per tirafondo, capacità e numero necessario per tre disposizioni

<details><summary>Output reale di <code>python examples/api650_anchor_bolts_uplift_per_bolt_and_required_count.py</code></summary>

```text
M_rw = 29,601 kN·m, W_t = 900 kN → levantamiento total 4·M/D − W_t = 5,020 kN

   N_b  perno F_y [MPa] P_AB [kN] cap. [kN]    DCR seguro  N_b mínimo
    24    M30       250     209.2     106.0   1.97  False          48
    48    M36       250     104.6     152.7   0.69   True          33
    32    M36       400     156.9     244.3   0.64   True          21

W_tank_kN es el peso de manto + techo + accesorios: con el peso del líquido en su lugar el levantamiento sale cero y el anclaje «cumple» sin calcular nada.
```

</details>

#### Relazione completa in Markdown: geometria, Housner, spessore, ancoraggio, instabilità e giudizio

<details><summary>Output reale di <code>python examples/api650_complete_tank_memo_markdown.py</code></summary>

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

#### Modello a stick di Housner per SAP2000 (massa convettiva su molla k_c = m_c·ω_c²) e mesh parametrica del mantello

<details><summary>Output reale di <code>python examples/housner_stick_model_for_sap2000_and_parametric_shell_mesh.py</code></summary>

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

#### Pressioni di riempimento di Janssen in un silo di grano di 6 m × 18 m (scheda W00225)

<details><summary>Output reale di <code>python examples/silo_janssen_pressures_wheat_EN1991_4_W00225.py</code></summary>

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

#### Classe di snellezza e fattori di scarico C_h, C_w per quattro altezze dello stesso silo

<details><summary>Output reale di <code>python examples/silo_slenderness_classes_and_discharge_factors_C_h_C_w.py</code></summary>

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

#### Carico localizzato di riempimento e pressione nel canale di flusso di un silo snello

<details><summary>Output reale di <code>python examples/silo_patch_load_and_flow_funnel_slender_silo.py</code></summary>

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

#### Instabilità meridiana della parete con la compressione trasmessa dall'attrito del grano, per classe di qualità A/B/C

<details><summary>Output reale di <code>python examples/silo_wall_meridional_buckling_EN1993_1_6_quality_classes.py</code></summary>

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

#### Sensibilità a K e μ e coerenza delle due routine di Janssen del pacchetto

<details><summary>Output reale di <code>python examples/silo_two_implementations_consistency_and_K_mu_sensitivity.py</code></summary>

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

### 4. Altre strutture di impianto

#### Ciminiera di 40 m: frequenza propria, velocità critica dei vortici e banda di rischio (sperimentale)

<details><summary>Output reale di <code>python examples/steel_chimney_vortex_shedding_critical_wind_speed.py</code></summary>

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

#### Sfera di GPL di 20 m a 17,5 bar: spessore ASME VIII UG-32, carico per colonna e taglio alla base preliminare

<details><summary>Output reale di <code>python examples/lpg_sphere_asme_viii_thickness_columns_and_base_shear.py</code></summary>

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

#### Pipe rack a due e tre livelli: pesi, momento da attrito termico e taglio alla base preliminare

<details><summary>Output reale di <code>python examples/pipe_rack_loads_thermal_moment_and_base_shear_preliminary.py</code></summary>

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

#### Capannone: pressione di picco del vento per categoria di terreno e pressoflessione di una colonna IPE 400 con il k_y dichiarato

<details><summary>Output reale di <code>python examples/portal_frame_wind_pressure_terrain_categories_and_member_interaction_IPE400.py</code></summary>

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

tracción: ValueError → check_steel_member_interaction: N_Ed_kN=-300 kN es TRACCIÓN, y EN 1993-1-1 §6.3.3 cubre 'members in bending an…

χ_y ausente: ValueError → check_steel_member_interaction: chi_y debe proporcionarse explícitamente. No se asumen factores de reducción p…
```

</details>

#### Muro antiesplosione come SDOF elastoplastico: domanda di duttilità in regime impulsivo e rotazione all'appoggio

<details><summary>Output reale di <code>python examples/blast_wall_sdof_ductility_demand_impulsive_asymptote.py</code></summary>

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

### 5. Basi di colonna e ancoraggi

#### Piastra di base con piccola eccentricità (e ≤ N/6): dimensioni, spessore e nessuna trazione nei tirafondi

<details><summary>Output reale di <code>python examples/column_base_plate_small_eccentricity_salmon_johnson.py</code></summary>

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

#### Grande eccentricità con la geometria completa dell'ancoraggio: i quattro modi della ACI 318-19 §17.6 e quello che governa

<details><summary>Output reale di <code>python examples/column_base_plate_large_eccentricity_aci318_17_anchor_modes.py</code></summary>

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
Los φ (0,75 acero, 0,70 hormigón) son entrada fija del módulo sin armadura suplementaria; §17.7 (cortante en anclajes) no se comprueba: el cortante va a fricción y llave.
```

</details>

#### La stessa base senza la geometria dell'ancoraggio: NO_VERIFICADO con l'elenco esatto di ciò che manca

<details><summary>Output reale di <code>python examples/column_base_missing_anchor_geometry_is_not_verified.py</code></summary>

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

#### Tacco a taglio: quando serve e che capacità ha (caso golden del pacchetto)

<details><summary>Output reale di <code>python examples/column_base_shear_lug_required_when_friction_insufficient.py</code></summary>

```text
μ = 0.20: fricción μ·P = 120 kN frente a V = 180 kN → llave requerida: True
  llave 200 × 75 × 25 mm: aplastamiento 207 kN, cortante chapa 562 kN → is_ok = True
  placa N = 400, B = 300, t = 24.5 mm; T_u = 0.0 kN; estado VERIFICADO, cumple = True

μ = 0.40: fricción μ·P = 240 kN frente a V = 180 kN → llave requerida: False
  placa N = 400, B = 300, t = 24.5 mm; T_u = 0.0 kN; estado VERIFICADO, cumple = True

dims_source: ENTRADA FIJA: altura 75 mm y espesor 25 mm son constantes del modulo, NO un dimensionamiento. Solo el ancho se ata a la geometria de la plac…
```

</details>

#### Cono di calcestruzzo di un ancoraggio isolato in ACI 318-19, EN 1992-4 e AS 5216

<details><summary>Output reale di <code>python examples/anchor_concrete_cone_capacity_multi_code_US_EU_AU.py</code></summary>

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

#### Base con trazione netta (P ≤ 0): il modulo non dimensiona per pressione di contatto e lo dichiara

<details><summary>Output reale di <code>python examples/column_base_uplift_P_le_0_honest_not_verified.py</code></summary>

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

### 6. Travi composte e API REST

#### Trave composta di soppalco industriale secondo AISC 360-16: W460x74 su 9 m con connettori dimensionati automaticamente

<details><summary>Output reale di <code>python examples/composite_mezzanine_beam_AISC_360_W460x74_auto_studs.py</code></summary>

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

#### Trave composta secondo EN 1994-1-1: IPE 450 S355 con connessione parziale e il minimo del §6.6.1.2

<details><summary>Output reale di <code>python examples/composite_mezzanine_beam_EN1994_IPE450_partial_interaction.py</code></summary>

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

#### Ripartizione dei carichi: fase costruttiva contro fase composta, puntellata o no, con carico concentrato di un'apparecchiatura

<details><summary>Output reale di <code>python examples/composite_beam_loads_breakdown_construction_vs_composite_stage.py</code></summary>

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

#### Quanti connettori servono: capacità, freccia e modo governante in funzione del numero di connettori

<details><summary>Output reale di <code>python examples/composite_beam_stud_count_sensitivity_and_governing_mode.py</code></summary>

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

#### API REST senza server: Housner, ancoraggio, instabilità, progetto completo API 650 e Janssen dei silos

<details><summary>Output reale di <code>python examples/rest_api_tanks_api650_full_design_and_silos_janssen_testclient.py</code></summary>

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

## Verifica

- Valori calcolati a mano con le formule della API 650 Allegato E: frazioni e altezze di Housner nei due rami di D/H, T_i del §E.4.5.1 con C_i interpolato (0,227 s per il serbatoio di 20 m × 15 m × 8 mm), T_c = 1,8·K_s·√D, SRSS del taglio e del momento, w_a dell'anello di fondo e J con forze per unità di circonferenza (`tests/test_api650_annex_e_closed_form.py`).
- Schede del master UPC: trazione anulare 500 kN/m (W01046/W01096/W01112), Janssen con z_o, p_ho, p_hf, p_vf, p_wf (W00225), sfera ASME (W00262); metodo del piede e Tabella 5.6a; piastra di base con tacco a taglio sotto P, V, M completi.
- ACI 318-19 cap. 17 con la derivazione di k_c = 10 in SI (N_b = 259,8 kN per f'c = 25 MPa e h_ef = 300 mm) e i modi non applicabili distinti da quelli non calcolati; test di «nessuna approvazione silenziosa» per capacità nulle, spessori negativi e stati di carico fuori dal metodo.
- Correzioni di questa revisione (0.2.0, vedi CHANGELOG): T_i senza il fattore 1/√2000 né √(t_u/D) (0,006 s); rami del serbatoio snello e X_c della norma; momenti sommati linearmente invece che con la SRSS; J diviso per il peso totale (fattore π·D) e relazione che usava il peso del liquido come peso stabilizzante; frazione convettiva della ASCE 7 con D/H invertito e S_ac senza il fattore 1,5; trazione anulare confrontata con una tensione critica di instabilità da pressione esterna; Janssen di `silos_en1991_4` senza il fattore K; k_c = 17 per calcestruzzo non fessurato in `anchor_codes`.

## Limitazioni

- `Sa_i` e `Sa_c` sono i coefficienti A_i e A_c già divisi per R_w/I: il pacchetto non costruisce lo spettro della API 650 §E.4.6 a partire da S_S, S_1 e classe del sito.
- Il momento ribaltante è quello alla base del mantello (ringwall): non include la pressione sul fondo (M_s del §E.6.1.5-2) né il peso del fondo.
- `check_anchorage` usa 0,6·F_y come capacità del tirafondo (la norma ammette 0,8·F_y) e `check_anchorage_J` dimensiona la sedia con formule semplificate; la verifica di autoancoraggio con sollevamento (L e t_a del §E.6.2.1.1.2) non c'è.
- L'instabilità assiale del mantello è α·E·t/R con α = 0,6; la formula di F_C del §E.6.2.2.3 (83·t_s/D o il ramo GHD²/t²) non è implementata. Il knockdown di Rotter si pubblica ma non governa.
- `asce7_15_7` assume T_i = 0 se non si fornisce lo spessore e non valuta S_ai oltre T_L; i fattori R sono dati in ingresso.
- `chimneys`, `esferas_gpl` e `pipe_rack` sono predimensionamento con coefficienti sismici di screening (C_s fisso per norma), senza spettro.
- `portal_frame.check_steel_member_interaction` usa k_y = min(1 + 0,6·n, 1,4), equivalente alla Tabella B.1 con C_my = 1 e λ̄_y = 0,8 fissi; per colonne più snelle sottostima k_yy e il risultato lo dichiara in `k_y_basis`.
- `bases_columna`: la capacità dell'acciaio del tirafondo è lo snervamento sull'area lorda (non A_se·f_uta del §17.6.1.2); il tacco a taglio ha altezza e spessore fissi; §17.7 e §17.8 non si verificano; con P ≤ 0 non si ricava la domanda di trazione.
- `anchor_codes` copre solo il cono di un ancoraggio senza bordi moltiplicato per il numero di ancoraggi.
- Le travi composte presuppongono campata semplice, carico uniforme più un concentrato in mezzeria, lamiera perpendicolare con una fila di connettori; la freccia con connessione parziale usa l'approssimazione della AISC I3.2 anche nel ramo EN 1994.
- `report_api650` è uno scheletro delle sezioni dell'Allegato E, non una relazione calcolata: la relazione calcolata è `memos.render_tank_memo`.

## Norme e riferimenti

- API 650 (13ª ed., 2020): §5.6.3.2, Tabella 5.6a, §5.9.7, §5.10.3, Allegato E (§E.4.5.1, §E.4.5.2, §E.4.6, §E.6.1, §E.6.2).
- ASCE 7-22 §15.7.6; ACI 350.3-20 §9.3.
- Housner, G. W. (1963), BSSA 53(2); Malhotra, Wenk e Wieland (2000), SEI 10(3) (tabella di C_i, riportata nella EN 1998-4 Allegato A Tabella A.2); Rotter, J. M. (1997).
- ASME BPVC Sezione VIII Div. 1 UG-28 e UG-32.
- EN 1991-4:2006 §1.5.31-33, §5.2, §5.3, §5.2.4, Allegato G, Tabella E.1; EN 1993-1-6 Allegato D.
- EN 1991-1-4 §7.13, Tabella 4.1 e Allegato E; DIN EN 13084.
- EN 1993-1-1 §6.3.3 e Allegato B Tabella B.1.
- UFC 3-340-02 (risposta SDOF delle strutture di protezione).
- Salmon, C. G. e Johnson, J. E., Steel Structures (1996) §14; AISC Design Guide 1; ACI 318-19 cap. 17; EN 1992-4; AS 5216.
- AISC 360-16 Cap. I; EN 1994-1-1 §6.2, §6.6.1.2; ASCE 7-16 ed EN 1990 (combinazioni).
- Schede del Master in Ingegneria Strutturale e delle Costruzioni (UPC) citate per WorkID nelle docstring di `tests/`.

## Licenza

MIT. Vedi [LICENSE](LICENSE).

---

Parte di **Loadpath**, la raccolta di librerie strutturali open source di [Jesús Murgas](https://github.com/jmurgass99).
