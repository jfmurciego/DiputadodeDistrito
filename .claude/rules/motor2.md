---
paths:
  - "ddd_motor2/**"
  - "herramientas/bateria_motor.py"
  - "herramientas/estado_produccion.py"
  - ".github/workflows/bateria-motor.yml"
  - ".github/workflows/_reutilizable-generacion-territorial.yml"
---

# Motor nuevo (motor2): batería, P30 y certificación (lecciones del 10-11)

- **Un criterio de aceptación cambia en la misma PR que añade un candidato**: T-217 añadió el vigente como candidato y el
  recuento 1+N quedó obsoleto (batería r4 rechazada solo por eso). Esperado = 1 + N (+1 exhaustivo) (+1 si el vigente
  compite según COMPETICION.json); el vigente que no compite va a «vigente_excluido» con motivo, fuera de `candidatos`.
- **Ante un «PEOR» de la aceptación**, compara la línea JSON de la competición del territorio (`gh api
  repos/<r>/actions/jobs/<id>/logs`: fuera_tolerancia, fuera_vigente_publicado, frente_al_vigente) con la tabla
  INDICADORES: si no cuadran, el fallo es de medida. Hay dos recuentos de fuera de tolerancia (objetivo regional del
  contrato y por provincia): toda comparación usa `Natural.fuera_regional`, el mismo que la clave D8.
- **Atomicidad**: el laboratorio parte municipios hasta 1×objetivo; el contrato hasta `municipality_atomicity_limit_ratio`×objetivo
  (1,75 en autonómicas) y M04 agrupa municipios grandes en unidades U. Comparar cifras exige la misma atomicidad.
- **Vigente publicado**: parte unidades M04 en municipios divisibles; solo es representable con las piezas finas del generador
  `vigente`. Los núcleos cerrados salen del M04 del canónico: un mapa de otro M04 puede incumplir R-NUCLEO sin ser malo
  (reparación mínima: Cataluña 3 secciones, Ávila 1 unidad). Un vigente de otro seccionado no compite ni siembra
  («vigente excluido: otro seccionado») y deja el territorio «sin vigente comparable» (T-224).
- **P30 = batería**: el P30 de la 00 y `competir_territorio` son la misma competición; un generador nuevo debe llegar a
  `produccion.generadores_por_defecto` (test de paridad). Todo dato que cambie el resultado (`datos/composicion/*.csv`)
  entra en la huella `motor2`. `competir` sale con 6 sin `PYTHONHASHSEED=0`.
- **Cambio de ganador entre dos pruebas con las mismas entradas**: antes de culpar al entorno, `git diff <a> <b> -- ddd_motor2`
  de los commits de cada prueba (La Rioja cambió por #694, no por GEOS ni la semilla).
- **Certificación con motor2** lee `<run>/p30_motor2/P30.json` (ganador), exige `violaciones_duras` y
  `composicion_m06_sha256`; un P30 de la 1.0.0 ya no certifica. Misma regla de contrato que con M05.
- **00 con P30**: un paso que reescribe la entrada de M06 rompe el linaje M05: guarda la salida M05 y restáurala byte a byte.
  Los pasos de módulo son un ancla YAML (`*module_steps`): condiciónalos con `env.STAGE == 'M0x' && inputs.…`.
  `tests/test_ejecucion_completa.py` fija la lista EXACTA de entradas de la 00 (toda entrada nueva lo rompe).
  Los ficheros que escribe docker son root: `sudo chown -R` antes de escribirlos desde Python.
- **Entorno de la batería**: instalar el lock del ensemble sube pandas/geopandas y rompe el canónico. Se instala solo
  gerrychain `--no-deps` + networkx/rustworkx/scipy/tqdm/six con pines del lock del laboratorio, y un paso falla si cambia
  el `pip freeze` base. En sesión limpia `requirements.lock` no instala gerrychain.
- **Reproducir en local** (barato): `bateria_motor.py entradas <t> [--seccionado shapefile]` (~2 min, rc≠0 si falla un
  territorio: no encadenar con `&&`) + `competir --cadenas 1` + `indicadores`. Madrid falla la adquisición en cloud.
  `test_t212_forma_con_la_m01_de_las_entradas` y R015 `M05Determinism` fallan en local sin geopandas (también en main).
- **Sesiones y PR**: crear chats de implementación con `source_url` del repo (sin él no hay repo y `add_repo` lo deniega el
  modo auto). El revisor en solo lectura no ejecuta Python: los tests los pasa quien implementa y lo declara. Tras un
  squash no se empujan más commits a esa PR; nueva PR. Cita el HEAD copiándolo de `git log` tras el push.
- **Renombres de workflows (corte 5.0.0)**: sin «·» en ningún `name:` de flujos con botón (separador « — »;
  `test_codauto_preparation_contract`). Renombrar la 00 toca además run-name, búsqueda de duplicados (`en_curso`),
  TITLE_00/poll del Gestor y RUN_NAME de métricas; aceptar el título viejo para runs en vuelo e históricos. Al fusionar main
  con PRs paralelas que suben VERSIÓN del mismo workflow: versión por encima y ANTERIOR a copia nueva de la de main.
  actionlint da 34 avisos preexistentes: compara contra main.
- **Congreso 2026**: el par INE 2025 está versionado (`inputs/partes`, MANIFEST_PARTES); no se vuelve a descargar. La guarda
  de 2023 del resolver no se amplía (D-80). Bloqueos con padrón 2025: Toledo (`modulos/01` decodifica estricta una muestra de
  4096 bytes y corta la «ó»), Las Palmas (Lanzarote + La Graciosa 1,424 > techo 1,40), Málaga (1,37), Madrid (resto de
  Leganés aislado). No se tocan `modulos/` en tareas de contratos.
- **Huella motor2 (11-12)**: no hashear ficheros que cambian con otras publicaciones (`publicaciones_visor.json` entero cambiaba la huella de todos los territorios al publicar uno): hashear solo lo resuelto por territorio (`produccion.huella_vigente(t)`, #734). Un único vigente (`ddd_motor2/vigente.py`) = el run publicado en el visor; sin composición versionada → SIN_VIGENTE, no bloquea (T-224).
- **Semilla D-90 (#731)**: sale del código oficial de la tabla maestra (`territorio_ids.codigo_semilla`, NACnn/AUTnn; fuera de tabla → ErrorContrato; `congreso350_*` fallaría). Es la nueva referencia «bit a bit» (cambian La Rioja del Congreso y La Rioja). Optimizaciones previas: cota de nodos del exhaustivo (#724), cadenas −30 % con el mismo RNG (#730), puentes con `zfill(10)` (#727), código muerto M04 v745–v754 y M05 v740 en `legacy/ddd_core/t263_codigo_muerto/` (#723; la huella M04 de los checkpoints cambia: 00 «Generar desde fuente»).
- **Excepciones del núcleo**: D-66 = máx. 1 distrito mixto por municipio; la excepción permite 2 en ESE municipio y 2 entradas por territorio (`validation.max_mixed_districts_exceptions`, #733: solo esquema y anotación; falla si se declara porque el núcleo aún no la aplica, T-269). Techo de población exento (T-235, #736): `validation.population_cap_exempt_partitions` solo con K=1 y decisión del propietario, función común `ddd_core/population_cap_exemptions.py` leída por M04, M05, M06, validador y motor2 (Las Palmas 2026: 35-G01 Lanzarote + La Graciosa). Pendiente: estrategia GerryChain opt-in y `diagnosticar_poblacion_m05.py` sin la exención.
- **Revisión**: el revisor da BLOCKED con CI pendiente y FAIL real ante lo que ejecutaría el código (huella inestable, comprobación que bloquea de más); pasar a «una revisión por PR» y reservar la segunda para el defecto bloqueante.
