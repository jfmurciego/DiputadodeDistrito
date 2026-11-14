# T-313 — Inventario para migrar la notación M01-M08 a P21-P26 y P40

Solo lectura sobre `origin/main` (c4e4206, 2026-11-14). Recuentos con `git grep`/`git ls-files` (ficheros versionados).
Patrón M: `\bM0[1-8]\b|M0[1-8]_|-M0[1-8]\b|m0[1-8]_|modulos/0[1-8]_`. La migración no se hace aquí.

## 1. Equivalencias (framework §2, citado)

| Fase | Contenido (framework) | Hoy |
|---|---|---|
| P20 | Producción territorial | M01 a M06 |
| P21 | Población y secciones | M01 |
| P22 | Geometría y alias | M02 |
| P23 | Grafo | M03 |
| P24 | Semillas | M04 |
| P25 | Optimización: canónico y GerryChain | M05 y estrategias GerryChain 25 y 50 |
| P26 | Consolidación y certificación territorial | M06 y auditoría geométrica |
| P40 | Producción electoral | M07 y M08, workflow 04 |

El framework dice «P21 a P25 es ajustable» y «no renombrar `modulos/0X_*`: están en huellas M05, evidencias N08 y R015/R016;
los ficheros se renombran en una migración propia».

**Ambigüedades a decidir antes de migrar**
1. M02 ↔ P22 «Geometría y alias», pero `modulos/02_construir_adyacencias.py` y `docs/MODULOS/M02_ADYACENCIAS.md` son adyacencias; el grafo es M03. Falta decidir si P22 absorbe adyacencias.
2. M07 y M08 caen ambos en P40 sin subfase: hay que fijar P41/P42 (o P40a/b) porque hoy son módulos, estados (`-M08`) y artefactos (`-M08`) distintos.
3. «Auditoría geométrica» (`M06_INDEPENDENT_GEOMETRIC_AUDIT`, 244 apariciones) entra en P26 sin id propio.
4. «Estrategias GerryChain 25 y 50» en P25: `25`/`50` no son fases pero chocan visualmente con P25/P50 (P50 = Archivo y distribución). Riesgo de confusión P25/P50 en grep.
5. Pre-M04 (`pre_m04_evidence`, `pre_m04_diagnostic`, «binding pre-M04», D-82), `M03U` (artefacto `ddd-state-<run>-M03U`) y `M05_REPARACION_POBLACIONAL_GENERICA` no tienen equivalente.
6. «Mxx» también nombra versiones del motor (`m04_engine`, `7.4.x`) y los N08/N06/N07 (estudios, no módulos): no confundir con M0x.
7. Regla de alias: ¿M05 → P25 también en `docs/MODULOS/M05_*` y en lecciones históricas? Propuesta §4: lo histórico no se reescribe.

## 2. Inventario cuantificado

Total: **4.398** ficheros con el patrón; **1.640** en `legacy/` (copias; no se tocan) → ~**2.760** vivos.

| Categoría | Ficheros | Detalle |
|---|---|---|
| Módulos `modulos/0X_*` | 8 | `01_preparar_base_territorial` … `08_integrar_resultados`; copias en `legacy/modulo01…08` (2/6/6/23/21/6/5/3 = 72) |
| Código `ddd_core` | 30 con patrón (16 nombrados `m04_*`, `m05_*`, `m06_schema`) | + 33 refs en `legacy/ddd_core` |
| `ddd_motor2`, `ddd_ensemble`, `paquetes/` | 5 / 4 / 12 con patrón | solo menciones; ninguno nombrado Mxx |
| `herramientas/` | 127 con patrón; 29 con Mxx en el nombre | huellas: `huella_checkpoint_m05.py`, `huella_checkpoint_motor.py`, `seleccionar_checkpoint_productivo.py` |
| `tests/` | 189 con patrón (fuera de fixtures); 52 con Mxx en el nombre; 76 citan `modulos/0X_*` | `tests/fixtures` 204 más (evidencia congelada: no se tocan) |
| Workflows | 17 de 24 | `_reutilizable-generacion-territorial.yml` 145 refs (jobs `m01,m02,m03,pre_m04_*,m04,m05,m06`); resto: `_reutilizable-incorporacion-electoral` 25, `ejecucion-completa-proyecto` 24, `generar-alternativas-territoriales` 17, `_reutilizable-publicar-sitio` 17, `produccion-distritos` 16, `recuperar-producto-electoral-durable` 14, `bateria-motor` 13 (+ input `versiones_m05`, modo `m05`), `cadena-publicacion` 12, `pruebas-plataforma` 9, `mantenimiento-programado` 8, otros ≤6. Menciones por etapa: M01 35, M02 10, M03 28, M04 38, M05 38, M06 100, M07 23, M08 57 |
| Nombres de estado/artefacto | — | `ddd-state-<run>-M03`, `-M03U`, `-M06`, `-M08`; en R2 `ddd-minimo-<run>-M06` (173) y `-M08` (173), `ddd-state-<run>-M08` (10), `-M06` (2). Otros `ddd-*` (audit, publication, full-run…) no llevan Mxx |
| Claves R2 | — | `orchestracion/archivo_r2.json`: **720** objetos `<territorio>/<run>/<artefacto>.zip`; **358** claves llevan Mxx (`ddd-minimo-…-M06/M08`, `ddd-state-…`). `almacen_m06_r2.json`: prefijo `arc-p/m06/` y `m06/m08…`, **0** objetos indexados hoy (T-302 sin lanzar). Prefijos `arc-e`/`arc-p`: sin Mxx |
| `orchestracion/*.json` | 8 de 16 con patrón | `publicaciones_visor.json`: 339 productos, `kind` `canonical_m06` 174 / `canonical_m08` 163 (+3 ensemble, 2 static); `catalogo_procedencia.json` 71 territorios, 12 entradas; `checkpoints_fase1.json`, `estado_tareas.json`, `estado_operativo*.json` |
| `configuracion/` y `schemas/` | 49 + 3 | `m04_engine.json`, `politica_*_2025.yaml`, `controles_obligatorios.yaml`, `puertas_f10.v1.json`, `verificacion_independiente_m03_m06.json`, `ensemble/*.json` (37), `catalogo_preparacion.yaml`; schemas `m06-district-catalog`, `territory-production-contract`, `g10-plan-lote` |
| Docs | ~700 | `docs/ESTUDIOS` 361, `registro` 140 (histórico), `AUDITORIAS` 62, `SALIDAS_CHATGPT` 57, `ARQUITECTURA` 14, `RONDAS` 12, `MODULOS` 10 (9 con versión activa, R015), `EJECUCIONES` 9, `ORQUESTACION` 6; `.claude` 16 (reglas, skills) |
| Visor y público | ~17 | `visor/` 7 (`app.js`, `escenarios.js`, v2), `documentacion_publica` 6, `publicado/` 2, `dashboard/` 2 (generado) |
| `territorios/*` (122 carpetas) | **1.186** | `evidencia` 922 (`generaciones_m06/<run>.json` 241, ejecuciones), `config` 174, `resultados` 79 (`resultados/ejecuciones/gh-<run>/M03…M08/` y ficheros `m0x_*`), `docs` 4 |
| `datos/`, `resultados/`, `datos_abiertos/` | 77 / 20 / — | M08 ligero publicado, composiciones (M06) |
| `evals/` | 23 | |

Nombres de fichero de producto más repetidos (conteo de apariciones en código/config/territorios): `m01_secciones_poblacion` 951, `m03_grafo` 728, `m05_distritos_optimizados` 496, `m04_semillas` 490, `m02_adyacencias` 352, `m06_contiguedad_geometrica` 243, `m06_distritos`/`m06_secciones`/`m06_composicion_distritos`/`m06_catalogo_distritos`.

**Huellas y gobernanza.** Huella M05 = cierre de imports `ddd_core` desde `modulos/05_optimizar_distritos.py` (`herramientas/huella_checkpoint_m05.py`, `huella_checkpoint_motor.py`, `seleccionar_checkpoint_productivo.py`, `ddd_motor2/produccion.py`, `_reutilizable-generacion-territorial.yml`, `documentacion_publica/evidencias/source-index.json`; tests `test_huella_m05_motor_activo`, `test_checkpoint_productivo_selector`, `test_motor2_semilla`). `modulos/04_generar_semillas.py` entra en la evidencia pre-M04 de los contratos `physical_components`. N08: `docs/ESTUDIOS/N08_*`, `verificar_evidencia_n08_readonly.py`, `test_preflight_caceres_n08.py` fijan hashes de ficheros activos. R015 (`test_r015_invariantes.py`, 9 refs a `modulos/0X_*`; cabeceras VERSIÓN/ANTERIOR y copia en `legacy/`) y R016 (`test_r016_evidencia_publicada.py`, `test_r016_refinamiento.py`). Renombrar un fichero con VERSIÓN exige copia legacy + ANTERIOR por cada uno (8 módulos + `docs/MODULOS/M0x_*` 9 + herramientas Mxx 29 + ddd_core Mxx 16 + tests Mxx 52 = ~114 renombrados).

**Histórico vs. cadena nueva**
- Histórico (se lee por alias, no se reescribe): `legacy/` (1.640), `docs/registro`, `docs/ESTUDIOS`, `AUDITORIAS`, `SALIDAS_CHATGPT`, `tests/fixtures`, `tests/legacy`, `territorios/*/evidencia` (922), `territorios/*/resultados/ejecuciones`, `datos/`, `resultados/`, `publicado/`, `evals/`, `orchestracion/archivo_r2.json` (claves de objetos ya subidos), productos publicados (`canonical_m06/m08`, blobs).
- Cadena de producción nueva (se migra): `modulos/`, `ddd_core`, `ddd_motor2`, workflows (jobs, inputs, nombres de artefacto), `herramientas/`, `configuracion/` y `schemas/`, tests vivos, `docs/MODULOS`, `visor/` y `documentacion_publica`, `.claude/rules`, claves R2 de las 71 regeneradas.

## 3. Riesgos

1. **Checkpoints (D-82 y huellas).** Renombrar `modulos/05_*` o cualquier `ddd_core` del cierre cambia `engine_files` → invalida los M05/M06 previos; `modulos/04_*` invalida la evidencia pre-M04 de los contratos `physical_components` (Canarias, Baleares, Las Palmas, S. C. Tenerife). Cambiar los nombres de `ddd-state-<run>-M0x` rompe la selección de checkpoint (`produccion-distritos.yml` baja M06→M05→M04→M03 por nombre). Pasos de la 00 posteriores: «Generar desde fuente territorial acreditada» o «Ejecutar desde el principio»; «Reutilizar» restaura nombres viejos. Por eso el corte va tras confirmar la P50 de las 71 y antes de 5.0.0.
2. **R2.** Las claves ya subidas (720; 358 con Mxx) no se renombran en R2: se necesita lector con alias (nombre viejo → fase) o duplicar. Proponer alias solo en lectura; las claves nuevas (71 regeneradas) ya nacen con P2x. `almacen_m06_r2.json` está vacío: se puede definir con la notación nueva antes de que el Operador archive (coste cero).
3. **Artefactos de Actions** caducan a 14 días: un `ddd-state-…-M06` en vuelo no lo encontrará un workflow nuevo; no migrar con runs abiertos.
4. **Tests de diseño que fijan nombres**: 76 tests citan `modulos/0X_*`; R015/R016, huellas, N08, `test_workflows_principales_ligeros`, `test_workflow_safety`, `test_workflow_interfaz_institucional`, `test_pre_m04_evidence_pipeline`, `test_preflight_caceres_n08`, `test_r039_electoral_contract`. Fixtures congelados (204) deben seguir con nombres viejos.
5. **Visor y registro de publicaciones**: `kind=canonical_m06/m08` (337 entradas) es clave de lectura del visor y del registro; cambiarla en vez de aliasarla rompe el visor (T-125).
6. **Datos y esquemas**: nombres de columna/ficheros `m0x_*` en `territorios/*/resultados` y `datos_abiertos/INDEX.json` (sha256 de 49 GeoJSON M06) y `schemas/m06-district-catalog`; si cambian, cambian sha y contratos de consumidores externos.
7. **Colisión P25/P50** en búsquedas (ambigüedad 4) y M02 ↔ P22 (ambigüedad 1).
8. **Conflictos entre PRs**: workflows y `herramientas/` son compartidos; una sola PR grande choca con cualquier PR abierta (T-220 tuvo que sustituir a #740 por #747).

**T-220 como modelo (#747, `b5bd69e`)**: una PR con 2.733 ficheros. Cómo: (a) tabla maestra `configuracion/notacion_territorial.csv` (sha256 literal anclado en el test) y `configuracion/equivalencias_territorios.csv` (viejo→nuevo); (b) `ddd_core/territorio_ids.py` con `resolver_id` para leer ids viejos; (c) renombrado de carpetas y sustitución en código vivo; (d) guardián `tests/test_t220_renombrado.py`: recorre `git ls-files` (en CI no hay otro modo) y falla si queda un id viejo vivo fuera de la lista `EXENTOS` (legacy, docs, fixtures, orchestracion, datos, resultados, publicado, evals… más tests de regresión sobre raíz congelada `tests/_raiz_congelada.py`), con tokenización de Python para no marcar comentarios/strings históricos; (e) `tests/test_t220_huella_puentes_shell.py` para puentes shell; (f) test de la tabla (`test_notacion_territorial`, `test_resolver_territorio`). **Reutilizable**: la mecánica completa (tabla maestra con sha, resolvedor de alias, guardián con lista EXENTOS y recorrido `git ls-files`, la raíz congelada para tests históricos). Cambia el objeto: ids de módulos en lugar de ids de territorio, más nombres de job/artefacto/clave R2 que T-220 no tenía.

## 4. Propuesta de orden en UNA PR y estimación

Ensayo local previo (`.claude/rules/diagnostico-local.md`) de 1 territorio completo P21→P26 y P40 con contrato temporal, comparando salidas bit a bit con la referencia anterior (el contenido no debe cambiar, solo nombres).

Orden:
1. **Tabla maestra** `configuracion/notacion_fases.csv` (M0x ↔ P2x/P40, nombre de módulo, de job, de estado, de clave R2, de `kind`) con sha en un test + `ddd_core/fases_ids.py` con `resolver_fase` (alias viejo→nuevo). Decidir ambigüedades 1-5 aquí. (~4 ficheros)
2. **Guardián** `tests/test_t313_fases.py` copiando el de T-220 (lista EXENTOS: legacy, docs históricos, fixtures, `archivo_r2.json`, evidencia y resultados de `territorios/*`, `publicado`, `datos`). Debe fallar antes de migrar (rojo→verde). (~2)
3. **Renombrado de módulos y paquetes** (`modulos/0X_*`, `ddd_core/m0x_*`, herramientas y tests Mxx) con copia en `legacy/`, VERSIÓN/ANTERIOR y `docs/MODULOS`; ajustar huellas M05, N08 (montar copia archivada), R015/R016. (~114 renombrados + ~100 con referencias)
4. **Workflows** (jobs, inputs, nombres de artefacto con lectura de ambos nombres hasta agotar los 14 días, `produccion-distritos` selector por alias); versionar cada workflow. (~17)
5. **Contratos y configuración** YAML/JSON/schemas con claves nuevas y aliases. (~50)
6. **Catálogo, registro de publicaciones y visor**: aceptar `canonical_m06/m08` y claves nuevas; `almacen_m06_r2` nace con la notación nueva. (~15)
7. **Docs vivos** (`ARQUITECTURA`, `MODULOS`, `.claude/rules`, skills, `PLAN`/registro por el planificador). No se reescriben registro, estudios ni evidencia. (~40)
8. Ensayo local de 1 territorio, suite completa, guardián en `main`; la CI en verde en la PR y en `main`; PR `no-automerge`; luego 00 «Ejecutar desde el principio» para las 71.

**Estimación**: ~2.760 ficheros vivos contienen el patrón, pero solo ~**350–450** se modifican (≈114 renombrados, ~100 código/tests, 17 workflows, ~50 config/schemas, ~40 docs vivos, ~15 visor/catálogo); más ~114 copias en `legacy/`. Territorios/evidencia/fixtures/legacy: 0 cambios (alias). Marcado como PR grande: decisión del propietario sobre congelar el resto de PRs de workflows/herramientas durante la migración (coordinación D-18).
