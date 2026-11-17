# T-395 · Diseño: P43, publicación del histórico por fecha de elección (P40 y visor)

VERSIÓN: 1.0.0 · FECHA: 2026-11-17 · ESTADO: propuesta para el Planificador y el propietario (D-124, D-129, D-134, D-150, D-152)
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: D-134 dejó P43 «en tarea aparte tras el diseño del paso A». Este documento lo diseña. Solo documento: sin cambios en `ddd_core/`, `herramientas/`, workflows, `orchestracion/` ni datos. Base: `origin/main` f559cea8.
Parte de: T-355 (#830, cerrada sin fusionar; sus 3.048 líneas siguen en la rama `t355-historico-publicacion`), §7 de T-393 (PR #873, ids `<t>_hAAAA_MM`, opción A) y T-378 (§2, §8, §14).

## 0. Resumen y recomendación

1. **Un registro, un tipo nuevo.** Las entradas del histórico llevan `kind: historico_epoca` (no `canonical_m08`). Un M08 histórico no es «el vigente» de nada: así no entra por accidente en hemiciclo, legislatura, datos abiertos ni en la regla de pares M06/M08 (§3, §5).
2. **`territory_id` del registro = provincia (`nac22`); el id propio `nac22_h2019_11` va en `historico_id`.** El visor agrupa por provincia y elección; el id `_h` es identidad de producción (run, artefactos, checkpoints), no de visor (§3).
3. **P43 no es un workflow nuevo: es la tercera opción de «Qué publicar» de P40** («Histórico»), con `elección` (AAAA-MM) y `territorios`; mismo `simular` marcado, todo o nada y sitio completo (§2).
4. **P00 con elección AAAA-MM no publica ni escribe en `main`.** Deja M08 + `PUERTA` en R2 con manifiesto sha256 y un issue; P43 lo recoge de R2 (§4). Se mantiene «`Publicar = sí` se rechaza con aviso en histórico» de T-393 §7.
5. **T-355 se rescata, no se reabre:** de #830 se reutilizan el descriptor por PUERTA y sus fallos cerrados (`PUERTA_NO_PASS`, `SIN_M08`, `SIN_DISTRITOS`, `CLAVE_HISTORICA`, `CLAVE_REPETIDA`), reescritos para el kind nuevo, el id `_h` y la fuente R2. Se descarta su parte de workflows (los dos ficheros ya no existen) y su `election_date` en P50 (§6).
6. **Visor:** hoy `validElection()` de `visor/v3/v3.js` está cableado a `202307`. Hace falta una capa «histórico» explícita; sin ella los datos publicados no se ven (§7).
7. **Detrás de T-377 y de T-393 (ids), con turno exclusivo.** Lo no probable sin Actions está en §10.

## 1. Qué hay hoy (medido sobre `origin/main`)

| Pieza | Estado |
|---|---|
| Registro `registro_publicaciones_visor.py` 1.8.1 | Dimensión de elección opcional desde 1.5.0 (`election_date`, `election_id`; `eleccion_de(entry)`; sin fecha = `ELECCION_POR_DEFECTO` 2023-07-23). Identidad = (territorio, kind, run/escenario, elección). `canonical=true` único por (territorio, familia, elección). Solo-adición. |
| `check_pairs` / `linaje_m06_m08.pares_incompletos` | Por (territorio, elección): si **no** hay `canonical_m06` de esa elección, `continue` (no exige nada). Un `canonical_m08` histórico sin M06 pasaría **en silencio**, sin la garantía de T-249. |
| Consumidores de `canonical_m08` / `vigente_por_eleccion` | 13 ficheros: `catalogo_procedencia`, `composicion_m06`, `evaluar_publicacion_visor`, `generar_datos_abiertos`, `generar_hemiciclo`, `generar_nombres_comunidades_nacional`, `legislatura_vigente`, `linaje_m06_m08`, `p50_resolver`, `preparar_visor_ejecucion`, `resultados_ligeros`, `resultados_partidos`, y el propio registro. Todos filtran por elección con valor por defecto 2023. |
| P40 (`p40-publicacion.yml` 1.0.0) | `workflow_dispatch`: `que_publicar` (Solo el sitio \| Territorios), `territorios`, `simular` (true). Jobs `resolver` → `preparar` → `publicar`. `resolver` llama a `herramientas/p40_resolver.py` (última 00 completa con la 04 en verde por territorio, de `territorios/<t>/evidencia/ejecuciones_completas/`). El publicador descarga artefactos `ddd-*` (selectiva → completa → R2), acredita (`evaluar_publicacion_visor`), `describe-production`, `merge-descriptors`, promueve a blob, `candidate`, construye el sitio. Cabecera: «P43 (histórico por fecha) queda fuera: tarea aparte». Congelado por `tests/test_t372_p40_equivalencia.py`. |
| Paso A (`historico_campana.py` 1.5.0, `historico_m07m08.py`) | Produce por provincia y elección el M08 reagregado sobre el **mapa 2023** (sin `--mapa`) y `PUERTA_<t>_<AAAA_MM>.json` (M07, perdidos, contraste BOE). 294 pares en la ficha 2026-11-14; con `publicar=no` («la 04 del histórico no está adaptada»). |
| Visor v3 (`visor/v3/v3.js`) | `S.election` por defecto `"202307"`; `validElection()` = `nacional && "202307"`; con otra fecha muestra «Sin capa electoral certificada para esta fecha». El panel de procedencia ya lee `catalogo_procedencia.json` por prefijo `AAAA-MM` y la fecha `prod.eleccion`. |
| T-393 §7 | `elección = AAAA-MM` + `congreso` → `nacNN_hAAAA_MM`; 52 ≤ 256 jobs; cierre histórico «no escribe en `main` hasta T-355». |

## 2. Decisiones

| # | Decisión | Por qué |
|---|---|---|
| D1 | **P43 = opción «Histórico» de `que_publicar` en P40.** Campos: `eleccion` (lista cerrada AAAA-MM: 2011-11, 2015-12, 2016-06, 2019-04, 2019-11), `territorios` (códigos `nacNN`; vacío = todos los de esa elección con M08 en R2), `simular` (marcado). | D-129/D-130: un workflow por familia, opciones dentro, sin parámetros técnicos. Reutiliza el publicador (blob, candidato, preflight, sitio). |
| D2 | **Todo o nada por lote y una elección por lote.** Un territorio sin M08 válido, PUERTA ≠ PASS o hash que no cuadra rechaza el lote (`P43_LOTE_RECHAZADO`). | Fail-closed de T-355 y de P40. Una elección por lote conserva `CLAVE_REPETIDA`. |
| D3 | **`kind: historico_epoca`**, un registro por (provincia, elección). Campos en §3. | Un M08 histórico no es vigente. Con `canonical_m08` heredaría `check_pairs`, la unicidad canónica y la lectura de hemiciclo/legislatura (§5). |
| D4 | **`territory_id` = `nac22`; `historico_id` = `nac22_h2019_11`.** `territorio_ids.base_y_eleccion` (T-393 §2) los une. | El visor y `catalogo_procedencia` agrupan por provincia; T-393 dice que `_h` no es el mismo territorio-elección que `nac22` para catálogo, no para el visor. |
| D5 | **Fuente de P43 = R2 (`productos/<id>/<run>/…`) + manifiesto, no artefactos de Actions ni `main`.** | D-129: carpeta `productos/`. Los artefactos caducan; el cierre del histórico no escribe en `main` (T-393 §7, T-378). |
| D6 | **M06 de la elección = el M06 publicado del territorio** (mapa 2023 del paso A), referenciado, no re-registrado: `m06_ref: {entry_id, run_id, sha256}`. | Es lo que hace el paso A (reagrega sobre el mapa 2023). Un M06 propio por época (P20 `_h`) es la fase 2; el formato lo admite (`m06_ref.modo = "propio"`), sin implementarlo. |
| D7 | **La puerta es la de T-342/T-343 y no se relaja:** `PUERTA.estado == "PASS"` (M07 PASS o PASS_WITH_DECLARED_EXCEPTIONS con ≤ 0,1 % salvo D-70) y contraste BOE. P43 solo comprueba que el JSON existe, su sha256 y que `territorio`, `clave` y `estado` cuadran con el `historico_id`. | P43 no decide la calidad; la decide P30. |
| D8 | **Fecha de la elección = tabla fija `ELECCIONES_HISTORICO`** (de T-355: 201911→2019-11-10, 201904→2019-04-28, 201606→2016-06-26, 201512→2015-12-20, 201111→2011-11-20), verificada contra `configuracion/resultados_oficiales_congreso_<AAAA>_<MM>.csv` (BOE). 2023 no entra (flujo vigente). | Datos oficiales nunca de memoria (CLAUDE.md): el test compara la tabla con los ficheros del BOE. |
| D9 | **Republicar** = nueva entrada del mismo (provincia, elección) con `run_id` mayor; vigente por el mayor `run_id` (criterio de `vigente_por_eleccion`). Sin borrar. | Registro solo-adición. |
| D10 | **P43 nunca se llama desde la 00 ni desde el Gestor.** Solo botón de P40 (con permiso del Operador). | Evita publicar histórico dentro de una campaña; el cierre de P00 no tiene `Publicar` para histórico. |

## 3. El registro: entrada `historico_epoca`

```json
{
  "id": "hist-nac22-2019_11-<run>",
  "kind": "historico_epoca",
  "asset_type": "electoral_product",
  "stage": "M08",
  "territory_id": "nac22",
  "historico_id": "nac22_h2019_11",
  "territory_label": "Huesca",
  "run_id": "<run de la P00 histórica>",
  "election_date": "2019-11-10",
  "election_id": "generales_nac22_2019-11-10",
  "expected_districts": 3,
  "puerta": {"estado": "PASS", "m07": "PASS", "sha256": "<hex>"},
  "m06_ref": {"modo": "reutiliza_publicado", "entry_id": "…", "run_id": "…", "sha256": "…"},
  "mapa": "2023",
  "label": "M08 electoral · histórico 2019-11-10 · run <run>",
  "publication_status": "PUBLICABLE",
  "canonical": false
}
```

Más el activo inmutable (blob + sha256 del ZIP M08) como en las demás entradas.

Cambios en `registro_publicaciones_visor.py` (1.10.0, legacy):
- `HISTORICO_KINDS = {"historico_epoca"}` dentro de `PRODUCT_KINDS`, **fuera** de `CANONICAL_KINDS` y de `SCENARIO_KINDS`.
- `_validate_entry`: exige `historico_id` (forma de T-393 §2), `election_date` ∈ `ELECCIONES_HISTORICO.values()`, `election_id` que termine en la fecha, `puerta.estado == "PASS"`, `m06_ref`, `canonical` ausente o `false`, `base_y_eleccion(historico_id) == (territory_id, election_date[:7])`.
- `identity_key` sin cambio (territorio, kind, run, elección).
- `describe-production` no cambia; nuevo subcomando **`describe-historico`** (`--r2-manifest`, `--eleccion`, `--territorios`) en lugar de sobrecargar `es_raiz_historica` (T-355 mezclaba las dos formas en la misma función y su detección por «no hay `production_status.json`» es frágil).
- `rechazar_mapa_350` se mantiene (D-18/D-19).

## 4. Qué publica P00 con elección AAAA-MM y cómo lo recoge P43

**P00 (cierre histórico), por provincia y elección, sin `main`:**
1. P20 produce el M06 `_h` y P30 el M08 + `PUERTA_<t>_<AAAA_MM>.json` (T-365: `electoral`). Hoy el piloto usa el mapa 2023; el formato fija `mapa`.
2. Subida a R2 `productos/nac22_h2019_11/<run>/`: `m08_distritos_resultados.geojson.zip`, `resumen_electoral.csv`, `PUERTA_….json`, `MANIFEST.json`. `MANIFEST.json` lleva `historico_id`, `run_id`, `clave`, `fecha`, `mapa`, sha256 de cada fichero y K. Verificación de lectura tras subir (ya existe `restaurar_estado_r2.py` para el patrón).
3. Issue del cierre con una línea por provincia (PASS/FALLA y causa del contrato). **Ningún commit, ningún registro.**
4. `Publicar = sí` con histórico: rechazado en la comprobación previa con aviso «el histórico se publica con P40 → Histórico».

**P43 (P40 con «Histórico»):** el resolver nuevo `p40_resolver.py historico --eleccion AAAA-MM [--territorios …]` lista `productos/` de R2, toma por provincia el `MANIFEST.json` del `run_id` mayor con PUERTA PASS, verifica sha256 y devuelve JSON (`entradas`, `descartadas` con motivo). Los errores salen como `::error::P43_…` con rc 1, como `P40_…`.

**Qué se descarta de T-355:** la lectura de `ddd-historico-*` (artefacto con solo CSV); el parámetro `election_date` de P50; los cambios en `historico_m07m08.py` 1.2.0 (copiar el M08 a `salida_historico`): con R2 como fuente ya no hace falta.

## 5. Qué choca con P40, el registro y los consumidores

| # | Choque | Resolución |
|---|---|---|
| C1 | El publicador de P40 espera un run de la 00 (`production_run_id`, artefactos `ddd-*`, `evaluar_publicacion_visor --strict-request`, `describe-production`). El histórico no tiene run 00 ni artefactos. | Ruta nueva dentro del job `publicar`: pasos «Recuperar de R2», «Acreditar manifiesto» y `describe-historico`, con `if: inputs.que_publicar == 'Histórico'`; los pasos de la 00 se saltan. El resto (blob, `candidate`, preflight, sitio) se comparte. Mismo patrón que la ruta del ensemble (`!cancelled()`). |
| C2 | `tests/test_t372_p40_equivalencia.py` congela P40 contra la copia de los tres workflows viejos: añadir una opción y pasos rompe la equivalencia. | La PR de P43 actualiza el test con una **lista de diferencias esperadas** (opción nueva y pasos con `if` histórico) y un control negativo: sin la opción, P40 sigue siendo equivalente. Tarea de la PR de implementación, con aviso al dueño de T-372. |
| C3 | `check_pairs` ignora un M08 de una elección sin M06 (`continue`). | No se reutiliza `canonical_m08`: `historico_epoca` tiene su propio chequeo `historico_ref_ok` (el `m06_ref` existe en el registro, su sha256 coincide y es del mismo territorio). `check_pairs` no cambia (test: no se vuelve más laxo). |
| C4 | Los 13 consumidores filtran por `canonical_m08`/elección. | Con un kind nuevo **ninguno cambia de comportamiento** (control de no-regresión: salida idéntica con el registro actual + entradas `historico_epoca`). Solo se añaden lectores nuevos: `catalogo_procedencia` (producto `historico` con `eleccion` y `vigente`) y `resultados_ligeros`/`generar_datos_abiertos` (capa histórica, §7). |
| C5 | `catalogo_procedencia._declarada`/`_eleccion` y el visor usan `election_date` sin declarar → 2023. Un histórico mal fechado se leería como 2023. | `_validate_entry` exige fecha en la tabla D8; test de que `eleccion_declarada` es true. |
| C6 | `composicion_m06.py` (T-301) exige la composición del M06 de cada descriptor y la versiona. | `describe-historico` no emite M06; `m06_ref` apunta a la composición ya versionada. Test: P43 no llama a `composicion_m06` y no la escribe. |
| C7 | `rechazar_mapa_350` y `scenario_*`: el lote no mezcla. | Test: lote con `historico_epoca` + alternativas se rechaza; `congreso350_*` se rechaza. |
| C8 | `herramientas/p50_resolver.py` (usa `canonical_m08`) y P50 publicación académica: no deben ver el histórico. | Sin cambio; test de que `p50_resolver` ignora `historico_epoca`. P50 3.7.0 no recibe `election_date`. |
| C9 | `PUERTA_<t>_<AAAA_MM>.json` usa `territorio = nac22` (T-365), no `nac22_h2019_11`. | El manifiesto fija `historico_id`; el resolver acepta `territorio` + `clave` y comprueba que dan el `historico_id` por `base_y_eleccion`. Si P30 pasa a escribir el id `_h`, el test lo cubre en ambas formas. |
| C10 | T-393: hasta que no exista `territorio_ids` 1.2.0, el id `_h` no se resuelve. | P43 depende de T-393. Orden: T-393 → P00 histórico (piloto nac22 2019-11) → T-395 (implementación). |

## 6. Ficheros y tests exactos (implementación, turno exclusivo, tras T-377 y T-393)

| Fichero | Cambio |
|---|---|
| `herramientas/registro_publicaciones_visor.py` (1.10.0, legacy) | `historico_epoca`, validación, `describe-historico`, `historico_ref_ok`, `ELECCIONES_HISTORICO` (§3) |
| `herramientas/p40_resolver.py` (1.1.0, legacy) | subcomando `historico` (§4) |
| `.github/workflows/p40-publicacion.yml` (1.1.0, legacy) | opción «Histórico», `eleccion`, pasos con `if` (C1) |
| `herramientas/catalogo_procedencia.py` | producto `historico`, `eleccion_declarada=true` |
| `herramientas/resultados_ligeros.py`, `generar_datos_abiertos.py` | capa por elección histórica con `--registro` (§7) |
| `visor/v3/v3.js`, `visor/v3/calendario.json` | capa histórica (§7) |
| `herramientas/historico_epoca_r2.py` (nuevo) | escribir y leer `MANIFEST.json` de `productos/` (subida de P00, lectura de P43) |
| `tests/test_t372_p40_equivalencia.py` | diferencias esperadas (C2) |
| `docs/PLAN.md` | solo lo edita el planificador |

No se tocan: `canonical_*`, `check_pairs`, `linaje_m06_m08.py`, `composicion_m06.py`, `p50_resolver.py`, `historico_m07m08.py`, el motor (M04/M05). Sin cambio de huellas ni de checkpoints: no hace falta 00 nueva.

Tests (nuevo `tests/test_t395_p43_historico.py`, en rebanadas, con fuentes sintéticas y valores esperados literales o del CSV del BOE):
1. Entrada válida: se acepta; falta `historico_id`, fecha fuera de tabla, `puerta.estado != PASS`, `canonical: true`, `base_y_eleccion` distinto de (provincia, fecha[:7]) → `ValueError` con código.
2. Tabla de fechas = fechas de los 5 `resultados_oficiales_congreso_*.csv` del BOE (sha256 de cada fichero en el test).
3. `describe-historico`: lote de dos provincias PASS → 2 descriptores; una PUERTA sin PASS / sin M08 / sin distritos / sha256 distinto / dos elecciones → lote rechazado entero.
4. `merge-descriptors` con `historico_epoca` + `canonical_m08` de 2023 del mismo territorio: coexisten sin pisarse; `vigente_por_eleccion(canonical_m08, 2023)` sigue dando el de 2023; la elección 2019-11 no devuelve nada por `canonical_m08`.
5. No-regresión: con un registro de prueba que contiene entradas `historico_epoca`, las salidas de `resultados_ligeros`, `generar_datos_abiertos`, `generar_hemiciclo`, `legislatura_vigente` y `p50_resolver` son **byte a byte** las de antes (control positivo: quitar el kind nuevo del filtro las hace fallar).
6. `check_pairs`: no más laxo (M08 canónico sin M06 sigue fallando como hoy) y `historico_ref_ok` falla con `m06_ref` inexistente o sha256 distinto.
7. Resolver: R2 simulado (carpeta local): toma el `run_id` mayor con PASS; descarta y explica los demás; sin manifiesto → `P43_SIN_PRODUCTO`; sha256 alterado → `P43_HASH`.
8. Equivalencia de P40 (C2): sin «Histórico», pasos idénticos a los de 1.0.0; con «Histórico», `que_publicar` tiene 3 opciones, `simular` sigue por defecto `true`, el job `publicar` salta los pasos de la 00 y el entorno `github-pages` y la concurrencia `ddd-pages-prod` no cambian.
9. `test_workflow_safety` (pin por SHA, permisos) y `test_t220_renombrado` sin cambios; gobernanza R015.
10. Con el piloto `nac22_h2019_11` (T-365): `PUERTA` real + M08 real del piloto → entrada válida (si el fichero cabe en el repo; si no, sha256 fijado y test saltado con motivo explícito, nunca en verde falso).

## 7. Visor

Estado actual: solo se ve 2023 nacional (`validElection()`). Para ver el histórico:
- **Datos:** `resultados_ligeros.py --registro` (y `generar_datos_abiertos.py`) emiten `datos/resultados/historico/<AAAA-MM>/<nacNN>.json` (ganador por distrito, K, fecha, sha256 del M08, `mapa`). El mapa y los distritos son los del M06 publicado (D6): la capa histórica se dibuja sobre las geometrías 2023. El visor lo dice: «Resultados de AAAA-MM reagregados al mapa de distritos propuesto».
- **`visor/v3/v3.js`:** `validElection()` pasa a «2023 o elección histórica con capa en el catálogo»; los textos fijos «2023» (l. 450, 460, 467) salen de `S.election`; los botones de la línea de tiempo nacional se activan solo si `catalogo_procedencia.json` trae un producto `historico` de esa elección (si no, siguen sin capa, como hoy). Provincias sin M08 histórico: «Sin capa electoral certificada para esta fecha» (mensaje actual).
- **Comparación histórica de una sección**: sigue sin dibujarse (texto vigente del panel «Evolución»); fuera de P43.
- **`calendario.json`:** añadir las 5 fechas nacionales si faltan; el test comprueba que cada fecha de la línea de tiempo con capa existe en el registro.
- **No incluir** todavía series ni hemiciclo histórico (D-18: sin contenido por iniciativa propia).

El visor no se puede probar en Actions sin sitio desplegado: la prueba local es `herramientas/ver_visor_v2_local.py` con el registro de prueba (§10).

## 8. Orden de implementación

1. T-393 (ids + catálogo) y T-377 (P30) fusionadas.
2. P00 con `elección = AAAA-MM` y subida a R2 (piloto `nac22_h2019_11`; D-150 punto 4).
3. PR de P43 en tres commits: (a) registro + `describe-historico` + `historico_epoca_r2` + tests; (b) P40 «Histórico» + test de equivalencia; (c) catálogo de procedencia, resultados ligeros y visor.
4. Revisor independiente en cada una; fusiona el propietario (no `auto-merge`: toca P40).
5. Prueba real: P40 Histórico **con `simular` marcado** para nac22 2019-11; luego, con frase del propietario, sin simular, en el chat del Operador (D-52).

## 9. Riesgos

1. **Publicar un mapa de 2023 con votos de 2019** puede leerse como la «distribución real» de 2019. Mitigación: etiqueta del visor y `mapa` en el registro; decisión de redacción del propietario.
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

## 11. Alternativa descartada: `canonical_m08` con `election_date` (la de T-355)

Reutiliza el registro sin kind nuevo y los 13 consumidores ya filtran por elección, pero: (1) `check_pairs` ignora silenciosamente la elección sin M06; (2) `canonical=true` único por (territorio, familia, elección) hace pasar por «vigente» un M08 sin su M06; (3) `generar_hemiciclo`/`legislatura_vigente` quedan a un cambio de valor por defecto de leer histórico como vigente; (4) el id `_h` se pierde (el `territory_id` de T-355 era el de la provincia sin traza de época). Se descarta salvo que el propietario prefiera menos código y más vigilancia en los consumidores.

## 12. Pendiente del propietario y del Planificador

- ¿Etiqueta pública del mapa («reagregado al mapa propuesto»)? (riesgo 1).
- ¿Se publican las provincias con avisos (T-364: 46 municipios; 2011 con D-70) o solo las del semáforo verde de T-393 §7? Recomendación: solo verde y ámbar con aviso visible; rojo, nunca.
- ¿El histórico entra en `datos_abiertos/` (cada release) o solo en el visor? Recomendación: solo visor y catálogo de procedencia en la primera entrega.
