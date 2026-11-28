# T-507 · El exacto de Deslinde con K ≥ 5: medición en local

Fecha: 2026-11-26. Código: «antes» = `main` a1132d2e (Deslinde 1.1, worktree); «después» = la rama de #1035 en
d39fe3c (Deslinde 1.2; el motor es igual que en `main` 07f614de). En local, con el motor real. No se ha lanzado ni publicado nada.

## Método
- Entradas: `bateria_motor.py entradas --desde-fuente --seccionado shapefile`; seccionado 2023 y 2024 de www.ine.es en
  `DDD_ESPEJO_DIR` (sha256 comprobado contra `orchestracion/fuentes_r2.json`).
- Competición: `PYTHONHASHSEED=0 python -m ddd_motor2.competir` (D8, 10 cadenas), un territorio por ejecución.
- Candidatos: los 27 territorios con K ≥ 5, una circunscripción y sin exenciones, sacados de
  `Reglas.desde_contrato` sobre `territorios/*/config/*_2025.yaml` (#1035). Se han medido 25. nac48 (Vizcaya)
  falla antes de llegar al exacto (abajo). Madrid (nac28, aut13) no se puede medir en la nube.
- Reloj: segundos de pared con dos competiciones a la vez (antes y después en paralelo, 4 núcleos), así que es
  pesimista. Sevilla (nac41) sale de las pasadas de T-503, solo.
- `RESULTADOS.json` trae la clave D8 completa del ganador antes y después.

## Resultado

| Territorio | Tamaño (átomos × K) | Exacto | Demarcaciones partidas | Frontera (km) | Ganador | Reloj (s) | `huella_resultado` |
|---|---|---|---|---|---|---|---|
| nac03 | — | NO_APLICA (no cabe) | 12 → 12 | 728,5 → 728,5 | ponderado-s678287566 → ponderado-s678287566 | 108 → 108 | igual |
| nac04 | 624 | OPTIMO | 6 → 4 | 335,2 → 363,9 | ponderado-s1755548843 → exacto | 18 → 109 | **cambia** |
| nac06 | 996 | SIN_SOLUCION | 6 → 6 | 635,8 → 635,8 | ponderado-s1701933260 → ponderado-s1701933260 | 29 → 107 | **cambia** |
| nac12 | 680 | MEJOR_VALIDO | 3 → 3 | 217,9 → 196,3 | vigente → exacto | 30 → 161 | **cambia** |
| nac14 | 474 | OPTIMO | 6 → 5 | 528,1 → 621,2 | vigente → exacto | 36 → 70 | **cambia** |
| nac15 | 846 | MEJOR_VALIDO | 7 → 6 | 494,5 → 483,9 | ponderado-s1099375369 → exacto | 26 → 157 | **cambia** |
| nac17 | 1547 | SIN_SOLUCION | 7 → 7 | 434,1 → 434,1 | vigente → vigente | 44 → 87 | **cambia** |
| nac18 | 1400 | SIN_SOLUCION | 6 → 6 | 464,3 → 464,3 | ponderado-s401416052 → ponderado-s401416052 | 45 → 85 | **cambia** |
| nac20 | 534 | MEJOR_VALIDO | 3 → 3 | 190,3 → 190,3 | vigente → vigente | 30 → 149 | **cambia** |
| nac23 | 485 | OPTIMO | 5 → 5 | 573,4 → 524,2 | vigente → exacto | 29 → 95 | **cambia** |
| nac31 | 1638 | SIN_SOLUCION | 5 → 5 | 290,2 → 290,2 | vigente → vigente | 99 → 117 | **cambia** |
| nac33 | 640 | OPTIMO | 5 → 5 | 386,4 → 385,4 | vigente → exacto | 28 → 59 | **cambia** |
| nac39 | 515 | OPTIMO | 4 → 4 | 147,3 → 139,5 | vigente → exacto | 20 → 55 | **cambia** |
| nac41 | 1776 | MEJOR_VALIDO | 8 → 6 | 763,8 → 786,0 | ponderado-s1767573395 → exacto | 27 → 149 | **cambia** |
| nac43 | 1288 | MEJOR_VALIDO | 7 → 6 | 302,5 → 467,2 | ponderado-s1963930333 → exacto | 28 → 149 | **cambia** |
| nac45 | 1224 | SIN_SOLUCION | 7 → 7 | 584,4 → 584,4 | vigente → vigente | 33 → 69 | **cambia** |
| nac46 | — | NO_APLICA (no cabe) | 26 → 26 | 1088,4 → 1088,4 | ponderado-s1192842858 → ponderado-s1192842858 | 85 → 48 | igual |
| nac48 | — | NO_APLICA (canónico FALLO_GENERADOR) | — → — | — → — | canonico → canonico | 3 → 2 | igual |
| nac50 | — | NO_APLICA (no cabe) | 8 → 8 | 945,2 → 945,2 | canonico → canonico | 39 → 30 | igual |
| aut03 | — | NO_APLICA (no cabe) | 26 → 26 | 1243,0 → 1243,0 | ponderado-s1094054105 → ponderado-s1094054105 | 50 → 49 | igual |
| aut06 | — | NO_APLICA (no cabe) | 13 → 13 | 762,1 → 762,1 | ponderado-s1810203965 → ponderado-s1810203965 | 351 → 352 | igual |
| aut15 | — | NO_APLICA (no cabe) | 12 → 12 | 1614,4 → 1614,4 | ponderado-s312090555 → ponderado-s312090555 | 383 → 387 | igual |
| aut17 | — | NO_APLICA (no cabe) | 7 → 7 | 563,0 → 563,0 | ponderado-s1667786157 → ponderado-s1667786157 | 35 → 34 | igual |
| aut18 | 625 | OPTIMO | 1 → 1 | 36,8 → 36,8 | canonico → canonico | 267 → 268 | **cambia** |
| aut19 | 625 | OPTIMO | 1 → 1 | 38,5 → 38,5 | ponderado-s524912015 → ponderado-s524912015 | 70 → 70 | **cambia** |

- **Ninguno empeora**: en todos, la clave D8 del ganador después es menor o igual que antes. Es así por construcción,
  porque el exacto solo gana si su clave es mejor.
- **Ninguno pasa de 10 min**: el máximo es nac12, con 161 s. `TAMANO_MAX = 2.000` se mantiene.
- **Gana el exacto** en 9: nac04, nac12, nac14, nac15, nac23, nac33, nac39, nac41, nac43. Baja las demarcaciones partidas en nac04 (6 → 4), nac14 (6 → 5), nac15
  (7 → 6), nac41 (8 → 6) y nac43 (7 → 6). En los demás donde gana, empata en demarcaciones y mejora la frontera.
- **SIN_SOLUCION** en nac06, nac17, nac18, nac31 y nac45: el exacto no encuentra un plan dentro de su tope determinista.
  Cuesta tiempo (hasta +78 s) y cambia la huella, pero no el ganador.
- **No caben** (NO_APLICA con el motivo literal «K=… fuera de 2..4»): nac03, nac46, nac50, aut03, aut06, aut15 y aut17.
  Su huella no cambia.
- **aut18 y aut19** (K = 25, 25 átomos): el exacto aplica y demuestra el óptimo, pero no cambia el ganador; cambia la huella.
- **nac48** (Vizcaya) da FALLO_M04 en el canónico, antes y después, con las entradas de la nube. Sin composición del
  canónico, el exacto es NO_APLICA y la huella no cambia. Es un fallo previo e independiente de T-503: en una 00 con
  entradas buenas, el exacto aplicaría si cabe. **No está medido.**

## Madrid (nac28, aut13): no se puede medir en local
`bateria_motor.py entradas` da FALLO_ADQUISICION en la nube (fallo conocido). **No aplican**, y no hace falta medirlas:
- Cada átomo es de un solo municipio, y Madrid tiene 178 (`configuracion/partidos_judiciales.csv`, sha256 ae00cf82…).
  Por tanto, el tamaño es al menos 178 × 59 = 10.502 (nac28) y 178 × 135 = 24.030 (aut13), por encima de 2.000.
- Aunque hubiera menos átomos, caber exigiría menos átomos que distritos (átomos ≤ 2.000 / K < K), y entonces no
  existe ningún plan. El exacto no podría aportar un ganador.

## Territorios con `huella_resultado` nueva (para la P30 y la republicación del 29-11)
nac04, nac06, nac12, nac14, nac15, nac17, nac18, nac20, nac23, nac31, nac33, nac39, nac41, nac43, nac45, aut18, aut19 (17). La huella `motor2` cambia en todos, porque cambia el código. El ganador cambia en 9:
nac04, nac12, nac14, nac15, nac23, nac33, nac39, nac41, nac43. Hay que rehacer la P30 y volver a publicar esos territorios, con permiso del propietario.

## La lista de candidatos está completa
La lista de 27 de #1035 sale de las mismas condiciones que `exacto.aplicable` (una circunscripción, sin exenciones de
suelo ni techo). Todo territorio con K ≥ 5 fuera de ella da, por código, NO_APLICA con el motivo literal de la 1.0.0, y
su huella no cambia. Esos no se han medido. La medición confirma que de los 27 solo cambian los que caben.

## Coste
Unos 70 min de CPU en local: entradas (unos 6 min) y 2 × 25 competiciones.
