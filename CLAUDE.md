# Diputado de Distrito — memoria de sesiones

Claude Code lee este archivo al abrir cada sesión. Al cerrar una sesión, invoca `/cierre-sesion` para añadir
aquí lo aprendido. Solo lecciones que hayan costado tiempo descubrir; nada que se deduzca leyendo el código.

## Reglas del propietario
- Mínimo consumo de créditos en cada ejecución, prompt y chat. Camino crítico; sin desvíos (p. ej. F10) salvo que se pida.
- Topónimos solo en español (Mahón, Ciudadela, Ibiza, Vizcaya, Guipúzcoa, Alicante, Castellón…), nunca en otras lenguas.
- No lanzar ejecuciones productivas ni publicar (visor, releases) sin permiso explícito en ese mensaje.
- Sin vigilantes ni revisiones programadas salvo que se pidan.
- Respuestas cortas, en español.

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

## Ficheros con efectos ocultos
- `modulos/05_optimizar_distritos.py` está en la huella M05 (`huella_checkpoint_m05.ENGINE_FILES`): tocarlo
  invalida los M06 previos para la 04 (lo resolvió #346 con `--consume-certified-product`).
- La imagen Docker de CI excluye `legacy/` salvo lo declarado en `.dockerignore`. Si un test lee una copia de
  `legacy/`, añádela allí o el test no debe depender de ella.
- Los documentos `docs/MODULOS/*.md` declaran la versión activa del código (test de gobernanza R015).
- Las evidencias N08 (`docs/ESTUDIOS/N08_*`) fijan hashes de ficheros activos; si cambias uno, monta la copia
  archivada en `herramientas/verificar_evidencia_n08_readonly.py` y en `tests/test_preflight_caceres_n08.py`.
- Gobernanza: cada cambio de fichero versionado sube su cabecera VERSIÓN y deja copia en `legacy/` con ANTERIOR.

## Contratos, política y población
- El materializador sobrescribe en el contrato los umbrales con los de la política: cualquier ajuste por territorio
  va en `configuracion/politica_generacion_territorial_2025.yaml` (`population_limits`, `structural_floor_exemptions`),
  no solo en el contrato.
- Exenciones de suelo: por partición (isla/provincia, `population_floor_exempt_partitions`) o por municipio
  (`population_floor_exempt_municipalities`, código INE de 5 cifras; Beniel en Murcia).
- Bloqueo por población: suele ser estructural (municipios indivisibles o núcleos cerrados que encajonan distritos
  pequeños). Palancas: `municipality_atomicity_limit_ratio` más bajo, `population_repair` (private_annealing),
  exención de suelo. Más presupuesto de reparación no ayuda si es estructural.

## Diagnóstico local (sin descargar artefactos: desde la sesión cloud dan 403)
- El propietario sube con un script desde su Mac el grafo M03 y el M01 del run a la rama `diagnostico/poblacion-20261028`.
- Copia ambos a `territorios/<t>/.cache/ddd/preparacion/<t>_2025/` y ejecuta el motor real:
  `python -m ddd_core.m04_seed_engine --params territorios/<t>/config/<t>_2025.yaml` y
  `python modulos/05_optimizar_distritos.py --params …`. Las rutas se resuelven respecto al contrato: las copias
  temporales del contrato van en `territorios/<t>/config/`, nunca fuera.
- Los logs de jobs se leen con la herramienta MCP `get_job_logs`; los grandes se guardan en fichero y se filtran.

## Visor y dashboard
- El visor solo muestra lo que está en `orchestracion/publicaciones_visor.json`. Publica con
  `production_run_id=<run 00 completo>` por cada territorio nuevo; con el campo vacío solo entra `latest_validated`.
- El dashboard (`herramientas/generar_estado_operativo.py`) acepta un M08 de otro run si el manifiesto de ese run
  acredita la 02 con el M06 vigente y la 04 en success (#354).

## Historial de lecciones
<!-- /cierre-sesion añade aquí una línea por lección nueva: fecha · lección · PR o run de evidencia. -->
- 2026-10-29 · Murcia/Valencia: M04 7.4.15–7.4.18 (reintentos solo en la ruta de agotamiento), exención de Beniel, umbral 1,5 en Valencia · #324 #327 #332 #343 #336 #345 #352 #354.
