# T-313 — Diseño de la migración de notación M0x → P2x/P3x

VERSIÓN: 1.0.0 · FECHA: 2026-11-17 · ANTERIOR: ninguna (fichero nuevo) · solo diseño (ningún cambio de código). Base: `origin/main` 6454079. Sustituye a las §4 y
«Decisiones del Planificador (14-11)» de `INVENTARIO.md` (#784), que usan la numeración anterior a D-129 y no se reescribe.
Fija las decisiones del propietario del 17-11: D-165 (renombrado; actualiza D-102) y D-166 (las 11 recomendaciones de este diseño). Citas: D-102, D-129, D-138, D-142.

## 1. Equivalencias (decisión 1) y qué cambia respecto a #784

| Hoy | Nueva | Nombre | Notas |
|---|---|---|---|
| M01 | P21 | Base y población | |
| M02 | P22 | Geometría y adyacencias | |
| M03 / M03U | P23 / P23U | Grafo / unidades internas | |
| pre-M04, M04 | pre-P24, P24 | Solución inicial | `m04_engine.json` → `p24_motor.json` (mismo nº de versión) |
| M05 | P25 | Optimización | `M05_REPARACION_POBLACIONAL_GENERICA` → `P25_REPARACION_…` |
| M06 | P26 | Producto certificado | |
| auditoría geométrica | P27 | Auditoría | |
| ensembles (GerryChain 25/50) | — | P28 **retirado** (D-138) | sin fila de alias; `ddd_ensemble` se queda (D-138) y T-380 retira lo publicado (D-141); solo sus referencias Mxx |
| M07 | P31 | Agregación | |
| M08 | P32 | Resultados por distrito | |
| puerta (04) | P33 | Puerta | |

Correcciones a #784: **P41/P42 ya no son M07/M08** (son P40 sitio y lotes, D-129); por tanto `canonical_p42` y `-P41/-P42` del
14-11 quedan anulados: el `kind` nuevo es `canonical_p26` y `canonical_p32`, y los estados `-P31`/`-P32`.
P40 = Publicación con P41 sitio y P42 lotes (D-129); no tienen relación con M07/M08.
Quedan fuera (no son módulos): versiones del motor (`7.4.x`, `m04_engine` como nº), estudios N06/N07/N08.

## 2. Mecanismo: tabla de alias única (decisión 2)

- `configuracion/notacion_fases.csv`: una fila por identificador (`id_viejo, id_nuevo, tipo, escribe_nuevo, lee_ambos`); sha256 literal
  anclado en `tests/test_t313_fases.py` (mecánica de T-220: `configuracion/notacion_territorial.csv` + `ddd_core/territorio_ids.py`).
- `ddd_core/fases_ids.py`: `resolver_fase(id)` (viejo o nuevo → nuevo), `alias_lectura(id)` (nuevo → [nuevo, viejo]) y
  `normalizar_prefijo` (`M04_*`→`P24_*`). Único lugar con los nombres viejos. Los workflows lo llaman con
  `python -m ddd_core.fases_ids <id>`; el visor (JS) lee un `fases.json` generado desde la CSV (test de coherencia).
- **Guardián** `tests/test_t313_fases.py`: recorre `git ls-files`; falla si queda un id viejo vivo fuera de `EXENTOS`
  (legacy, `docs/registro|ESTUDIOS|AUDITORIAS|SALIDAS_CHATGPT|RONDAS|EJECUCIONES`, `tests/fixtures`, `tests/legacy`,
  `territorios/*/evidencia|resultados`, `datos`, `resultados`, `publicado`, `evals`, `orchestracion/archivo_r2.json`, `publicaciones_visor.json`
  históricas, `fases_ids.py` y la CSV). Tokeniza Python para no marcar comentarios históricos; `\bP25\b`/`\bP50\b` con límite de palabra.

## 3. Inventario por capa (`git grep -lIE`, sin `legacy/`)

Patrón: `\bM0[1-8]\b|M0[1-8]_|-M0[1-8]\b|m0[1-8]_|modulos/0[1-8]_|pre_m04|M03U|canonical_m0[68]|m04_engine`. Total **3.727** ficheros de 11.256
no-legacy (más que los ~2.760 de #784: patrón ampliado y `territorios/` creció). «Nombre» = ficheros con Mxx en el nombre.

| Capa (PR) | Ficheros con patrón | Nombre | Acción |
|---|---|---|---|
| Código y módulos: `modulos/` | 8 | 8 | renombrar |
| `ddd_core` | 30 | 16 (`m04_*` 7, `m05_*` 8, `m06_schema`) | renombrar |
| `ddd_motor2`, `ddd_ensemble` | 6, 4 | 0 | ids/imports |
| `paquetes/` (Deslinde) | 12 | 0 | **no tocar API** (ver riesgo 4) |
| Herramientas | 133 | 29 | renombrar + `huella_checkpoint_m05.py` |
| Workflows (11 de 15) | 11 | — | `p20-distritos` 145 refs; `ejecucion-completa` 24 y `gestor-campanas` 5 **desaparecen con T-379 PR 3**; `p30` 22, `p70` 21, `p40` 13, `p90` 10, `p80` 5, `p50` 3, `p10` 2, puerta 2 |
| Tests vivos (sin fixtures/legacy) | 232 | 52 | renombrar (`test_m0x_*`, `test_pre_m04_*`) |
| Config/esquemas/orquestación | 29 / 3 / 8 | 2 / 1 / 1 | `p24_motor.json`, `verificacion_independiente_m03_m06.json`, `m06-district-catalog.schema.json`, `almacen_m06_r2.json` |
| Visor y público | 7 + 6 + 2 + 2 (`visor`, `documentacion_publica`, `publicado`, `dashboard`) | 0 | lector con alias; textos «M06/M08» |
| Docs vivas | `.claude` 16, `docs/ARQUITECTURA` 16, `docs/MODULOS` 10 (9 con nombre), `docs/ORQUESTACION` 6, `CLAUDE.md` | 9 | reescribir |
| **Jerga «la 00/04…»** (sin históricos) | ~340 apariciones (`la 00` 190, `la 04` 67, `la 05` 26, `la 03` 24, `la 02` 18, `otra 00` 8, `la 01` 3) en `.claude` 13, `docs/ARQUITECTURA` 8, `.github` 10, `herramientas` 31, `ddd_core` 2, +~25 tests | — | ver PR 7 |
| Histórico/congelado (alias, 0 cambios) | `territorios` 1.425, `tests/fixtures` 851, `docs/ESTUDIOS` 371, `docs/registro` 180, `datos` 95, `docs/AUDITORIAS` 62, `docs/SALIDAS_CHATGPT` 57, `evals` 23, `resultados` 20, `docs/RONDAS` 12, `docs/EJECUCIONES` 9, `datos_abiertos` 2 | — | solo lectura por alias |

Renombrados de fichero: **≈121** (8 + 16 + 29 + 52 + 9 `docs/MODULOS` + 7 sueltos: config 2, datos 2, orchestracion 1, schemas 1, `requirements-gerrychain-m05.lock`).
`tests/fixtures` (851) y `territorios/*` conservan nombres viejos: los lectores los aceptan.

## 4. Lista cerrada de identificadores persistidos y su alias

Escritura nueva con nombre nuevo; lectura de ambos (`resolver_fase`). «No se reescribe» = dato ya guardado.

| # | Identificador persistido | Nuevo | Dónde está guardado hoy | Política |
|---|---|---|---|---|
| 1 | `kind` `canonical_m06` / `canonical_m08` | `canonical_p26` / `canonical_p32` | `publicaciones_visor.json` (339: 174/163), visor `app.js`/`escenarios.js`, registro, P50 | las 337 no se reescriben; visor, registro y P50 leen ambos |
| 2 | Artefactos Actions `ddd-state-<run>-M03`, `-M03U`, `-M04`?, `-M05`, `-M06`, `-M08` (+ sufijos de reanudación) | `-P23`, `-P23U`, `-P24`, `-P25`, `-P26`, `-P32` | runs vivos (caducan a 14 días) | nuevos con P; selector baja P26→P25→P24→P23 probando ambos nombres; por decisión 3 un checkpoint viejo no se reutiliza (se regenera) |
| 3 | `ddd-minimo-<run>-M06` / `-M08` | `-P26` / `-P32` | R2 (173 + 173) y artefactos | productos: lectura por alias permanente (los consumen P40/P50/P72); nuevos con P |
| 4 | Claves R2 de `archivo_r2.json` (720 objetos, 358 con Mxx) y prefijos `arc-p/m06/…` de `almacen_m06_r2.json` (0 objetos) | claves nuevas con P | `orchestracion/archivo_r2.json` | no se renombran en R2 (carpetas R2: tarea aparte de D-131); `almacen_m06_r2.json` nace con nombre nuevo (coste 0) |
| 5 | Directorios `M01…M08` de `territorios/*/resultados/ejecuciones/gh-<run>/` | `P21…P26`, `P31`, `P32` | 122 territorios | no se reescriben; lectores (`linaje_m06_m08`, `composicion_m06`, certificador, dashboard) aceptan ambos |
| 6 | Ficheros de producto `<slug>_m01_secciones_poblacion`, `_m03_grafo`, `_m04_semillas`, `_m05_distritos_optimizados`, `_m06_distritos`/`_secciones`/`_composicion_distritos`/`_catalogo_distritos`/`_contiguedad_geometrica`/`_resumen_distritos`, `_m07_resumen_electoral`/`_reconciliacion`, `_m08_distritos_resultados`; informes `m0x_informe.json`, `m0x_report.json` | prefijo `p2x_`/`p3x_` | `territorios/*`, `datos/`, `datos_abiertos/INDEX.json`, blobs publicados | no se reescriben; salen con nombre nuevo al regenerar/republicar (cambia sha del ZIP: ver riesgo 6) |
| 7 | Claves y códigos dentro de JSON: `m06_run`, `m05_executed`, `m01_artifact_sha`, `m0x_artifact_name`, `pre_m04_*` (`_evidence`, `_diagnostic`, `_topology`, `_accreditation`, `_implementation_binding`, `_run_id`, `_source_commit`, `_artifact_sha`), códigos `M04_INFEASIBLE`, `M04_PARTITION_UNIT`, `M05_SUCCESS`, `M03_PROMOTABLE`, `M06_DIAGNOSTIC`, `M07_RECONCILIATION`, `M08_ABSENT`… | cambio mecánico de prefijo `M0x`→`P2x/P3x`, `pre_m04`→`pre_p24` | manifiestos (`CHECKPOINT_RUN_ID`, `chain`), evidencias, `catalogo_procedencia.json` (71), `estado_*.json`, `checkpoints_fase1.json` | `normalizar_prefijo` en cada lector; manifiestos históricos no se reescriben |
| 8 | Ids de job/`needs`/outputs/etiquetas de log de `p20-distritos.yml`: `m01,m02,m03,internal_units,pre_m04_evidence,pre_m04_diagnostic,m04,m05,m06`, input `versiones_m05`, modo `m05`, `M0x_RESULT` | `p21…p26`, `pre_p24_*`, `versiones_p25` | solo en YAML (no persistido) | renombrar sin alias; no son checks requeridos (`veredicto`, `pruebas` intactos) |
| 9 | Huella M05 (`engine_files`: cierre de imports de `modulos/05_*`), evidencia pre-M04 (`modulos/04_*`) | huella con rutas nuevas | checkpoints, `source-index.json`, N08 | cambian a propósito (decisión 3); ver riesgo 1 |
| 10 | Config: `m04_engine.json`, `verificacion_independiente_m03_m06.json`, `schemas/m06-district-catalog` | `p24_motor.json`, `…_p23_p26.json`, `p26-district-catalog` | `configuracion/`, `schemas/` | renombrar; el esquema nuevo declara el viejo como alias |

Fuera de la lista (no se tocan, no son ids de fase): `ddd-audit`, `ddd-publication`, `ddd-full-run`; versiones de motor; `7.4.x`.

## 5. Orden de las PR (decisión 4), dependencias y criterio de hecho

Todas con `no-automerge`, una capa cada una, revisor independiente y fusión por el propietario. **Regla de capa**: cada PR renombra lo
suyo y corrige mecánicamente (por script con la tabla) las rutas/imports que eso rompe en cualquier otra capa, para que `main` y la
CI sigan en verde; los nombres de job/artefacto/textos de otras capas van en su PR. Precondiciones: T-379 PR 3 y T-383 fusionadas y
validadas; sin runs de la 00 abiertos; histórico congelado (D-164).

| PR | Capa | Depende de | Criterio de hecho |
|---|---|---|---|
| 0 | Ensayo local previo (sin PR): 1 territorio P21→P26 y P31/P32 con contrato temporal, salidas de referencia | — | línea base guardada (hash de contenido por fichero) |
| 1 | **Tabla + resolvedor + lectores con alias** (visor, registro de publicaciones, selector de checkpoint, `archivo_r2`, `linaje`, `composicion`, certificador, dashboard) y guardián en modo «lista de pendientes» | T-379 PR 3, T-383 | no cambia ningún comportamiento; tests: resolver, sha de la tabla, lectores aceptan ambos (fixtures viejos + datos nuevos sintéticos) |
| 2 | **Código y módulos**: `modulos/0X_*`→`modulos/p2x_*`/`p3x_*`, `ddd_core/m0x_*`, `ddd_motor2`/`ddd_ensemble` ids, `p24_motor.json`, huellas, VERSIÓN/ANTERIOR | 1 | suite completa verde; salida del ensayo local = línea base salvo nombres; huellas nuevas calculadas y documentadas |
| 3 | **Herramientas** (29 renombradas + referencias) | 2 | idem; `p24`/`p25` CLIs con alias de argumento solo si un workflow vivo los usa |
| 4 | **Workflows**: jobs/inputs/artefactos/`versiones_p25`, escritura con nombre nuevo; test de equivalencia por workflow | 2, 3 | los `test_t3xx_*_equivalencia` pasan con nombres nuevos; un workflow en seco (simular) por familia con frase del Operador |
| 5 | **Tests** (52 `test_m0x_*`/`pre_m04`→`test_p2x_*`) y guardián pasa a «sin pendientes» | 2-4 | guardián en verde sobre `git ls-files` sin lista de pendientes |
| 6 | **Documentación viva** (`CLAUDE.md`, `.claude/rules`, skills, `docs/ARQUITECTURA`, `docs/MODULOS`, `EQUIVALENCIAS_D129.md` con tabla de §1) | 5 | el test de T-383 (workflow inexistente) amplía a ids de fase; reglas R015 actualizadas |
| 7 | **Jerga «la 00/04…»** → P00/P20/P30/P40 etc. en texto vivo (~340 apariciones) | 6 | grep de la jerga = 0 fuera de `EXENTOS` |

Validación posterior (no es parte de las PR; la lanza el Operador con frase): P00 de prueba sobre un territorio con «Generar desde fuente»,
M06 equivalente en contenido al de referencia, y regeneración de las 71 con huellas nuevas.

## 6. Riesgos

1. **Huellas M05/N08.** Renombrar `modulos/05_*` o cualquier `ddd_core` del cierre cambia `engine_files` → todos los M05/M06 previos quedan
   incompatibles (a propósito, decisión 3). `modulos/04_*` invalida la evidencia pre-M04 de los 4 territorios con `physical_components`
   (Canarias, Baleares, Las Palmas, Santa Cruz de Tenerife): hay que regenerarla con `handoff_evidencia_pre_m04` antes de su 00. N08 (hashes
   de ficheros activos) pasaría a fallar: el verificador lee N08 contra la copia de `legacy/` por alias, no se regenera el estudio.
   Efecto práctico: 00 en «Generar desde fuente» o «Ejecutar desde el principio»; antes, inventario de lo reutilizable y test de flujo.
2. **Reutilizar restaura nombres viejos.** El selector (`seleccionar_checkpoint_productivo.py`) debe ignorar por regla los nombres viejos
   (no solo no encontrarlos): test explícito.
3. **Visor y registro.** Si un lector no acepta ambos `kind`, el visor pierde 337 productos (T-125). PR 1 va antes de cualquier escritor nuevo.
4. **Deslinde / `ddd_motor2`.** `paquetes/deslinde` (12 ficheros) cita `M03…M06` y la clave `m06_secciones` (4) en su API; es paquete versionado
   (1.0/1.1, DOI). No se toca su API ni se republica; el adaptador de `ddd_motor2` traduce. Solo se renombran sus referencias a ficheros del repo si las hubiera.
5. **P25/P50 en grep.** Tras migrar, `P25` = optimización y `P50` = Publicación académica; hoy `P50` aparece en 27 ficheros con el sentido viejo de
   publicación y `P25` en 2. Guardián con límite de palabra; `ensemble25/50` (nombres que se conservan en `ddd_ensemble`) nunca como número suelto.
6. **Shas de datos abiertos.** Renombrar ficheros dentro de ZIP/GeoJSON publicados cambia `datos_abiertos/INDEX.json`; solo ocurre al
   regenerar/republicar. Test de equivalencia de contenido (no de nombre).
7. **Conflictos entre PR** en `workflows/`, `herramientas/`, `ddd_core/`: congelar PR ajenas en la capa mientras dure cada PR.
8. **Artefactos en vuelo** (14 días): ninguna PR se fusiona con runs abiertos.
9. **Gobernanza R015/R016** (VERSIÓN/ANTERIOR + copia en `legacy/`): 121 renombrados = ~121 copias; ver pregunta 3.

## 7. Preguntas abiertas (con recomendación)

1. **Ventana.** ¿Cuándo? *Recomiendo después de la noche del 29-11 y de fusionada T-379 PR 3*: invalida huellas y obliga a regenerar las 71; no tocar entre la validación (24-11) y el ensayo.
2. **Nombres de módulos y ficheros.** *Recomiendo*: `modulos/p21_base_poblacion.py`, `p22_geometria_adyacencias`, `p23_grafo`, `p24_solucion_inicial`, `p25_optimizacion`, `p26_producto_certificado`, `p31_agregacion`, `p32_resultados_distrito`; `ddd_core/p24_*`, `p25_*`, `p26_schema`; la auditoría sin módulo propio nuevo. (Levanta la norma «no renombrar `modulos/0X_*`» de la skill implementador y R015, a anotar en PR 6.)
3. **Copias en `legacy/` de 121 renombrados.** *Recomiendo*: `git mv` + `ANTERIOR: <ruta vieja>`; copia en `legacy/` solo de los 8 módulos y las huellas; R015 se adapta en PR 2.
4. **Claves y códigos dentro de JSON** (fila 7). *Recomiendo* cambio mecánico de prefijo con `normalizar_prefijo` en lectores, no lista a mano; los manifiestos viejos no se tocan.
5. **Alias de `ddd-minimo-…-M06/M08` (fila 3).** *Recomiendo permanente* (son los productos en R2 y los lee P72/P50); el alias de `ddd-state-…` (fila 2) solo de lectura y sin reutilización.
6. **Ficheros de producto y datos abiertos (fila 6).** *Recomiendo* nombre nuevo solo al regenerar; sin republicar las 71 por esta causa.
7. **Deslinde.** *Recomiendo* no tocar `paquetes/deslinde`; adaptador en `ddd_motor2`.
8. **`almacen_m06_r2.json` y carpetas R2.** *Recomiendo* dejarlo a la tarea de renombrar carpetas R2 (D-131, tras el paso 9) y no archivar nada antes; hoy 0 objetos.
9. **`pre_m04` → `pre_p24`.** *Recomiendo sí* (decisión 14-11 vigente); regenerar la evidencia de los 4 territorios con `physical_components` dentro de la regeneración de las 71.
10. **Congelación.** *Recomiendo* congelar PR ajenas solo en la capa de la PR en curso (no todo el repo) y PR 2-4 consecutivas en el mismo día.
11. **Etiquetas del visor** («M06/M08», constantes `M06_BINS`). *Recomiendo* renombrar texto visible y constantes en PR 1/4; `kind` solo con alias.
