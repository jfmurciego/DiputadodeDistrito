# T-270 · Medición de Deslinde con el motor optimizado (INFORME PARCIAL)

**Estado: PARCIAL.** Se paró por orden del Coordinador (cuota al 100 %). Falta lo indicado en «Pendiente y cómo reanudar».
Solo se ha medido en local; el motor no cambia. Máquina: sesión cloud, 4 CPU, Python 3.13, `requirements.lock` +
gerrychain 1.0.0 `--no-deps`, `PYTHONHASHSEED=0`, 10 cadenas, D8. «Después» = `main` 478e89a (incluye #723 #724 #727
#730 #731 #734 #736). «Antes» = `ee8e776` (commit de T-254), mismas entradas, 1 repetición, con `medir.py` de T-254.

**Entradas desde fuente** (`bateria_motor.py entradas`, no artefactos de Actions). Sevilla y Valencia del Congreso
y Andalucía con `--seccionado shapefile`. Madrid del Congreso, Madrid y Barcelona del Congreso con el seccionado OGC del
INE (ruta de producción): con el shapefile, Madrid falla la adquisición (`GEOMETRY_INVALID_AUDITED`, provincia 28) y en
Barcelona del Congreso el M04 se para («invalid administrative component source binding»: municipios no conexos sin
acreditación topológica). Con OGC, los dos van bien.

Territorios (id actual; código oficial entre paréntesis según la tabla maestra, pendiente de comprobar en la versión final):
congreso_sevilla, congreso_valencia, congreso_barcelona, congreso_madrid, andalucia, madrid.

## 1. Tiempo por fase, después (media ± desviación típica, s; 3 repeticiones)

| Fase | congreso_sevilla | congreso_valencia | congreso_barcelona | congreso_madrid | andalucia | madrid |
|---|---|---|---|---|---|---|
| Exhaustivo (cota, no se lanza) | 0,97 ± 0,06 | 0,58 ± 0,09 | 0,49 ± 0,01 | 0,57 ± 0,11 | 1,32 ± 0,09 | 0,60 ± 0,07 |
| Cadenas (10) | 6,08 ± 0,31 | 11,39 ± 0,40 | 15,13 ± 0,31 | 10,58 ± 0,27 | 177,79 ± 8,42 | **356,80 ± 17,13** |
| Canónico (subprocesos) | 16,52 ± 0,48 | 34,04 ± 1,99 | 82,47 ± 1,66 | **253,37 ± 1,95** | **343,04 ± 4,62** | **311,69 ± 5,15** |
| — M04 | 10,13 | 25,87 | 70,80 | **240,97** | 49,13 | **280,13** |
| — M05 | 3,33 | 4,43 | 7,10 | 7,00 | **279,90** | 25,87 |
| — M06 + validación | 2,80 | 3,50 | 4,30 | 5,17 | 13,50 | 5,43 |
| Elección D8 (`juzgar`) | 1,79 | 2,66 | 3,19 | 3,84 | 14,20 | 6,08 |
| Vigente | 0,31 | 0,51 | 0,51 | 0,66 | 3,21 | 1,17 |
| **Total** | **25,71 ± 0,37** | **49,19 ± 2,08** | **101,81 ± 2,02** | **269,04 ± 1,94** | **539,58 ± 13,31** | **676,38 ± 14,56** |

En los 6, las 3 repeticiones dan las mismas huellas (ganador y sha256 de cada composición).
Ganadores: cadena en 5, «vigente» en congreso_madrid.

## 2. Antes / después (total de la competición, s)

| Territorio | Antes (ee8e776) | Después (main) | Exhaustivo antes → después | Cadenas antes → después |
|---|---|---|---|---|
| congreso_huesca (T-254) | 114,11 | 23,03 | 92,61 → 1,27 | 14,62 → 12,98 |
| congreso_la_rioja (T-254) | 143,90 | 20,92 | 124,68 → 2,04 | 13,69 → 11,69 |
| la_rioja (T-254) | 84,08 | 32,91 | 50,90 → 0,27 | 24,13 → 20,85 |
| congreso_sevilla | 69,08 | 25,71 | 41,92 → 0,97 | 8,31 → 6,08 |
| congreso_valencia | 107,95 | 49,19 | 54,91 → 0,58 | 15,53 → 11,39 |
| congreso_barcelona | 178,97 | 101,81 | 71,64 → 0,49 | 19,89 → 15,13 |
| congreso_madrid | 342,48 | 269,04 | 49,49 → 0,57 | 14,19 → 10,58 |
| andalucia | 784,49 | 539,58 | 184,87 → 1,32 | 249,28 → 177,79 |
| madrid | 960,13 | 676,38 | 58,03 → 0,60 | 557,18 → 356,80 |

Las filas de T-254 comparan su tabla con 3 repeticiones nuevas en main. El canónico no cambia (M04/M05 iguales ±5 %).
Los ganadores cambian entre antes y después por la semilla D-90 (#731), no por las optimizaciones.

**P30 y certificación** (1 ejecución; `resultados/MEDICION_*_rep1_p30.json` y `CERTIFICACION.json`): P30
`produccion competir` 10,4 / ~21 / 21,2 / 16,3 / 212,9 / 345,7 s (Sevilla, Valencia, Barcelona, Madrid Congreso,
Andalucía, Madrid); todos `P30_GANA_OTRO_PLAN`. Rehacer M06 1,8-9,4 s; `verificar` 0,1-0,2 s; auditoría geométrica
4,2-7,9 s; `estado_produccion` (certificación completa, `certificar.py`) 0,10-0,14 s, todos `PASS_WITH_EXCEPTIONS`.

## 3. Utilidad del exhaustivo (b) — datos hasta ahora

- En los 9 territorios medidos la cota (#724) no deja lanzarlo; la cota sale justo por encima del presupuesto
  (200 072-231 152 nodos frente a 200 000).
- Datos versionados de la batería r3 (T-196, `docs/ESTUDIOS/T196_BATERIA_D8/datos/CANDIDATOS.csv`): el exhaustivo
  acaba en 11 territorios (8 del Congreso con K=1, congreso_alava, ceuta, melilla) y en los 11 su plan es **el mismo**
  que el del canónico y el de las 10 cadenas (misma `huella_plan`). No aporta ningún candidato distinto ni cambia
  ningún ganador. Los COMPETICION.json de T-180 son de la 1.1.0 (sin exhaustivo).
- Conclusión provisional: el exhaustivo no aporta en ningún territorio medido; propuesta técnica: retirarlo de la
  competición (o dejarlo solo para el certificador). Falta confirmarlo con `a_frente_d8.py` (ver abajo).

## 4. A frente a D8 en el exhaustivo (c) — pendiente

`a_frente_d8.py` enumera todos los planes válidos y compara el mejor por A y por D8. No llegó a ejecutarse. Argumento
provisional: en los 11 territorios donde acaba hay un único plan válido (K=1; congreso_alava 1 plan, T-136) o todos los
candidatos coinciden, así que A y D8 no pueden elegir distinto; en los demás no se lanza. Sin datos, no se afirma.

## 5. Qué queda por optimizar (por peso medido)

1. **M04 en territorios grandes**: 241 s (congreso_madrid, 94 % del total), 280 s (madrid), 71 s (congreso_barcelona).
   T-254 ya señaló `connected` (BFS desde cero) en `find_peel`. Perfil de Madrid: pendiente.
2. **M05 con recocido privado** en Andalucía: 280 s (52 %). Perfil pendiente.
3. **Cadenas en autonómicas grandes**: 357 s en Madrid (53 %), 178 s en Andalucía; árbol ponderado y `nucleo`
   (T-254 n.º 3).
4. **Exhaustivo**: hoy ≤ 1,3 s (cálculo de la cota); retirarlo ahorra eso y simplifica la huella.
5. **Puerta privada duplicada en M05** (T-254 n.º 4) y elección D8 (`juzgar`, hasta 14 s en Andalucía).

## Pendiente y cómo reanudar

```bash
pip install -r requirements.lock && pip install --no-deps gerrychain==1.0.0
pip install networkx==3.6.1 rustworkx==0.18.1 scipy==1.18.1 tqdm==4.70.1 six==1.17.0
python3 herramientas/bateria_motor.py nacionales
python3 herramientas/bateria_motor.py entradas ceuta melilla congreso_alava congreso_soria congreso_huesca --seccionado shapefile
PYTHONHASHSEED=0 python3 docs/ESTUDIOS/T254_MEDICION_DESLINDE/medir.py --rep 1 --salida /tmp/peq ceuta melilla congreso_alava congreso_soria
PYTHONHASHSEED=0 python3 docs/ESTUDIOS/T270_MEDICION_DESLINDE_OPTIMIZADO/a_frente_d8.py ceuta melilla congreso_alava congreso_soria congreso_huesca
# perfiles (tras medir el territorio, que deja su caché):
DDD_RUN_ID=bateria-congreso_madrid-7.4.4 DDD_OPTIMIZATION_ALGORITHM="Canónico" python3 -m cProfile -o m04.prof modulos/04_generar_semillas.py --params territorios/congreso_madrid/config/congreso_madrid_2025.yaml
DDD_RUN_ID=bateria-andalucia-7.4.4 DDD_OPTIMIZATION_ALGORITHM="Canónico" python3 -m cProfile -o m05.prof modulos/05_optimizar_distritos.py --params territorios/andalucia/config/andalucia_2025.yaml
```

Falta además: códigos oficiales de los territorios, registro `docs/registro/AAAA-MM-DD_<rama>.md` y la PR.

## Nota de estado (2026-11-14)

Parado por orden de ahorro del Coordinador (T-270, baja prioridad). Hecho en esta sesión: merge de `origin/main`, entorno
instalado y entradas de ceuta, melilla, congreso_alava, congreso_soria y congreso_huesca generadas (no versionadas).
Falta: `medir.py` de esos 5, `a_frente_d8.py`, perfiles M04 (congreso_madrid) y M05 (andalucia), códigos oficiales,
registro `docs/registro/AAAA-MM-DD_<rama>.md` y la PR. Comandos en «Pendiente y cómo reanudar».
