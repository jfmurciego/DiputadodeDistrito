# T-197 — Ensayo de la noche electoral de las generales del 29-11-2026

Fecha: 2026-11-10 · Solo local, con el ZIP nacional por mesa de 2023 (release `fuente-infoelectoral-02202307`,
sha256 `e78fc231…f1717f8` comprobado) disfrazado de 2026. No se lanzó ningún workflow, no se publicó y no se escribió
`orchestracion/publicaciones_visor.json` (el registro simulado vive fuera del repositorio). Sin cambios en `herramientas/`,
`modulos/`, `ddd_core/` ni workflows. Guion reproducible: `ensayo.py` (este directorio; `python -I ensayo.py <dir>` con el ZIP
en `<dir>/zip/`).

## Qué se hizo
Para cada una de las 52 circunscripciones de `configuracion/elecciones_generales_2026.yaml`:
1. **Contrato**: el contrato 2023 con `election_id=<territorio>_2026-11-29` y `election_date=2026-11-29`, pasado por `fuente_infoelectoral_mesas.resolve` (validaciones de totales y CERA).
2. **Ingestión**: `fuente_infoelectoral_mesas.convert` (huella, secciones, mesas, votos y CERA contra el contrato).
3. **Homologación**: cada sigla del ZIP por `homologacion_candidaturas_2026.resolver` (reglas 2026) y comparada con las candidaturas BOE 2026 de la provincia.
4. **Asignación por distrito**: `resultados_partidos.agregar_informe` sobre las composiciones vigentes (`datos/composicion`) y el ganador del M08 vigente; con la tabla de equivalencia 2023 y la tolerancia D-17.
5. **Escaños**: D'Hondt con umbral del 3 % (`reparto_art162.dhondt`) con los escaños oficiales 2026 (RD 806/2026) sobre los votos homologados.
6. **Registro del visor en simulación**: copia del registro con 52 `canonical_m08` simulados (run `9000000000000`, blobs ficticios), pasada por `validate_registry`.

## Resultado (52 de 52)
- **Ingestión y contrato: 52/52 sin error.** Totales de votos y CERA cuadran.
- **Asignación por distrito: 52/52 agregan sin error** (suma por partido = total provincial del ZIP; ganador de cada distrito = M08 vigente). Desajuste D-17 máximo: Badajoz 0,87 %, Valencia 0,77 %, Albacete 0,63 %. En los 30 territorios con `*_partidos.csv` publicado en git, el CSV simulado es **idéntico byte a byte** al de 2023 (30/30); los otros 22 no tienen referencia en git (solo comprobaciones internas).
- **Escaños: 350 en total.** En las 50 provincias cuya K 2026 = K 2023 el reparto por partido coincide con el oficial 2023 (50/50 como multiconjunto de escaños). Cádiz 8 (9 en 2023) y Madrid 38 (37) usan el escaño 2026 del RD.
- **Registro simulado: valida** (197 → 249 entradas). Efecto: el producto simulado pasa a ser el «vigente» de las 52 y deja al de 2023 fuera de `resultados_ligeros.vigentes()`.

## Lo que falla o queda al descubierto
1. **Homologación 2026 incompleta frente a las siglas de Interior.** Con las reglas 2026, las siglas que no están en ninguna regla pasan por «identidad, certeza ALTA» sin aviso. Con el ZIP 2023 quedan sin unir: `PSE-EE (PSOE)` (Álava, Guipúzcoa, Vizcaya), `SUMAR - ECP`, `SUMAR - COMPROMÍS`, `SUMAR ARAGÓN`, `JxCAT - JUNTS`, `U.P.N.`, `MÉS PER MALLORCA-MÉS PER MENORCA-SUMAR`. Los escaños salen bien en número pero **con nombres de partido partidos** (p. ej. 5 «PSE-EE (PSOE)» + 117 «PSOE»). Todas las provincias traen siglas del ZIP sin candidatura BOE 2026 (columna «sin cand.»): esperable en parte (partidos que ya no concurren), pero hoy nada distingue lo esperable de un error.
2. **El registro del visor no tiene dimensión de elección.** Un M08 de 2026 con el mismo `territory_id` desplaza al de 2023 como vigente (gana el `run_id` mayor); `resultados_ligeros.generar` y `resultados_partidos.generar` borran lo de 2023 al regenerar, y `resultados_partidos.FECHA = "2023-07-23"` filtra solo contratos de 2023. La entrada no lleva `election_date`/`election_id`.
3. **`resultados_partidos.contratos()` solo ve contratos de 2023** (constante `FECHA`); con contratos 2026 no encontraría ninguno.
4. **Nombres de partido en el CSV de distrito** siguen la sigla del ZIP, no el homologado (no se aplica la homologación en `agregar`).

## Qué falta (lista corta, por orden)
1. **Tabla de equivalencia de secciones 2026** (fichero nuevo, ver T-129 §3): las secciones del censo electoral de noviembre de 2026 no son las del seccionado INE 2023 del M06. Sin ella, las secciones del ZIP ausentes del M06 se reparten por D-17 y fallan si las partidas entre distritos superan el tope (0,5 % de los votos de la provincia; en el ensayo con 2023 pasan las 52, con desajuste total de hasta 0,87 % en Badajoz). Se construye con el ZIP 2026 y el callejero; no se puede ensayar antes.
2. **52 contratos Infoelectoral 2026** (`configuracion/contratos_infoelectoral.yaml`): URL, sha256, prefijo, ficheros, `expected` y `official_totals` solo existen con el ZIP real y la resolución de la JEC. Hay que comprobar que `herramientas/generar_provincias_congreso.py` admite fecha y prefijo nuevos (no verificado). Espejo en release porque Interior rechaza runners.
3. **Homologación fail-closed sobre el ZIP real**: una comprobación que, con las siglas del ZIP, falle o avise de toda sigla sin regla y sin candidatura BOE, y reglas 2026 para las variantes de Interior de arriba (decisión de contenido: familia SUMAR, JUNTS, PSE-EE, UPN).
4. **Decisión del propietario sobre el registro**: convivencia 2023/2026 (campo de elección en la entrada y en `vigentes()`) o sustitución. Toca `registro_publicaciones_visor.py`, `resultados_ligeros.py`, `resultados_partidos.py`: pedir turno al Coordinador.
5. **Parametrizar `FECHA`** en `resultados_partidos.py` (fecha de la elección vigente en vez de constante).
6. Una vez haya M08 2026: ejecutar la 00 / el Gestor sobre los 52 con el contrato 2026 (lo lanza el Operador con permiso).

## Nota del censo (T-129): cerrada
Nada pendiente de acreditar. `docs/NOTA_T129_CENSO_Y_REPARTO_2026.md`: el reparto de escaños 2026 reproduce el RD 806/2026 con las cifras oficiales de población (RD 1117/2025); el K de los distritos sigue con la tabla INE 65034 (decisión del propietario, opción A); el censo electoral (CER/CERA) llega con el ZIP de Interior y se casa con el M06 por la tabla de equivalencia 2026 (punto 1 arriba). Este ensayo lo confirma: el CERA (un registro por provincia) se excluye y cuadra en las 52.

## Detalle por circunscripción
Columnas: ingestión del ZIP · distritos · desajuste D-17 (%) · CSV de distrito vs 2023 publicado · escaños 2026 · reparto vs oficial 2023 (solo si misma K) · siglas del ZIP sin candidatura BOE 2026.

| Circunscripción | Cód. | Ingestión | Distritos | Desaj. % | CSV | Esc. | Reparto | Sin cand. |
|---|---|---|---|---|---|---|---|---|
| alava | 01 | 240 secc, 427 mesas, 167304 votos | 3 | 0.00 | = | 4 | = | 4 |
| albacete | 02 | 296 secc, 521 mesas, 218503 votos | 3 | 0.63 | sin ref. | 4 | = | 3 |
| alicante | 03 | 1236 secc, 2227 mesas, 888631 votos | 17 | 0.19 | sin ref. | 12 | = | 3 |
| almeria | 04 | 462 secc, 837 mesas, 316006 votos | 6 | 0.52 | sin ref. | 6 | = | 5 |
| avila | 05 | 310 secc, 358 mesas, 96470 votos | 1 | 0.00 | sin ref. | 3 | = | 5 |
| badajoz | 06 | 551 secc, 902 mesas, 386842 votos | 6 | 0.87 | sin ref. | 5 | = | 5 |
| baleares | 07 | 670 secc, 1249 mesas, 496245 votos | 10 | 0.00 | = | 8 | = | 2 |
| barcelona | 08 | 3649 secc, 6472 mesas, 2625437 votos | 50 | 0.24 | sin ref. | 32 | = | 5 |
| burgos | 09 | 582 secc, 746 mesas, 198616 votos | 3 | 0.00 | = | 4 | = | 6 |
| caceres | 10 | 412 secc, 524 mesas, 232620 votos | 3 | 0.32 | sin ref. | 4 | = | 6 |
| cadiz | 11 | 926 secc, 1528 mesas, 627167 votos | 11 | 0.00 | = | 8 | — | 4 |
| castellon | 12 | 444 secc, 740 mesas, 303870 votos | 5 | 0.00 | = | 5 | = | 2 |
| ciudad_real | 13 | 419 secc, 707 mesas, 279684 votos | 4 | 0.00 | sin ref. | 5 | = | 4 |
| cordoba | 14 | 620 secc, 948 mesas, 442151 votos | 6 | 0.00 | sin ref. | 6 | = | 3 |
| la_coruna | 15 | 882 secc, 1544 mesas, 662459 votos | 9 | 0.47 | sin ref. | 8 | = | 2 |
| cuenca | 16 | 310 secc, 383 mesas, 112472 votos | 2 | 0.00 | = | 3 | = | 3 |
| gerona | 17 | 536 secc, 863 mesas, 317740 votos | 7 | 0.00 | = | 6 | = | 5 |
| granada | 18 | 672 secc, 1121 mesas, 494203 votos | 8 | 0.00 | = | 7 | = | 5 |
| guadalajara | 19 | 400 secc, 587 mesas, 139031 votos | 2 | 0.00 | = | 3 | = | 4 |
| guipuzcoa | 20 | 547 secc, 858 mesas, 370320 votos | 6 | 0.00 | sin ref. | 6 | = | 4 |
| huelva | 21 | 371 secc, 651 mesas, 253713 votos | 4 | 0.00 | = | 5 | = | 4 |
| huesca | 22 | 286 secc, 403 mesas, 117735 votos | 2 | 0.00 | = | 3 | = | 5 |
| jaen | 23 | 501 secc, 873 mesas, 364706 votos | 5 | 0.00 | sin ref. | 5 | = | 4 |
| leon | 24 | 447 secc, 722 mesas, 269759 votos | 4 | 0.00 | = | 4 | = | 5 |
| lerida | 25 | 388 secc, 549 mesas, 180770 votos | 4 | 0.00 | = | 4 | = | 6 |
| la_rioja | 26 | 344 secc, 516 mesas, 171589 votos | 3 | 0.34 | sin ref. | 4 | = | 4 |
| lugo | 27 | 277 secc, 533 mesas, 193699 votos | 3 | 0.21 | sin ref. | 4 | = | 5 |
| madrid | 28 | 4480 secc, 7118 mesas, 3535749 votos | 59 | 0.03 | sin ref. | 38 | — | 3 |
| malaga | 29 | 1084 secc, 1734 mesas, 775255 votos | 15 | 0.06 | sin ref. | 11 | = | 4 |
| murcia | 30 | 1223 secc, 1726 mesas, 739321 votos | 13 | 0.00 | = | 10 | = | 5 |
| navarra | 31 | 578 secc, 997 mesas, 336216 votos | 6 | 0.00 | = | 5 | = | 4 |
| orense | 32 | 257 secc, 539 mesas, 179460 votos | 3 | 0.00 | = | 4 | = | 4 |
| asturias | 33 | 832 secc, 1528 mesas, 582385 votos | 8 | 0.00 | = | 7 | = | 4 |
| palencia | 34 | 275 secc, 335 mesas, 95377 votos | 1 | 0.00 | = | 3 | = | 8 |
| las_palmas | 35 | 715 secc, 1564 mesas, 523753 votos | 10 | 0.00 | = | 8 | = | 6 |
| pontevedra | 36 | 727 secc, 1344 mesas, 559676 votos | 8 | 0.12 | sin ref. | 7 | = | 3 |
| salamanca | 37 | 532 secc, 648 mesas, 194989 votos | 3 | 0.00 | = | 4 | = | 5 |
| santa_cruz_de_tenerife | 38 | 681 secc, 1379 mesas, 484835 votos | 9 | 0.00 | = | 7 | = | 5 |
| cantabria | 39 | 460 secc, 777 mesas, 343495 votos | 5 | 0.00 | = | 5 | = | 3 |
| segovia | 40 | 276 secc, 330 mesas, 87194 votos | 1 | 0.00 | = | 3 | = | 5 |
| sevilla | 41 | 1365 secc, 2588 mesas, 1043832 votos | 16 | 0.06 | sin ref. | 12 | = | 4 |
| soria | 42 | 216 secc, 256 mesas, 49823 votos | 1 | 0.00 | = | 2 | = | 4 |
| tarragona | 43 | 542 secc, 1039 mesas, 362891 votos | 7 | 0.00 | = | 6 | = | 7 |
| teruel | 44 | 284 secc, 328 mesas, 75074 votos | 1 | 0.00 | = | 3 | = | 5 |
| toledo | 45 | 530 secc, 903 mesas, 383100 votos | 6 | 0.21 | sin ref. | 6 | = | 4 |
| valencia | 46 | 1827 secc, 3200 mesas, 1419017 votos | 23 | 0.77 | sin ref. | 16 | = | 5 |
| valladolid | 47 | 565 secc, 763 mesas, 311740 votos | 4 | 0.00 | = | 5 | = | 6 |
| vizcaya | 48 | 929 secc, 1410 mesas, 602806 votos | 10 | 0.00 | sin ref. | 8 | = | 4 |
| zamora | 49 | 319 secc, 369 mesas, 100766 votos | 1 | 0.00 | = | 3 | = | 6 |
| zaragoza | 50 | 885 secc, 1467 mesas, 510009 votos | 8 | 0.15 | sin ref. | 7 | = | 5 |
| ceuta | 51 | 56 secc, 96 mesas, 32905 votos | 1 | 0.00 | = | 1 | = | 5 |
| melilla | 52 | 44 secc, 87 mesas, 26925 votos | 1 | 0.00 | = | 1 | = | 5 |
