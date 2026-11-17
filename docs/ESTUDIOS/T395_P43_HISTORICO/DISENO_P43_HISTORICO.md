# T-395 · Diseño: P43, publicación del histórico por fecha de elección (P40 y visor)

VERSIÓN: 1.2.0 · FECHA: 2026-11-17 · ESTADO: propuesta para el Planificador y el propietario (D-124, D-125, D-129, D-134, D-150, D-152)
ANTERIOR: 1.1.0 (#875@25c83af); 1.0.0 (#875@67864de, asumía el mapa 2023 del paso A, contra D-125)
CAMBIOS 1.2.0: D-154 (propietario, vía Planificador) registrado (§12); revisor independiente de 1.0.0: condiciones `if` exactas de P40 para el modo histórico (C1), `Validar sitio candidato completo` y `preparar_visor_ejecucion` (C12), `Persistir registro` (C13), prueba de no-regresión de los 13 consumidores (§6.5), origen verificable de las fechas (D8), ruta de datos distinta de la del paso A (§7) y estado de las referencias no fusionadas.
CAMBIOS 1.1.0: criterio del Planificador (D-125, opción A del propietario): el M06 de cada elección es el propio de P20 sobre `<t>_hAAAA_MM` y el M08 el de P30 sobre ese M06; sin reagregación al mapa 2023 (T-351 obsoleta). Cambian D3, D6, §3, §4, §5 (C3, C6), §7, §9, §11 y §12.
MOTIVO: D-134 dejó P43 «en tarea aparte tras el diseño del paso A». Este documento lo diseña. Solo documento: sin cambios en `ddd_core/`, `herramientas/`, workflows, `orchestracion/` ni datos. Base: `origin/main` f559cea8.
Referencias y su estado: T-355 = #830, **cerrada sin fusionar** (rama `t355-historico-publicacion`, sin merge-base con `main`; leída con `pull_request_read`, no ejecutada aquí). T-393 = #873@52a8419e, **abierta y sin fusionar**: sus ids `_h`, su `territorio_ids` 1.2.0 y sus 260 filas son diseño, no código en `main`; las cifras de provincias generables (39/27/33/35/46) son **suyas y no las he verificado**. T-378 = `docs/ESTUDIOS/T378_P00_CAMPANA/`, en `main` desde #858 (227b9fff, diseño 1.1). Los hechos de `main` de este documento se midieron sobre f559cea8.

## 0. Resumen y recomendación

1. **Cada elección publica su propio par M06 + M08** (D-125): distritos generados con seccionado, padrón y K oficial de esa época (P20 sobre `<t>_hAAAA_MM`, T-393) y resultados de P30 sobre ese M06. **No hay reagregación al mapa 2023**: el paso A sobre 2023 (T-351, #819) queda como legacy (§1, §11).
2. **Registro: se reutilizan `canonical_m06` y `canonical_m08` con la dimensión de elección ya existente** (`election_date`, `election_id`, T-199/T-201), más `historico_id` y `fuente: "historico_epoca"`. Con un M06 propio por elección desaparecen los motivos de la v1.0 para un kind nuevo: `check_pairs`, la unicidad por (territorio, familia, elección) y el linaje M06/M08 **sí se aplican** (§3, §5). *Esto se aparta de «kind `historico_epoca`» del encargo: lo confirma el Planificador (§12).*
3. **`territory_id` del registro = provincia (`nac22`); el id propio `nac22_h2019_11` va en `historico_id`.** El visor agrupa por provincia y elección (§3).
4. **P43 no es un workflow nuevo: es la tercera opción de «Qué publicar» de P40** («Histórico»), con `elección` (AAAA-MM) y `territorios`; mismo `simular` marcado, todo o nada y sitio completo (§2).
5. **P00 con elección AAAA-MM no publica ni escribe en `main` (solo P00; el paso «Persistir registro» de P40 sí empuja a `main` tras desplegar, §5 C13).** Deja M06 + M08 + `PUERTA` en R2 con manifiesto sha256 y un issue; P43 lo recoge de R2 (§4). Se mantiene «`Publicar = sí` se rechaza con aviso en histórico» de T-393 §7.
6. **T-355 se rescata, no se reabre:** de #830 se reutilizan el descriptor por PUERTA y sus fallos cerrados (`PUERTA_NO_PASS`, `SIN_M08`, `SIN_DISTRITOS`, `CLAVE_HISTORICA`, `CLAVE_REPETIDA`), ampliados al M06 propio y a la fuente R2. Se descarta su `reutiliza el M06 publicado` y su parte de workflows y P50 (§4).
7. **D-154:** se publican verde y ámbar (este con aviso visible); rojo, nunca; primera entrega solo visor y catálogo de procedencia (§12).
8. **Visor:** `validElection()` de `visor/v3/v3.js` está cableado a `202307`; hace falta una capa «histórico» con la etiqueta «distritos de <fecha>, con datos de esa época» (§7).
9. **Detrás de T-377 y T-393, con turno exclusivo.** Lo no probable sin Actions: §10.
## 1. Qué hay hoy (medido sobre `origin/main`)

| Pieza | Estado |
|---|---|
| Registro `registro_publicaciones_visor.py` 1.8.1 | Dimensión de elección opcional desde 1.5.0 (`election_date`, `election_id`; `eleccion_de(entry)`; sin fecha = `ELECCION_POR_DEFECTO` 2023-07-23). Identidad = (territorio, kind, run/escenario, elección). `canonical=true` único por (territorio, familia, elección). Solo-adición. |
| `check_pairs` / `linaje_m06_m08.pares_incompletos` | Por (territorio, elección): si **no** hay `canonical_m06` de esa elección, `continue` (no exige nada). Un `canonical_m08` histórico sin M06 pasaría **en silencio**, sin la garantía de T-249. |
| Consumidores de `canonical_m08` / `vigente_por_eleccion` | 13 ficheros: `catalogo_procedencia`, `composicion_m06`, `evaluar_publicacion_visor`, `generar_datos_abiertos`, `generar_hemiciclo`, `generar_nombres_comunidades_nacional`, `legislatura_vigente`, `linaje_m06_m08`, `p50_resolver`, `preparar_visor_ejecucion`, `resultados_ligeros`, `resultados_partidos`, y el propio registro. Todos filtran por elección con valor por defecto 2023. |
| P40 (`p40-publicacion.yml` 1.0.0) | `workflow_dispatch`: `que_publicar` (Solo el sitio \| Territorios), `territorios`, `simular` (true). Jobs `resolver` → `preparar` → `publicar`. `resolver` llama a `herramientas/p40_resolver.py` (última 00 completa con la 04 en verde por territorio, de `territorios/<t>/evidencia/ejecuciones_completas/`). El publicador descarga artefactos `ddd-*` (selectiva → completa → R2), acredita (`evaluar_publicacion_visor`), `describe-production`, `merge-descriptors`, promueve a blob, `candidate`, construye el sitio. Cabecera: «P43 (histórico por fecha) queda fuera: tarea aparte». Congelado por `tests/test_t372_p40_equivalencia.py`. |
| Paso A (`historico_campana.py` 1.5.0, `historico_m07m08.py`) | **LEGACY por D-125** (T-351, ficha #819 obsoleta): reagrega votos de cada época sobre el **mapa 2023** (sin `--mapa`) y escribe `PUERTA_<t>_<AAAA_MM>.json`. P43 **no** lo consume: ni su M08 ni su M06. Se conserva `PUERTA` (formato) y el contraste BOE (T-342/T-343) porque P30 los reutiliza. El camino vivo es T-365: M06 propio por época + `electoral` (M07/M08 + PUERTA), piloto `nac22` 2019-11. |
| Visor v3 (`visor/v3/v3.js`) | `S.election` por defecto `"202307"`; `validElection()` = `nacional && "202307"`; con otra fecha muestra «Sin capa electoral certificada para esta fecha». El panel de procedencia ya lee `catalogo_procedencia.json` por prefijo `AAAA-MM` y la fecha `prod.eleccion`. |
| T-393 §7 | `elección = AAAA-MM` + `congreso` → `nacNN_hAAAA_MM`; 52 ≤ 256 jobs; cierre histórico «no escribe en `main` hasta T-355». |

## 2. Decisiones

| # | Decisión | Por qué |
|---|---|---|
| D1 | **P43 = opción «Histórico» de `que_publicar` en P40.** Campos: `eleccion` (lista cerrada AAAA-MM: 2011-11, 2015-12, 2016-06, 2019-04, 2019-11), `territorios` (códigos `nacNN`; vacío = todos los de esa elección con M08 en R2), `simular` (marcado). | D-129/D-130: un workflow por familia, opciones dentro, sin parámetros técnicos. Reutiliza el publicador (blob, candidato, preflight, sitio). |
| D2 | **Todo o nada por lote y una elección por lote.** Un territorio sin M08 válido, PUERTA ≠ PASS o hash que no cuadra rechaza el lote (`P43_LOTE_RECHAZADO`). | Fail-closed de T-355 y de P40. Una elección por lote conserva `CLAVE_REPETIDA`. |
| D3 | **`canonical_m06` + `canonical_m08` de la elección** (par por provincia y elección), con `historico_id` y `fuente: "historico_epoca"`. Campos en §3. | Con M06 propio, el par cumple `check_pairs` y el linaje (T-249) sin código nuevo. «Vigente» sigue siendo por elección (`vigente_por_eleccion`), no entre elecciones. |
| D4 | **`territory_id` = `nac22`; `historico_id` = `nac22_h2019_11`.** `territorio_ids.base_y_eleccion` (T-393 §2) los une. | El visor y `catalogo_procedencia` agrupan por provincia; T-393 dice que `_h` no es el mismo territorio-elección que `nac22` para catálogo, no para el visor. |
| D5 | **Fuente de P43 = R2 (`productos/<id>/<run>/…`) + manifiesto, no artefactos de Actions ni `main`.** | D-129: carpeta `productos/`. Los artefactos caducan; el cierre del histórico no escribe en `main` (T-393 §7, T-378). |
| D6 | **El M06 de la elección es el propio** (P20 sobre `<t>_hAAAA_MM`: seccionado y padrón del año, K = escaños oficiales de esa elección) y se registra con el M08 de P30 sobre él. **Nunca se reutiliza el M06 vigente ni se reagrega al mapa 2023** (D-125). | Es la opción A del propietario: ejercicio retrospectivo «quién habría mandado en ese momento», publicado con fecha y procedencia, separado del vigente. |
| D7 | **La puerta es la de T-342/T-343 y no se relaja:** `PUERTA.estado == "PASS"` (M07 PASS o PASS_WITH_DECLARED_EXCEPTIONS con ≤ 0,1 % salvo D-70) y contraste BOE. P43 solo comprueba que el JSON existe, su sha256 y que `territorio`, `clave` y `estado` cuadran con el `historico_id`. | P43 no decide la calidad; la decide P30. |
| D8 | **Fecha de la elección = tabla fija `ELECCIONES_HISTORICO`** (de T-355: 201911→2019-11-10, 201904→2019-04-28, 201606→2016-06-26, 201512→2015-12-20, 201111→2011-11-20), **Origen de cada fecha:** el campo `fuente` de `configuracion/resultados_oficiales_congreso_<AAAA>_<MM>.json` (BOE; 2011: «20 de noviembre de 2011», 2015: «20 de diciembre de 2015», 2016: «26 de junio de 2016», 2019-04: «28 de abril de 2019», 2019-11: «10-11-2019»). 2023 no entra (flujo vigente). | Datos oficiales nunca de memoria (CLAUDE.md). La tabla de T-355 era de memoria; aquí el test fija **literales** (las fechas de arriba) y comprueba que cada `fuente` del BOE las contiene (en texto largo o `dd-mm-aaaa`); no recalcula la tabla desde sí misma. |
| D9 | **Republicar** = nueva entrada del mismo (provincia, elección) con `run_id` mayor; vigente por el mayor `run_id` (criterio de `vigente_por_eleccion`). Sin borrar. | Registro solo-adición. |
| D10 | **P43 nunca se llama desde la 00 ni desde el Gestor.** Solo botón de P40 (con permiso del Operador). | Evita publicar histórico dentro de una campaña; el cierre de P00 no tiene `Publicar` para histórico. |

## 3. El registro: pares `canonical_m06` + `canonical_m08` de la elección

Una provincia y elección publican **dos entradas** (M06 y M08) como cualquier territorio, con estos campos añadidos:

```json
{
  "id": "m08-nac22_h2019_11-<run>",
  "kind": "canonical_m08",
  "territory_id": "nac22",
  "historico_id": "nac22_h2019_11",
  "fuente": "historico_epoca",
  "run_id": "<run de la P00 histórica>",
  "election_date": "2019-11-10",
  "election_id": "generales_nac22_2019-11-10",
  "expected_districts": 3,
  "puerta": {"estado": "PASS", "m07": "PASS", "sha256": "<hex>"},
  "datos_epoca": {"seccionado": "2019", "padron": "2019", "k_oficial": 3},
  "semaforo": "verde",
  "aviso_epoca": null,
  "canonical": true
}
```

El `canonical_m06` lleva lo mismo salvo `puerta`. Activo inmutable (blob + sha256) como en las demás entradas.

`semaforo` es `verde` o `ambar` (D-154); `aviso_epoca` es obligatorio (texto) con `ambar` y lo muestra el visor; con `rojo` no se genera entrada (el resolver descarta la provincia y lo dice).

Cambios en `registro_publicaciones_visor.py` (1.10.0, legacy):
- `_validate_entry`: si hay `fuente == "historico_epoca"`, exige `historico_id` (forma de T-393 §2), `election_date` ∈ `ELECCIONES_HISTORICO.values()`, `election_id` que termine en la fecha, `base_y_eleccion(historico_id) == (territory_id, election_date[:7])`, `datos_epoca.k_oficial` = `expected_districts`, `semaforo` ∈ {verde, ambar} con `aviso_epoca` si es ámbar y, en el M08, `puerta.estado == "PASS"`.
- `check_pairs` y `linaje_m06_m08` **sin cambio**: ahora actúan con la clave (provincia, elección). Un M08 histórico sin su M06 propio falla `PAR_INCOMPLETO`.
- `canonical=true` único por (territorio, familia, elección) (ya existe): cada elección conserva su M06/M08 vigente sin pisar 2023 ni las demás épocas.
- `describe-production` no cambia; subcomando nuevo **`describe-historico`** (`--r2-manifest`, `--eleccion`, `--territorios`) que emite el par. No se sobrecarga `es_raiz_historica` (la detección de T-355, «no hay `production_status.json`», es frágil).
- `rechazar_mapa_350` se mantiene (D-18/D-19). `ELECCIONES_HISTORICO` pasa a una tabla propia (fuente de D8).
## 4. Qué publica P00 con elección AAAA-MM y cómo lo recoge P43

**P00 (cierre histórico), por provincia y elección, sin `main`:**
1. P20 produce el M06 `_h` (seccionado y padrón del año, K oficial de la elección) y P30 el M08 + `PUERTA_<t>_<AAAA_MM>.json` sobre ese M06 (T-365: `cadena` = materializar + admisión + M01..M06 + `electoral`).
2. Subida a R2 `productos/nac22_h2019_11/<run>/`: M06 (`*_m06_distritos.geojson.zip` + composición), M08 (`m08_distritos_resultados.geojson.zip`), `resumen_electoral.csv`, `PUERTA_….json` y `MANIFEST.json` (`historico_id`, `run_id`, `clave`, `fecha`, `datos_epoca`, `semaforo`, `aviso_epoca`, K, sha256 de cada fichero y linaje M06→M08). Verificación de lectura tras subir (patrón de `restaurar_estado_r2.py`).
3. Issue del cierre con una línea por provincia (PASS/FALLA y causa del contrato). **Ningún commit, ningún registro en P00.** La publicación y su commit al registro son de P43 (P40), después de desplegar.
4. `Publicar = sí` con histórico: rechazado en la comprobación previa con aviso «el histórico se publica con P40 → Histórico».

**P43 (P40 con «Histórico»):** `p40_resolver.py historico --eleccion AAAA-MM [--territorios …]` lista `productos/` de R2, toma por provincia el `MANIFEST.json` del `run_id` mayor con PUERTA PASS y par M06/M08 del mismo linaje, verifica sha256 y devuelve JSON (`entradas`, `descartadas` con motivo). Errores `::error::P43_…` con rc 1, como `P40_…`.

**De T-355 (#830) se descarta:** la lectura de `ddd-historico-*`, el `election_date` en P50 y los cambios en `historico_m07m08.py` 1.2.0 (copiar el M08 a `salida_historico`): son del paso A (legacy) y la fuente ahora es R2. **Se reutiliza:** el patrón de descriptor y los fallos cerrados.
## 5. Qué choca con P40, el registro y los consumidores

| # | Choque | Resolución |
|---|---|---|
| C1 | Los pasos del publicador de la 00 cuelgan de `needs.preparar.outputs.production_run_id != ''` (l. 313, 330, 399, 414, 433). La elección AAAA-MM no tiene run 00: `production_run_id` vacío = modo «solo sitio» (se saltarían todos, y «Promover» también, dejando el histórico sin publicar sin error). | El resolver emite una salida nueva `modo` ∈ {`00`, `historico`, `sitio`}, que `preparar` reexporta (`outputs`). Condiciones: **Normalizar lote, Recuperar ejecución, Acreditar identidad, Validar descriptores** pasan de `production_run_id != ''` a `modo == '00'` (equivalente: con ids = `00`; con `workflow_call` de la 00 y de las alternativas el resolver fija `00`); **Promover productos a blob** pasa a `modo == '00' \|\| modo == 'historico'` (solo consume `/tmp/product-descriptors.json`); **nuevos** «Recuperar de R2», «Acreditar manifiesto» y `describe-historico`, con `modo == 'historico'`, que escriben `/tmp/product-descriptors.json`. `Construir candidato` y el sitio se comparten. `Preparar promoción web` («Sin production_run_id: modo solo sitio») cambia su mensaje según `modo`. Test (C2): con `modo=00` los pasos son los de 1.0.0; con `historico` se saltan los cinco y entran los nuevos. |
| C2 | `tests/test_t372_p40_equivalencia.py` congela P40 contra los tres workflows viejos. | La PR de P43 actualiza el test con lista de diferencias esperadas y control negativo (sin la opción, P40 sigue equivalente). Aviso al dueño de T-372. |
| C3 | `check_pairs` ignora una elección sin M06 (`continue`). | Ya no es un riesgo: cada elección registra su M06 propio y el par se comprueba. Test: M08 histórico sin M06 de su elección → `PAR_INCOMPLETO`; M06 de 2023 no sirve de par para 2019-11 (clave por elección). |
| C4 | Los 13 consumidores de `canonical_*`/`vigente_por_eleccion` (lista en §1). | Con kinds canónicos y elección explícita, ninguno cambia **por diseño**, pero no se afirma: el test de §6.5 los recorre **los 13** con un registro que añade el par histórico. Hemiciclo y legislatura siguen pidiendo 2023. |
| C5 | `catalogo_procedencia._declarada`/`_eleccion` leen `election_date` sin declarar como 2023: un histórico sin fecha se leería como 2023. | `_validate_entry` exige la fecha en la tabla D8 si `fuente == "historico_epoca"`; test de `eleccion_declarada == true`. |
| C6 | `composicion_m06.py` (T-301) exige y versiona la composición del M06 de cada descriptor. | Aplica tal cual: `describe-historico` emite el M06 propio y su composición se versiona por elección (`m06_vigentes(registro, eleccion)` ya admite elección). Test: la composición de 2019-11 no pisa la de 2023. |
| C7 | `rechazar_mapa_350` y `scenario_*`: el lote no mezcla. | Test: lote histórico + alternativas se rechaza; `congreso350_*` se rechaza. |
| C8 | `p50_resolver.py` y P50 publicación académica usan `canonical_m08`. | P50 vigente pide 2023: sin cambio; test de que `p50_resolver` ignora entradas con `fuente == "historico_epoca"`. P50 3.7.0 no recibe `election_date`. |
| C9 | `PUERTA_<t>_<AAAA_MM>.json` usa `territorio = nac22` (T-365). | El manifiesto fija `historico_id`; el resolver comprueba que `territorio`+`clave` dan el `historico_id` por `base_y_eleccion`. Si P30 pasa a escribir el id `_h`, el test cubre ambas formas. |
| C10 | T-393: sin `territorio_ids` 1.2.0 el id `_h` no se resuelve. | P43 depende de T-393. Orden: T-393 → P00 histórico (piloto nac22 2019-11) → T-395. |
| C11 | `datos_abiertos/INDEX.json` y `generar_datos_abiertos` asumen un M06 por territorio. | El histórico no entra en `datos_abiertos/` en la primera entrega (§12); test de que el INDEX no cambia con entradas históricas. |
| C12 | `p40-publicacion.yml` «Validar sitio candidato completo» (l. ~659-667) compara `observed_products` (kinds `static`, `canonical_m06`, `canonical_m08`) con **todos** los `products` del registro; `preparar_visor_ejecucion.add_registered_product` (l. ~306-329) lanza «kind no soportado» ante un kind desconocido. | Con `canonical_*` ambas comprobaciones **pasan sin cambio** (el kind está en la lista). Habría fallado con un kind `historico_epoca`: es una razón más para no crearlo. Riesgo restante: `add_registered_product` escribe `data/results/<t>/<run>/m0X.geojson` (sin elección en la ruta) y `viewer-results.json` incluye la fila con `election_date`; el visor v1/v2 que elige «el» producto por territorio podría tomar el histórico. Test: con el par histórico en el registro, `viewer-results.json` conserva las filas de 2023 y los visores v1/v2 siguen eligiendo el de 2023 (control positivo: pedir 2019-11-10 devuelve el histórico). Si falla, el cambio mínimo es filtrar por elección en la selección del visor, no en `add_registered_product`. |
| C13 | «Persistir registro sólo después del despliegue» (l. ~711-737) hace `git add -A` de `orchestracion/publicaciones_visor.json`, `datos/resultados`, `datos_abiertos` y `datos/composicion` y empuja a `main`. P43 **sí** escribe en `main` (solo ahí y tras desplegar). Además `datos/resultados/historico/<AAAAMM>/` ya existe (salida del paso A, legacy). | Test: con el par histórico, `datos_abiertos/INDEX.json` queda **idéntico** (D-154: sin datos abiertos en la primera entrega) y `datos/resultados/historico/` no se modifica; el visor lee una ruta propia (§7). `resultados_ligeros` y `generar_datos_abiertos` reciben la elección histórica solo por parámetro explícito. |
## 6. Ficheros y tests exactos (implementación, turno exclusivo, tras T-377 y T-393)

| Fichero | Cambio |
|---|---|
| `herramientas/registro_publicaciones_visor.py` (1.10.0, legacy) | validación de `fuente: historico_epoca`, `describe-historico`, `ELECCIONES_HISTORICO` (§3) |
| `herramientas/p40_resolver.py` (1.1.0, legacy) | subcomando `historico` (§4) |
| `.github/workflows/p40-publicacion.yml` (1.1.0, legacy) | opción «Histórico», `eleccion`, salida `modo`, cinco condiciones `if` y tres pasos nuevos (C1); mensaje de `Preparar promoción web` |
| `herramientas/preparar_visor_ejecucion.py`, selección de producto del visor v1/v2 | solo si falla el test de C12 |
| `herramientas/catalogo_procedencia.py` | producto `historico`, `eleccion_declarada=true` |
| `herramientas/resultados_ligeros.py`, `generar_datos_abiertos.py` | capa por elección histórica con `--registro` (§7) |
| `visor/v3/v3.js`, `visor/v3/calendario.json` | capa histórica (§7) |
| `herramientas/historico_epoca_r2.py` (nuevo) | escribir y leer `MANIFEST.json` de `productos/` (subida de P00, lectura de P43) |
| `tests/test_t372_p40_equivalencia.py` | diferencias esperadas (C2) |
| `docs/PLAN.md` | solo lo edita el planificador |

No se tocan: `check_pairs`, `linaje_m06_m08.py`, `composicion_m06.py`, `p50_resolver.py`, el motor (M04/M05). `historico_campana.py` e `historico_m07m08.py` (paso A sobre 2023) quedan como legacy: retirada o marca en una tarea aparte, no en esta. Sin cambio de huellas ni de checkpoints: no hace falta 00 nueva.

Tests (nuevo `tests/test_t395_p43_historico.py`, en rebanadas, con fuentes sintéticas y valores esperados literales o del CSV del BOE):
1. Entrada válida (par M06+M08): se acepta; falta `historico_id`, fecha fuera de tabla, `puerta.estado != PASS`, `k_oficial` ≠ `expected_districts`, `base_y_eleccion` distinto de (provincia, fecha[:7]) → `ValueError` con código.
2. Tabla de fechas = fechas de los 5 `resultados_oficiales_congreso_*.csv` del BOE (sha256 de cada fichero en el test).
3. `describe-historico`: lote de dos provincias PASS → 4 descriptores (par por provincia); una PUERTA sin PASS / sin M08 / sin distritos / sha256 distinto / dos elecciones → lote rechazado entero.
4. `merge-descriptors` con el par 2019-11 + `canonical_*` de 2023 del mismo territorio: coexisten sin pisarse; `vigente_por_eleccion(…, 2023)` sigue dando el de 2023 y `(…, 2019-11-10)` el histórico.
5. No-regresión de los **13** consumidores (`catalogo_procedencia`, `composicion_m06`, `evaluar_publicacion_visor`, `generar_datos_abiertos`, `generar_hemiciclo`, `generar_nombres_comunidades_nacional`, `legislatura_vigente`, `linaje_m06_m08`, `p50_resolver`, `preparar_visor_ejecucion`, `resultados_ligeros`, `resultados_partidos`, y el propio registro): con un registro de prueba que añade el par histórico, sus salidas con elección 2023 son byte a byte las de antes; el test cita la lista y falla si aparece un consumidor nuevo sin cubrir (`grep` de `canonical_m08`/`vigente_por_eleccion`); control positivo: pedir 2019-11-10 devuelve el histórico.
6. `check_pairs`/linaje: M08 histórico sin M06 propio → `PAR_INCOMPLETO`; M06 de 2023 no sirve de par; M08 de otro run que el M06 → fallo de linaje.
7. Resolver: R2 simulado (carpeta local): toma el `run_id` mayor con PASS; descarta y explica los demás; sin manifiesto → `P43_SIN_PRODUCTO`; sha256 alterado → `P43_HASH`.
8. Equivalencia de P40 (C2): sin «Histórico», pasos idénticos a los de 1.0.0; con «Histórico», `que_publicar` tiene 3 opciones, `simular` sigue por defecto `true`, el job `publicar` salta los pasos de la 00 y el entorno `github-pages` y la concurrencia `ddd-pages-prod` no cambian.
8b. «Validar sitio candidato completo» y `preparar_visor_ejecucion` aceptan el par histórico (C12): `observed_products == expected_products`, `viewer_path` y `observed_districts == expected_districts`; INDEX de `datos_abiertos` idéntico (C13).
9. `test_workflow_safety` (pin por SHA, permisos) y `test_t220_renombrado` sin cambios; gobernanza R015.
10. Con el piloto `nac22_h2019_11` (T-365): `PUERTA` real + M08 real del piloto → entrada válida (si el fichero cabe en el repo; si no, sha256 fijado y test saltado con motivo explícito, nunca en verde falso).

## 7. Visor

Estado actual: solo se ve 2023 nacional (`validElection()`). Para ver el histórico (D-125: «cada mapa se publica con su fecha y su procedencia, separado del vigente»):
- **Datos:** `resultados_ligeros.py --registro` emite por elección `datos/resultados/epoca/<AAAA-MM>/<nacNN>.json` (la ruta `datos/resultados/historico/` es del paso A y no se toca) (ganador por distrito, K oficial de la época, fecha, sha256 del M08). Los **distritos son los de esa elección** (M06 propio, §3); el visor no reutiliza la geometría de 2023.
- **Etiqueta pública (decidida por D-125, no abierta):** «Distritos de <fecha de la elección>, con datos de esa época» y, en el panel de procedencia, `datos_epoca` (año de seccionado y padrón, K oficial). Desaparece «reagregado al mapa propuesto». Es un ejercicio retrospectivo, no una propuesta de futuro: el texto lo dice.
- **`visor/v3/v3.js`:** `validElection()` pasa a «2023 o elección histórica con par M06/M08 en el catálogo»; los textos fijos «2023» (l. 450, 460, 467) salen de `S.election`; la capa de distritos, de la elección seleccionada. Los botones de la línea de tiempo nacional solo se activan si `catalogo_procedencia.json` trae el producto de esa elección; si no, siguen sin capa («Sin capa electoral certificada para esta fecha»).
- **Aviso ámbar (D-154):** una provincia con `semaforo: ambar` muestra `aviso_epoca` visible junto al mapa («Aviso: …»), nunca solo en el panel de procedencia. Las rojas no tienen capa.
- **Separado del vigente:** el hemiciclo, el estado de legislatura y las cifras «propuesta DDD» siguen siendo 2023/vigente; el histórico no alimenta ninguno.
- **`calendario.json`:** añadir las 5 fechas nacionales si faltan; test: cada fecha con capa existe en el registro.
- **No incluir** series de sección ni hemiciclo histórico (D-18).

Prueba local: `herramientas/ver_visor_v2_local.py` con registro de prueba (§10).
## 8. Orden de implementación

1. T-393 (ids + catálogo) y T-377 (P30) fusionadas.
2. P00 con `elección = AAAA-MM` y subida a R2 (piloto `nac22_h2019_11`; D-150 punto 4).
3. PR de P43 en tres commits: (a) registro + `describe-historico` + `historico_epoca_r2` + tests; (b) P40 «Histórico» + test de equivalencia; (c) catálogo de procedencia, resultados ligeros y visor.
4. Revisor independiente en cada una; fusiona el propietario (no `auto-merge`: toca P40).
5. Prueba real: P40 Histórico **con `simular` marcado** para nac22 2019-11; luego, con frase del propietario, sin simular, en el chat del Operador (D-52).

## 9. Riesgos

1. **Un mapa retrospectivo se lee como una propuesta a futuro.** D-125 lo cubre con la etiqueta de §7 y la separación del vigente; el visor no compara secciones entre épocas.
2. **Revisión y rebase de `p40-publicacion.yml`:** es compartido (T-372/T-377, D-134). Pedir turno exclusivo.
3. **Robots que reescriben el registro** (`orchestracion/publicaciones_visor.json`): la publicación es solo-adición con el publicador; sin cambios manuales.
4. **Costes:** P43 por lote sube blobs y reconstruye el sitio; 5 elecciones × ≤ 46 provincias en 5 lotes = 5 aprobaciones de `produccion` (P40 admite lotes; no se publica una elección partida).
5. **Colisión con el ensayo del 29-11 y con D-149:** nada de este diseño se ejecuta antes; sin ensayo con los workflows actuales.
6. **Tabla de fechas en código:** si una elección cambia de fecha en el registro electoral (`configuracion/registro_electoral.yaml`), el test la contrasta; hoy es solo una tabla fija de 5 elecciones.

## 10. Lo que no se puede probar sin Actions

| Qué | Por qué | Cómo se cubre |
|---|---|---|
| Flujo completo de P40 «Histórico» (resolver → R2 → blob → candidato → sitio → `github-pages`) | Usa secretos R2, la app de registro y el entorno `produccion`/`github-pages` | Pruebas unitarias del resolver con R2 simulado y del descriptor; ensayo de P40 con `simular` marcado, con permiso del Operador |
| Subida y lectura de R2 del cierre de P00 | Credenciales de R2 solo en Actions | Test del manifiesto con carpeta local; ensayo en la P00 piloto |
| Despliegue y aspecto del visor | Pages | `ver_visor_v2_local.py` con registro de prueba + captura; revisión humana |
| Tiempo y espacio de 5 elecciones | Reloj de Actions | Se mide con el piloto (T-365 §4: ~15 s en local) y se corrige aquí |
| Si P30 escribe `territorio` = `nac22` o `nac22_h2019_11` en la PUERTA | Depende de la implementación de T-377 | C9 admite ambas formas; el test de contrato se ajusta cuando T-377 fusione |

## 11. Alternativa descartada: reagregar sobre el mapa 2023 con un M06 reutilizado (v1.0 de este diseño y T-355)

Contradice D-125 (opción A): publicaría votos de 2019 sobre distritos de 2025 (T-351 obsoleta). Además dejaría sin M06 de la elección y haría que `check_pairs` ignorase el par en silencio. Se retira. Queda como **fase futura opcional** solo si el propietario la pidiese (otra decisión): un kind propio que no cuente como vigente.
## 12. Decisiones registradas y pendiente

**Registradas por el propietario (D-154, vía Planificador), ya incorporadas:**
1. Se publican las provincias del histórico en **verde** y las **ámbar con aviso visible** en el visor; las **rojas, nunca** (§3, §7).
2. **Primera entrega solo en el visor y en el catálogo de procedencia**; `datos_abiertos/` más adelante (C11, C13).
3. Etiqueta resuelta por D-125: «distritos de <fecha>, con datos de esa época» (§7).

**Pendiente (Planificador):** confirmar que el registro usa `canonical_m06`/`canonical_m08` con elección y `fuente: "historico_epoca"` y no un kind propio (§0.2, §3, C12). Si se mantiene un kind propio, hay que reimplementar `check_pairs`, la unicidad y los cambios de C12 en P40 y `preparar_visor_ejecucion`.
