# T-395 · Diseño: P43, publicación del histórico por fecha de elección (P40 y visor)

VERSIÓN: 1.5.0 · FECHA: 2026-11-17 · ESTADO: propuesta para el Planificador y el propietario (D-124, D-125, D-129, D-134, D-150, D-152)
ANTERIOR: 1.4.0 (#875@fbfa8ab); 1.3.0 (#875@29ddd0c, `canonical_*` con elección); 1.2.0 (#875@a2573e4); 1.1.0 (#875@25c83af); 1.0.0 (#875@67864de, asumía el mapa 2023 del paso A, contra D-125)
CAMBIOS 1.5.0 (revisor de #875@fbfa8ab, 4 menores): `catalogo_procedencia` exceptuado de «no ven el kind» (salida distinta por diseño, test); `label` y `publication_status` obligatorios (`_decorate_and_sort`, v3 `newest`); lectores que iteran `products` sin filtrar kind (C16) con decisión por lector y `grep` ampliado; rama de `_validate_entry` que rechaza `canonical` en `historico_*`.
CAMBIOS 1.4.0: **decisión del Planificador (17-11): opción B, kinds propios `historico_m06` y `historico_m08`** (aislamiento por construcción: un consumidor que no conoce el kind lo ignora; ninguna P00 histórica puede sustituir al vigente por tener `run_id` mayor). Cambian §0, D3, D6, D9, §3, §5 (C3, C4, C6, C8, C11, C12, C14), §6, §7, §11/§11b y §12. Se conserva lo de 1.2.0: `modo` y las cinco condiciones `if`, P43 sí escribe en `main`, fechas del BOE, `datos/resultados/epoca/`.
CAMBIOS 1.3.0 (re-revisión de #875@25c83af): selección por elección en el visor v3 y v1 con test (§7, §6, C14) y justificación frente al kind propio (§11b); `canonical` fuera de las entradas y D9 reescrita; el modo histórico y los pasos finales de P40 (`Registrar evidencia`, validación final) en C1; control positivo con `run_id` mayor; carga de la geometría de la elección en la capa nacional (§7); estado de D-150/152/154 y de T-393 (§Referencias).
CAMBIOS 1.2.0: D-154 (propietario, vía Planificador) registrado (§12); revisor independiente de 1.0.0: condiciones `if` exactas de P40 para el modo histórico (C1), `Validar sitio candidato completo` y `preparar_visor_ejecucion` (C12), `Persistir registro` (C13), prueba de no-regresión de los 13 consumidores (§6.5), origen verificable de las fechas (D8), ruta de datos distinta de la del paso A (§7) y estado de las referencias no fusionadas.
CAMBIOS 1.1.0: criterio del Planificador (D-125, opción A del propietario): el M06 de cada elección es el propio de P20 sobre `<t>_hAAAA_MM` y el M08 el de P30 sobre ese M06; sin reagregación al mapa 2023 (T-351 obsoleta). Cambian D3, D6, §3, §4, §5 (C3, C6), §7, §9, §11 y §12.
MOTIVO: D-134 dejó P43 «en tarea aparte tras el diseño del paso A». Este documento lo diseña. Solo documento: sin cambios en `ddd_core/`, `herramientas/`, workflows, `orchestracion/` ni datos. Base: `origin/main` f559cea8.
Referencias y su estado: T-355 = #830, **cerrada sin fusionar** (rama `t355-historico-publicacion`, sin merge-base con `main`; leída con `pull_request_read`, no ejecutada aquí). T-393 = #873@52a8419e, **abierta y sin fusionar**: sus ids `_h`, su `territorio_ids` 1.2.0 y sus 260 filas son diseño, no código en `main`; las cifras de provincias generables (39/27/33/35/46) son **suyas y no las he verificado**. T-378 = `docs/ESTUDIOS/T378_P00_CAMPANA/`, en `main` desde #858 (227b9fff, diseño 1.1). Decisiones: D-150 está en `docs/PLAN.md` de `main` (l. 301); **D-152 y D-154 no están en `main`** (PLAN 1.0.59): se citan como «decisión del propietario vía Planificador (17-11)» y se tratan como propuestos hasta que el Planificador los fusione; D-125 y D-129/D-134 sí están en `main`. Los hechos de `main` de este documento se midieron sobre f559cea8.

## 0. Resumen y recomendación

1. **Cada elección publica su propio par M06 + M08** (D-125): distritos generados con seccionado, padrón y K oficial de esa época (P20 sobre `<t>_hAAAA_MM`, T-393) y resultados de P30 sobre ese M06. **No hay reagregación al mapa 2023**: el paso A sobre 2023 (T-351, #819) queda como legacy (§1, §11).
2. **Registro: kinds propios `historico_m06` y `historico_m08`** (decisión del Planificador, 17-11), con `election_date`, `election_id` y `historico_id`. Un consumidor que no conoce el kind lo ignora (fallo seguro) y una P00 histórica no puede sustituir al vigente por tener `run_id` mayor. El par M06/M08 de la elección tiene su propio chequeo (`historico_par`, §3), porque `check_pairs` y la unicidad canónica no aplican. Coste: P40, `preparar_visor_ejecucion` y el visor deben aprender el kind (C12, C14).
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
| D3 | **Kinds `historico_m06` + `historico_m08`**, un par por provincia y elección, con `historico_id`, `election_date` y `fuente: "historico_epoca"`. Campos en §3. | Decisión del Planificador (17-11), opción B. Aislamiento por construcción; no se apoya en tocar bien 13 consumidores. |
| D4 | **`territory_id` = `nac22`; `historico_id` = `nac22_h2019_11`.** `territorio_ids.base_y_eleccion` (T-393 §2) los une. | El visor y `catalogo_procedencia` agrupan por provincia; T-393 dice que `_h` no es el mismo territorio-elección que `nac22` para catálogo, no para el visor. |
| D5 | **Fuente de P43 = R2 (`productos/<id>/<run>/…`) + manifiesto, no artefactos de Actions ni `main`.** | D-129: carpeta `productos/`. Los artefactos caducan; el cierre del histórico no escribe en `main` (T-393 §7, T-378). |
| D6 | **El M06 de la elección es el propio** (P20 sobre `<t>_hAAAA_MM`: seccionado y padrón del año, K = escaños oficiales de esa elección) y se registra con el M08 de P30 sobre él. **Nunca se reutiliza el M06 vigente ni se reagrega al mapa 2023** (D-125). | Es la opción A del propietario: ejercicio retrospectivo «quién habría mandado en ese momento», publicado con fecha y procedencia, separado del vigente. |
| D7 | **La puerta es la de T-342/T-343 y no se relaja:** `PUERTA.estado == "PASS"` (M07 PASS o PASS_WITH_DECLARED_EXCEPTIONS con ≤ 0,1 % salvo D-70) y contraste BOE. P43 solo comprueba que el JSON existe, su sha256 y que `territorio`, `clave` y `estado` cuadran con el `historico_id`. | P43 no decide la calidad; la decide P30. |
| D8 | **Fecha de la elección = tabla fija `ELECCIONES_HISTORICO`** (de T-355: 201911→2019-11-10, 201904→2019-04-28, 201606→2016-06-26, 201512→2015-12-20, 201111→2011-11-20), **Origen de cada fecha:** el campo `fuente` de `configuracion/resultados_oficiales_congreso_<AAAA>_<MM>.json` (BOE; 2011: «20 de noviembre de 2011», 2015: «20 de diciembre de 2015», 2016: «26 de junio de 2016», 2019-04: «28 de abril de 2019», 2019-11: «10-11-2019»). 2023 no entra (flujo vigente). | Datos oficiales nunca de memoria (CLAUDE.md). La tabla de T-355 era de memoria; aquí el test fija **literales** (las fechas de arriba) y comprueba que cada `fuente` del BOE las contiene (en texto largo o `dd-mm-aaaa`); no recalcula la tabla desde sí misma. |
| D9 | **Republicar** = nueva entrada del mismo (provincia, elección) con `run_id` mayor; vigente = mayor `run_id` dentro de (territorio, kind, elección), calculado solo por los lectores del histórico. Sin borrar ni `canonical`. | Registro solo-adición. |
| D10 | **P43 nunca se llama desde la 00 ni desde el Gestor.** Solo botón de P40 (con permiso del Operador). | Evita publicar histórico dentro de una campaña; el cierre de P00 no tiene `Publicar` para histórico. |

## 3. El registro: pares `historico_m06` + `historico_m08`

Una provincia y elección publican **dos entradas** con estos campos:

```json
{
  "id": "hm08-nac22_h2019_11-<run>",
  "kind": "historico_m08",
  "label": "M08 electoral · histórico 2019-11-10 · run <run>",
  "publication_status": "PUBLICABLE",
  "asset_type": "electoral_product",
  "stage": "M08",
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
  "aviso_epoca": null
}
```

La `historico_m06` lleva lo mismo salvo `puerta`, con `stage: "M06"` y su `label` (`M06 distritos · histórico …`). **`label` y `publication_status` son obligatorios**: `preparar_visor_ejecucion._decorate_and_sort` ordena por `item["label"]` (KeyError si falta) y v3 `newest()` exige `publication_status === "PUBLICABLE"`. Sin campo `canonical` (el registro actual no lo usa y `_validate_entry` solo lo admite en los kinds canónicos). `semaforo` es `verde` o `ambar` (D-154); `aviso_epoca` es obligatorio con `ambar` y lo muestra el visor; con `rojo` no se genera entrada. Activo inmutable (blob + sha256) como en las demás entradas.

Cambios en `registro_publicaciones_visor.py` (1.10.0, legacy):
- `HISTORICO_KINDS = {"historico_m06", "historico_m08"}` dentro de `PRODUCT_KINDS` y **fuera** de `CANONICAL_KINDS`, `SCENARIO_KINDS` y de la regla de `canonical`.
- `_validate_entry`: **rama nueva** `elif kind in HISTORICO_KINDS` **antes** de la genérica de `PRODUCT_KINDS` (que admite `canonical` None/True en todo kind de la lista, l. ~171-184): rechaza cualquier `canonical` distinto de `None`, y exige `label`, `publication_status == "PUBLICABLE"`, `historico_id` (forma de T-393 §2), `fuente == "historico_epoca"`, `election_date` ∈ `ELECCIONES_HISTORICO.values()`, `election_id` que termine en la fecha, `base_y_eleccion(historico_id) == (territory_id, election_date[:7])`, `datos_epoca.k_oficial == expected_districts`, `semaforo` ∈ {verde, ambar} con `aviso_epoca` si es ámbar y, en el M08, `puerta.estado == "PASS"`.
- **`historico_par(entries)`** (nuevo, en el registro; sustituye a `check_pairs` para estos kinds): por (territorio, elección) exige M06 y M08, mismo `run_id`, mismo `historico_id` y que el manifiesto acredite el linaje M06→M08 (sha256 del M06 usado por P30). Se llama desde `candidate` y desde `validate_registry`. `check_pairs` y `linaje_m06_m08` **no cambian** y no ven estos kinds.
- `identity_key` sin cambio. No hay unicidad canónica: el lector del histórico toma el `run_id` mayor dentro de su (territorio, kind, elección).
- `describe-production` no cambia; subcomando nuevo **`describe-historico`** (`--r2-manifest`, `--eleccion`, `--territorios`) que emite el par **con `label` y `publication_status`** (el lote se rechaza si falta). `rechazar_mapa_350` se mantiene (D-18/D-19). `ELECCIONES_HISTORICO` pasa a una tabla propia (fuente de D8).

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
| C1 | Los pasos del publicador de la 00 cuelgan de `needs.preparar.outputs.production_run_id != ''` (l. 313, 330, 399, 414, 433). La elección AAAA-MM no tiene run 00: `production_run_id` vacío = modo «solo sitio» (se saltarían todos, y «Promover» también, dejando el histórico sin publicar sin error). | El resolver emite una salida nueva `modo` ∈ {`00`, `historico`, `sitio`}, que `preparar` reexporta (`outputs`). Condiciones: **Normalizar lote, Recuperar ejecución, Acreditar identidad, Validar descriptores** pasan de `production_run_id != ''` a `modo == '00'` (equivalente: con ids = `00`; con `workflow_call` de la 00 y de las alternativas el resolver fija `00`); **Promover productos a blob** pasa a `modo == '00' \|\| modo == 'historico'` (solo consume `/tmp/product-descriptors.json`); **nuevos** «Recuperar de R2», «Acreditar manifiesto» y `describe-historico`, con `modo == 'historico'`, que escriben `/tmp/product-descriptors.json`. `Construir candidato` y el sitio se comparten. `Preparar promoción web` («Sin production_run_id: modo solo sitio») cambia su mensaje según `modo`. **Pasos finales** (l. ~681-689 y «Registrar evidencia», con `PRODUCTION_RUN_ID` vacío): usarían la rama «solo sitio» (`--requested-run-id ""`, sin comprobar nada del lote). Para `historico`, un paso nuevo «Acreditar publicación histórica» exige que cada id de `/tmp/product-descriptors.json` figure en `viewer-results.json` con `viewer_path` y `observed_districts == expected_districts`, y «Registrar evidencia» escribe `modo`, `historico_id`, run y sha256 de cada entrada. Test (C2): con `modo=00` los pasos son los de 1.0.0; con `historico` se saltan los cinco y entran los nuevos. |
| C2 | `tests/test_t372_p40_equivalencia.py` congela P40 contra los tres workflows viejos. | La PR de P43 actualiza el test con lista de diferencias esperadas y control negativo (sin la opción, P40 sigue equivalente). Aviso al dueño de T-372. |
| C3 | `check_pairs`/`pares_incompletos` solo ven `canonical_*` (clave por elección). | Un par histórico no los activa (aislamiento). Lo sustituye `historico_par` (§3): M08 sin M06 propio, runs distintos o `historico_id` distinto → `PAR_HISTORICO_INCOMPLETO`. Test de que `check_pairs` y `linaje_m06_m08` ignoran los kinds nuevos y de que un M06/M08 de 2023 no sirve de par histórico. |
| C4 | Los 13 consumidores de `canonical_*`/`vigente_por_eleccion` (lista en §1). | Filtran por kind: **no ven** `historico_*` (fallo seguro). No se afirma: el test de §6.5 los recorre **los 13**, más el dashboard y los datos abiertos, con un histórico de `run_id` mayor que el vigente. **Excepción de `catalogo_procedencia`:** recorre todos los `products` (l. 156-180) sin filtrar kind: el histórico **sí** entra, con `producto: "historico_m06"`/`"historico_m08"`, `eleccion` de su fecha, `vigente` por (territorio, kind, elección) y la comprobación de PUBLICADO; es la salida **distinta por diseño** (D-154: el catálogo de procedencia es una de las dos superficies de la primera entrega). Test: con el par histórico el catálogo solo **añade** esos productos (`productos` y `resumen.productos` crecen en lo esperado; los de 2023 y sus `vigente` no cambian) y `eleccion_declarada` es true. **Otros que no ignoran un kind desconocido:** `visor/escenarios.js` `stageOf` (`/_m08$/` ⇒ `historico_m08` sería «electoral» y `historico_m06` «territorial» en la v1) y `_decorate_and_sort` (`priority.get(kind, 9)`, no falla): ver C14. |
| C5 | `catalogo_procedencia._declarada`/`_eleccion` leen `election_date` sin declarar como 2023: un histórico sin fecha se leería como 2023. | `_validate_entry` exige la fecha en la tabla D8 si `fuente == "historico_epoca"`; test de `eleccion_declarada == true`. |
| C6 | `composicion_m06.py` (T-301) versiona la composición del M06 de cada descriptor (`canonical_m06`). | No ve `historico_m06`. En la primera entrega **no se versiona composición del histórico** (el visor solo necesita la geometría y el ganador por distrito, §7); queda para P43 fase 2. Test: `datos/composicion/` idéntico con el par histórico. |
| C7 | `rechazar_mapa_350` y `scenario_*`: el lote no mezcla. | Test: lote histórico + alternativas se rechaza; `congreso350_*` se rechaza. |
| C8 | `p50_resolver.py` y P50 usan `canonical_m08`. | No ven el kind nuevo; test (parte del §6.5). P50 3.7.0 no recibe `election_date`. |
| C9 | `PUERTA_<t>_<AAAA_MM>.json` usa `territorio = nac22` (T-365). | El manifiesto fija `historico_id`; el resolver comprueba que `territorio`+`clave` dan el `historico_id` por `base_y_eleccion`. Si P30 pasa a escribir el id `_h`, el test cubre ambas formas. |
| C10 | T-393: sin `territorio_ids` 1.2.0 el id `_h` no se resuelve. | P43 depende de T-393. Orden: T-393 → P00 histórico (piloto nac22 2019-11) → T-395. |
| C11 | `datos_abiertos/INDEX.json` y `generar_datos_abiertos` asumen un M06 por territorio. | No ven el kind: el histórico no entra en `datos_abiertos/` en la primera entrega (D-154); test: INDEX idéntico. |
| C12 | `p40-publicacion.yml` «Validar sitio candidato completo» (l. ~659-667): `observed_products` solo cuenta `static`, `canonical_m06`, `canonical_m08` y lo compara con **todos** los `products` del registro: una entrada `historico_*` abortaría («viewer/registro inconsistentes»). `preparar_visor_ejecucion.add_registered_product` (l. ~306-329) lanza «kind no soportado para producto». | **Se adaptan ambos** (el coste de B). P40: el conjunto de kinds de `observed_products` pasa a incluir `historico_m06`, `historico_m08`. `preparar_visor_ejecucion`: rama nueva para `historico_*` que escribe `data/results/epoca/<AAAA-MM>/<territorio>/<run>/m0X.geojson` (ruta distinta de la vigente) y `priority` ordena los kinds nuevos al final. Tests: lote con el par histórico → `observed_products == expected_products`, `viewer_path` y `observed_districts == expected_districts`; sin la adaptación el mismo test falla (control negativo). |
| C13 | «Persistir registro sólo después del despliegue» (l. ~711-737) hace `git add -A` de `orchestracion/publicaciones_visor.json`, `datos/resultados`, `datos_abiertos` y `datos/composicion` y empuja a `main`. P43 **sí** escribe en `main` (solo ahí y tras desplegar). Además `datos/resultados/historico/<AAAAMM>/` ya existe (salida del paso A, legacy). | Test: con el par histórico, `datos_abiertos/INDEX.json` queda **idéntico** (D-154: sin datos abiertos en la primera entrega) y `datos/resultados/historico/` no se modifica; el visor lee una ruta propia (§7). `resultados_ligeros` y `generar_datos_abiertos` no reciben el histórico (ver C15). |
| C14 | La v1 (`visor/app.js` + `visor/escenarios.js`) lista todos los `results` por territorio y `stageOf` clasifica por sufijo: `historico_m0X` aparecería mezclado con el vigente. v3 (`newest()` por `run_id`, l. 231) **no** ve el kind nuevo. | **Fijo, sin condicional:** (1) v3 lee `historico_m06/m08` **solo en la vista del histórico** (`loadEpoca(prov, S.election)`, cargador nuevo que busca en `D.products.results` los kinds `historico_*` de la provincia con `election_date` de prefijo `AAAA-MM` de `S.election`; `"201911"` → `"2019-11"`) y `newest()` del vigente no los ve; (2) v1 excluye `historico_*` en `bootstrap`/`refreshResults`. Tests con Node sobre `viewer-results.json` sintético: (a) histórico con `run_id` **mayor**: v1 y v3 siguen mostrando el vigente en `loadAutonomic`, `newest`, grupos y selector; (b) control negativo: sin la exclusión de la v1, (a) falla; (c) `loadEpoca("nac22","201911")` devuelve el par y `loadEpoca("nac22","202307")` no devuelve nada; (d) `node --check`. |
| C15 | El paso del sitio (l. ~557) invoca `resultados_ligeros.py --registro` **sin `--eleccion`** (defecto 2023-07-23, l. 190; con otra elección escribiría en `datos/resultados/<fecha>/` y solo lee `canonical_m08`). Nadie emite `datos/resultados/epoca/`. | Paso nuevo en P40 con `modo == 'historico'`: **«Emitir resultados de época»**, que para cada elección del lote ejecuta `resultados_ligeros.py --registro /tmp/publicaciones_visor.candidate.json --eleccion <AAAA-MM-DD> --kind historico --salida /tmp/site-candidate/datos/resultados/epoca/<AAAA-MM>`. `--kind` (nuevo, por defecto `canonical`) elige `historico_m08`. El paso 557 no cambia. Tests: con el par histórico, el paso 557 produce los mismos ficheros que sin él; `--kind historico` escribe `epoca/2019-11/nac22.json` con ganador por distrito, K y sha256; sin entradas históricas escribe vacío y falla cerrado si la elección pedida no existe en el registro. |
| C16 | Lectores que iteran `products` **sin filtrar kind** (medidos con `grep` de `get("products"`/`["products"]`): `p70_resolver.py` l. 85-89, `archivar_artefactos_r2.py` l. 103-106, `generar_estado_operativo.py` l. 465 (y `catalogo_procedencia.py`, C4). El resto filtra kind (`historico_autonomico`, `legislatura_vigente`, `generar_datos_abiertos`, `resultados_partidos`, `p50_resolver`, `composicion_m06`) o no lee este registro (`g10_*`); `inventario_ids_no_canonicos.py` solo informa por kind. | **Decisión por lector:** (a) `p70_resolver.fecha_eleccion`: **se excluye** `historico_*` (una línea): P70 sigue rechazando elecciones históricas (`P70_ELECCION_SIN_FECHA`) como hoy; archivar o podar histórico es otra tarea. Test: con el par histórico, `fecha_eleccion(root, "2019-11")` sigue fallando y `"2023-07"` igual. (b) `archivar_artefactos_r2`: **sin cambio, es lo deseado**: el run histórico publicado queda en `runs` y sus artefactos se archivan, no se podan como no publicados. Test: el run histórico figura en `runs` con territorio `nac22`. (c) `generar_estado_operativo` (territorios con «algún producto» = publicados): **se filtra** `historico_*`, para que una provincia con solo histórico no figure como publicada. Test: territorio con solo `historico_*` → no publicado; con `canonical_m08` → sí. |
## 6. Ficheros y tests exactos (implementación, turno exclusivo, tras T-377 y T-393)

| Fichero | Cambio |
|---|---|
| `herramientas/registro_publicaciones_visor.py` (1.10.0, legacy) | `HISTORICO_KINDS`, validación, `historico_par`, `describe-historico`, `ELECCIONES_HISTORICO` (§3) |
| `herramientas/p40_resolver.py` (1.1.0, legacy) | subcomando `historico` (§4) |
| `.github/workflows/p40-publicacion.yml` (1.1.0, legacy) | opción «Histórico», `eleccion`, salida `modo`, cinco `if` y pasos nuevos («Recuperar de R2», «Acreditar manifiesto», `describe-historico`, «Emitir resultados de época», «Acreditar publicación histórica»), kinds de `observed_products` (C12), mensaje de `Preparar promoción web` |
| `herramientas/preparar_visor_ejecucion.py` | rama `historico_*` y `priority` (C12) |
| `herramientas/resultados_ligeros.py` | `--kind historico` (C15) |
| `herramientas/catalogo_procedencia.py` | lectura explícita del producto `historico` (`eleccion_declarada=true`) |
| `visor/v3/v3.js` (legacy), `visor/v3/calendario.json` | `loadEpoca`, `validElection()` por elección con par, textos de `S.election`, aviso ámbar (§7); `newest()` no cambia |
| `visor/app.js`, `visor/escenarios.js` | exclusión de `historico_*` (C14) |
| `herramientas/p70_resolver.py`, `herramientas/generar_estado_operativo.py` | excluyen `historico_*` (C16 a y c) |
| `herramientas/historico_epoca_r2.py` (nuevo) | `MANIFEST.json` de `productos/` (subida de P00, lectura de P43) |
| `tests/test_t372_p40_equivalencia.py` | diferencias esperadas (C2) |
| `docs/PLAN.md` | solo lo edita el planificador |

No se tocan: `check_pairs`, `linaje_m06_m08.py`, `composicion_m06.py`, `p50_resolver.py`, `generar_datos_abiertos.py`, `generar_hemiciclo.py`, el motor (M04/M05). `historico_campana.py` e `historico_m07m08.py` (paso A sobre 2023) quedan como legacy: tarea aparte. Sin cambio de huellas ni de checkpoints: no hace falta 00 nueva.

Tests (nuevo `tests/test_t395_p43_historico.py`, en rebanadas, con fuentes sintéticas y valores esperados literales):
1. Entrada válida (par `historico_m06` + `historico_m08`): se acepta; falta `historico_id`, fecha fuera de tabla, `puerta.estado != PASS`, `k_oficial` ≠ `expected_districts`, `base_y_eleccion` distinto de (provincia, fecha[:7]), `canonical` presente, ámbar sin `aviso_epoca` → `ValueError` con código.
2. Fechas (D8): los literales 2011-11-20, 2015-12-20, 2016-06-26, 2019-04-28 y 2019-11-10 coinciden con `ELECCIONES_HISTORICO` y cada `fuente` de `configuracion/resultados_oficiales_congreso_<AAAA>_<MM>.json` contiene su fecha (`20 de noviembre de 2011`, `20 de diciembre de 2015`, `26 de junio de 2016`, `28 de abril de 2019`, `10-11-2019`); el sha256 de cada JSON está fijado en el test.
3. `describe-historico`: lote de dos provincias PASS → 4 descriptores; PUERTA sin PASS / sin M08 / sin distritos / sha256 distinto / dos elecciones / rojo → lote rechazado entero.
4. `merge-descriptors` + `candidate`: el par 2019-11 y los `canonical_*` de 2023 del mismo territorio coexisten sin pisarse; `validate_registry` acepta el registro; `vigente_por_eleccion` y `catalogo_procedencia` devuelven lo mismo que antes.
5. **No-regresión con histórico de `run_id` mayor** (regla común: salida con 2023 byte a byte igual; el test cita la lista y falla si aparece un consumidor nuevo sin cubrir, por `grep` de `canonical_m08`/`vigente_por_eleccion`/`PRODUCTION_KINDS` **y de `get("products"` / `["products"]`**, §5 C16). Los 13 con control propio (**`catalogo_procedencia` exceptuado**: su test es el de C4, no «byte a byte igual»): `catalogo_procedencia`, `composicion_m06`, `evaluar_publicacion_visor` (`PRODUCTION_KINDS`: un run histórico con `--strict-request` no se acepta como producción vigente), `generar_datos_abiertos` (INDEX idéntico), `generar_hemiciclo`, `generar_nombres_comunidades_nacional`, `legislatura_vigente`, `linaje_m06_m08`, `p50_resolver`, `preparar_visor_ejecucion` (rutas vigentes sin cambio), `resultados_ligeros` (paso 557 igual), `resultados_partidos`, y el propio registro. **Además el dashboard** (`generar_estado_operativo.py`, que acepta M08 de otros runs, #354) y los datos abiertos: sin cambios.
6. `historico_par`: M08 sin M06 → `PAR_HISTORICO_INCOMPLETO`; M06 de otro run, otro `historico_id` o sha256 de linaje distinto → fallo; `check_pairs` ignora los kinds nuevos.
7. Resolver: R2 simulado: toma el `run_id` mayor con PASS y semáforo verde o ámbar; rojo descartado con motivo; sin manifiesto → `P43_SIN_PRODUCTO`; sha256 alterado → `P43_HASH`.
8. Equivalencia de P40 (C2): sin «Histórico» y `modo=00`, pasos idénticos a 1.0.0; con «Histórico», 3 opciones, `simular` por defecto `true`, el job `publicar` salta los pasos de la 00 y entran los nuevos; `github-pages` y `ddd-pages-prod` sin cambio.
8a. Visor (C14 a-d) con Node.
8b. P40/`preparar_visor_ejecucion` aceptan el par histórico (C12) y «Emitir resultados de época» (C15); sin `label` o sin `publication_status` el lote se rechaza en `describe-historico` y en `_validate_entry` (control negativo: `_decorate_and_sort` lanzaría KeyError); `canonical` en un `historico_*` → `ValueError`. Lectores de C16 (a, b, c).
9. `test_workflow_safety` y `test_t220_renombrado` sin cambios; gobernanza R015.
10. Con el piloto `nac22_h2019_11` (T-365): `PUERTA` y M08 reales → entrada válida (si no caben en el repo, sha256 fijado y test saltado con motivo explícito).

## 7. Visor

Estado actual: solo se ve 2023 nacional (`validElection()`). Para ver el histórico (D-125: «cada mapa se publica con su fecha y su procedencia, separado del vigente»):
- **Datos:** el paso «Emitir resultados de época» de P40 (C15) escribe por elección `datos/resultados/epoca/<AAAA-MM>/<nacNN>.json` (ganador por distrito, K oficial de la época, fecha, sha256 del M08). La ruta `datos/resultados/historico/` es del paso A y no se toca. Los **distritos son los de esa elección** (`historico_m06`, §3); el visor no reutiliza la geometría de 2023.
- **Etiqueta pública (decidida por D-125, no abierta):** «Distritos de <fecha de la elección>, con datos de esa época» y, en el panel de procedencia, `datos_epoca` (año de seccionado y padrón, K oficial). Desaparece «reagregado al mapa propuesto». Es un ejercicio retrospectivo, no una propuesta de futuro: el texto lo dice.
- **`visor/v3/v3.js`:** lee `historico_*` **solo en la vista del histórico** (`loadEpoca`, C14) y `newest()` del vigente no los ve; `validElection()` pasa a «2023 o elección histórica con par `historico_m06/m08` en el catálogo»; los textos fijos «2023» (l. 450, 460, 467) salen de `S.election`; la capa de distritos, de la elección seleccionada. Los botones de la línea de tiempo nacional solo se activan si `catalogo_procedencia.json` trae el producto de esa elección; si no, siguen sin capa («Sin capa electoral certificada para esta fecha»).
- **Aviso ámbar (D-154):** una provincia con `semaforo: ambar` muestra `aviso_epoca` visible junto al mapa («Aviso: …»), nunca solo en el panel de procedencia. Las rojas no tienen capa.
- **Separado del vigente:** el hemiciclo, el estado de legislatura y las cifras «propuesta DDD» siguen siendo 2023/vigente; el histórico no alimenta ninguno.
- **`calendario.json`:** añadir las 5 fechas nacionales si faltan; test: cada fecha con capa existe en el registro.
- **No incluir** series de sección ni hemiciclo histórico (D-18).

Prueba local: `herramientas/ver_visor_v2_local.py` con registro de prueba (§10).
## 8. Orden de implementación

1. T-393 (ids + catálogo) y T-377 (P30) fusionadas.
2. P00 con `elección = AAAA-MM` y subida a R2 (piloto `nac22_h2019_11`; D-150 punto 4).
3. PR de P43 en tres commits: (a) registro (kinds, `historico_par`, `describe-historico`) + `historico_epoca_r2` + `preparar_visor_ejecucion` + tests; (b) P40 «Histórico» (modo, `if`, pasos nuevos, `observed_products`) + `resultados_ligeros --kind` + test de equivalencia; (c) catálogo de procedencia y visor (v3 `loadEpoca`, v1 exclusión).
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

## 11. Alternativas descartadas

- **Reagregar sobre el mapa 2023 con un M06 reutilizado** (v1.0 y T-355): contradice D-125 (opción A); T-351 obsoleta.
- **`canonical_m06/m08` con `election_date`** (v1.1-1.3 de este diseño): menos código en lo compartido y conserva T-249, pero un histórico de `run_id` mayor se mezcla con el vigente en los consumidores que no filtran por elección (v3 `newest`, v1) y la seguridad depende de tocar bien 13 consumidores. Descartada por el Planificador (17-11).

## 11b. Riesgos de la opción B (kinds propios), declarados

| Riesgo | Mitigación |
|---|---|
| P40 aborta («viewer/registro inconsistentes») y `preparar_visor_ejecucion` lanza «kind no soportado» ante `historico_*` | Se adaptan en la misma PR (C12), con control negativo |
| La v1 clasifica `historico_m0X` por sufijo y lo mezcla | Exclusión explícita y test (C14) |
| `historico_par` es código nuevo en vez de `check_pairs` | Test propio (§6.6); `check_pairs` queda intacto |
| Un lector del histórico futuro puede olvidar elegir el `run_id` mayor dentro de la elección | Helper único `historico_vigente(registro, eleccion)` en el registro y test de su uso |
| Sin composición del M06 histórico en la primera entrega (C6) | Declarado; fase 2 |

## 12. Decisiones registradas y pendiente

**Decisión del Planificador (17-11):** opción B, kinds propios `historico_m06` y `historico_m08` (§0.2, §3, §11b).

**Registradas por el propietario (D-154, vía Planificador, 17-11; aún no en `PLAN.md` de `main`), ya incorporadas:**
1. Se publican las provincias del histórico en **verde** y las **ámbar con aviso visible** en el visor; las **rojas, nunca** (§3, §7).
2. **Primera entrega solo en el visor y en el catálogo de procedencia**; `datos_abiertos/` más adelante (C11, C13).
3. Etiqueta resuelta por D-125: «distritos de <fecha>, con datos de esa época» (§7).

Sin preguntas abiertas en este documento.
