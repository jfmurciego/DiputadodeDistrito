# Diputado de Distrito — memoria de sesiones

Claude Code lee este archivo al abrir cada sesión. Al cerrar una sesión, invoca `/cierre-sesion` para añadir
aquí lo aprendido. Solo lecciones que hayan costado tiempo descubrir; nada que se deduzca leyendo el código.

## Reglas del propietario
- Mínimo consumo de créditos en cada ejecución, prompt y chat. Camino crítico; sin desvíos (p. ej. F10) salvo que se pida.
- Topónimos solo en español (Mahón, Ciudadela, Ibiza, Vizcaya, Guipúzcoa, Alicante, Castellón…), nunca en otras lenguas.
- No lanzar ejecuciones productivas ni publicar (visor, releases) sin permiso explícito en ese mensaje.
- Sin vigilantes ni revisiones programadas salvo que se pidan.
- Respuestas cortas, en español.
- No fusionar ninguna PR hasta ver la CI en verde en la PR y en `main`.

## Coordinación entre sesiones
- Suele haber varias sesiones en paralelo con territorios repartidos. Antes de tocar ficheros compartidos
  (workflows, catálogo, política, `herramientas/`, `modulos/`, `ddd_core/`), avisa a la otra sesión y pregunta.
- `docs/REGISTRO_DE_CAMBIOS.md` lo numera quien abra la PR; pregunta el último número antes de añadir entradas.
- Si `main` está en rojo, comprueba si el fallo es tuyo (ejecuta los tests en `origin/main`) antes de tocar nada.

## Ejecución 00 (`ejecucion-completa-proyecto.yml`)
- «Reutilizar progreso existente» reutiliza checkpoints M04 aunque haya cambiado el contrato. Tras cambiar umbrales,
  motor o fuente, usa «Generar desde fuente territorial acreditada» o «Ejecutar desde el principio».
- Si cambia el producto territorial (M06), el par electoral queda incompatible (`TERRITORIAL_READY_PAIR_INCOMPATIBLE`):
  1. si el paquete electoral ha caducado → `preparacion-resultados-electorales.yml` con reutilizar=false;
  2. `preparacion-legislatura-vigente.yml` `prepare_one` del territorio;
  3. 00 en «Reutilizar progreso existente» (hace 03/04).
- `TERRITORIAL_REPLAN_BLOCK: fuente elegida difiere del catálogo`: la fila del catálogo apunta a un receipt antiguo
  (`territorial_source_declaration` / `independent_source_evidence`); alinéala con `preparation_evidence` (#338, #352).
- Los artefactos de Actions caducan; un producto viejo puede ser válido en el catálogo y no descargable.
- «Reutilizar» restaura el último checkpoint REGISTRADO: si el run bueno no llegó a registrar (fallo de push), toma uno
  anterior (Murcia volvió al M03 en 3035, `CHECKPOINT_RUN_ID` en el log del paso M04). Mira ese valor antes de concluir.
- La 00 encadena sola par (`prepare_one`) y otra 00 como github-actions[bot] si la 04 se salta por falta de par;
  desde #389 solo si la puerta 02 pasó.

## Ficheros con efectos ocultos
- `modulos/05_optimizar_distritos.py` está en la huella M05 (`huella_checkpoint_m05.ENGINE_FILES`): tocarlo
  invalida los M06 previos para la 04 (lo resolvió #346 con `--consume-certified-product`).
- La imagen Docker de CI excluye `legacy/` salvo lo declarado en `.dockerignore`. Si un test lee una copia de
  `legacy/`, añádela allí o el test no debe depender de ella.
- Los documentos `docs/MODULOS/*.md` declaran la versión activa del código (test de gobernanza R015).
- Las evidencias N08 (`docs/ESTUDIOS/N08_*`) fijan hashes de ficheros activos; si cambias uno, monta la copia
  archivada en `herramientas/verificar_evidencia_n08_readonly.py` y en `tests/test_preflight_caceres_n08.py`.
- Gobernanza: cada cambio de fichero versionado sube su cabecera VERSIÓN y deja copia en `legacy/` con ANTERIOR.
- `modulos/04_generar_semillas.py` entra en la evidencia pre-M04 de los contratos `physical_components` (Canarias,
  Baleares, Las Palmas, Santa Cruz de Tenerife): cambiarlo los obliga a «Generar desde fuente territorial acreditada».

## Contratos, política y población
- El materializador sobrescribe en el contrato los umbrales con los de la política: cualquier ajuste por territorio
  va en `configuracion/politica_generacion_territorial_2025.yaml` (`population_limits`, `structural_floor_exemptions`),
  no solo en el contrato.
- Exenciones de suelo: por partición (isla/provincia, `population_floor_exempt_partitions`) o por municipio
  (`population_floor_exempt_municipalities`, código INE de 5 cifras; Beniel en Murcia).
- Bloqueo por población: suele ser estructural (municipios indivisibles o núcleos cerrados que encajonan distritos
  pequeños). Palancas: `municipality_atomicity_limit_ratio` más bajo, `population_repair` (private_annealing),
  exención de suelo. Más presupuesto de reparación no ayuda si es estructural.
- CRS de M02 en provincias del Congreso: el generador pone EPSG:3035; donde el autonómico usa 25830 (Comunidad
  Valenciana, Región de Murcia) cópialo. En 3035 los solapes INE crecen (0,19 → 11,8 m²) y fallan la admisibilidad
  de 01 (`GEOMETRY_INVALID_AUDITED`) o la conectividad pre-M04 (#374, #383). Los parámetros de M02 viven en el
  contrato; la política solo sobrescribe población; `population_repair` va en `modulo_05` del contrato.
- Estructural sin palanca de contrato: municipio atómico rodeado de municipios que solo lindan con él (Lorca+Águilas+
  Puerto Lumbreras) o enclaves dentro de un municipio con núcleos cerrados (Alcantarilla y Beniel en Murcia).
  Comprueba vecinos municipales en el grafo M03 antes de proponer ajustes.
- La exención municipal va en `validation` del contrato (el materializador no la toca) y la valida el motor; el techo por
  territorio, en la política (`population_cap_ratio` y `target_tolerance_ratio` = techo−1; la atomicidad no puede pasarlo).
  `population_repair` (profundidad 6, conjunto 3, 500.000 candidatos) no mejoró ningún exceso estructural el 01-11.
- En el informe M05, `population_status_by_district` es un dict y `final_hard_population_violations` cuenta también los
  distritos exentos: mira los no-PASS, no ese contador.

## Diagnóstico local (sin descargar artefactos: desde la sesión cloud dan 403)
- El propietario sube con un script desde su Mac el grafo M03 y el M01 del run a la rama `diagnostico/poblacion-20261028`.
- Copia ambos a `territorios/<t>/.cache/ddd/preparacion/<t>_2025/` y ejecuta el motor real:
  `python -m ddd_core.m04_seed_engine --params territorios/<t>/config/<t>_2025.yaml` y
  `python modulos/05_optimizar_distritos.py --params …`. Las rutas se resuelven respecto al contrato: las copias
  temporales del contrato van en `territorios/<t>/config/`, nunca fuera.
- Antes de gastar una 00, prueba el cambio en local (M04+M05 tardan ~15 s) con el contrato temporal: el volcado de la
  rama `diagnostico/t02-20261101` trae M01 y M03 grafo, pero no `*_m03_particiones*` (las islas no corren).
- `ddd-audit-<run>` (KB) trae `block_causes.json`; el informe M05 está en `ddd-state-<run>-M05` (~80 MB).
- Pytest no viene instalado: `pip install -r requirements.lock pytest==8.4.2`. La suite entera pasa de 10 min; la CI usa
  `unittest` por módulos, y en local basta con los ficheros de materialización, política, gobernanza y contratos.
- Los logs de jobs se leen con la herramienta MCP `get_job_logs`; los grandes se guardan en fichero y se filtran.
- Para T-02 y siguientes: `lanzadores/subir_diagnostico_t02.sh` (rama `lanzadores-mac`) sube M01+M03 a
  `diagnostico/<rama>`; acepta `ddd-state-<run>-M03` o `-M03U` y reintenta pushes (HTTP 408 desde el Mac).
- Suite completa local ~15 min: en segundo plano. `test_pipeline_adversarial_c07` y `test_pipeline_sintetico_m01_m06`
  fallan en local también en `main` (entorno); en CI pasan.

## Visor y dashboard
- El visor solo muestra lo que está en `orchestracion/publicaciones_visor.json`. Publica con
  `production_run_id=<run 00 completo>` por cada territorio nuevo; con el campo vacío solo entra `latest_validated`.
- El dashboard (`herramientas/generar_estado_operativo.py`) acepta un M08 de otro run si el manifiesto de ese run
  acredita la 02 con el M06 vigente y la 04 en success (#354).

## Sesión cloud, Mac del propietario y lanzamientos
- En la sesión cloud `gh workflow run` falla (GraphQL bloqueado): lanza con REST,
  `gh api -X POST repos/<r>/actions/workflows/<f>.yml/dispatches -f ref=main -f "inputs[k]=v"`.
- Identifica cada run por su territorio (`TERRITORY:` en el log del job «Planificar»), nunca por el orden: toda 00 que
  llega a M06 encadena sola «Activación de Legislatura» y otra 00 «Reutilizar» como `github-actions[bot]`, y se cuelan.
- Tras un rebase, la rama remota diverge y el reset/force push se deniega: fusiona `origin/main` o usa `git revert`.
- Los procesos en segundo plano (nohup/setsid) mueren al terminar el turno. Las cadenas largas
  (00 → legislatura → 00 electoral) corren en el Mac del propietario: script en la rama `lanzadores-mac`,
  descargado con `gh api ".../contents/<ruta>?ref=lanzadores-mac" -H "Accept: application/vnd.github.raw"`.
- Errores de un run sin descargar logs: `gh api repos/<r>/check-runs/<job_id>/annotations`. Si hace falta el log,
  pide `gh run view <id> --log-failed | grep -E "::error|Traceback|Error"` (con `tail` solo sale la limpieza).
- Mac (zsh): nunca uses `path` como variable (es `PATH`); los scripts van a un fichero (`pbpaste > f.sh`), no
  pegados (`!` da «event not found»); `gh` está en `~/.local/bin`; sin rutas con `<…>` ni globs sin coincidencia.
- Interior (Infoelectoral) rechaza runners y sesión cloud: el ZIP nacional por mesa está en el release
  `fuente-infoelectoral-02202307` y la 03 lo usa como espejo con la misma huella.
- Los robots de registro reescriben `catalogo_preparacion.yaml` y el catálogo maestro mientras corren
  ejecuciones: una PR que los toca choca enseguida. Rebasa tomando `main` y reinserta solo lo tuyo; fusiona rápido.
- Un ruleset que exige PR en `main` rechaza los registros de los robots (`GH013`) y las 00 fallan al registrar;
  `Duplicate header: "Authorization"` (HTTP 400) = credencial de registro mal combinada con actions/checkout (#381→#386).

## Congreso / nacional (provincias)
- `herramientas/generar_provincias_congreso.py` (idempotente) da de alta provincias desde el reparto N06 y hereda
  los puentes de enclaves de los contratos autonómicos: sin ellos el pre-M04 falla con «grafo territorial no
  supera conectividad administrativa» (Palencia, #371).
- Islas: componentes agrupadas y `bridges` en `particiones_insulares_2025.json`; inventario 2023 sacado del ZIP de
  Interior (coincide en hash con el INE 2023); `component_districts` en la política fija el reparto (#369 #370).
- Ámbitos sin CODAUTO usan `pilot_code` (C+CPRO) para ordenar en dashboard y visor (#367).

## Historial de lecciones
<!-- /cierre-sesion añade aquí una línea por lección nueva: fecha · lección · PR o run de evidencia. -->
- 2026-10-29 · Murcia/Valencia: M04 7.4.15–7.4.18 (reintentos solo en la ruta de agotamiento), exención de Beniel, umbral 1,5 en Valencia · #324 #327 #332 #343 #336 #345 #352 #354.
- 2026-10-31 · Congreso: piloto Huesca 01→05, 50 provincias generadas, islas agrupadas, puentes heredados, Infoelectoral por espejo, lanzamientos REST/Mac · #362 #363 #364 #367 #368 #369 #370 #371.
- 2026-11-01 · T-02: CRS 25830 (Huelva, Valencia), M04 7.6.0 multisección (Álava), dedupe de manifiesto al reanudar
  desde M05, encadenado solo con puerta 02, PARADA de visor = marcador; Murcia bloqueada estructural · #374 #383 #387 #389.
- 2026-11-01 · Bloqueos de población de provincias: exención municipal en el contrato, techo por territorio en la política, reparación profunda inútil si es estructural, validación local y runs por territorio · #380 #384 #391.
