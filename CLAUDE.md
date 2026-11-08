# Diputado de Distrito — memoria de sesiones

Claude Code lee este archivo al abrir cada sesión. Al cerrar una sesión, invoca `/cierre-sesion` para añadir
lo aprendido. Solo lecciones que hayan costado tiempo descubrir; nada que se deduzca leyendo el código.
Máximo 100 líneas: lo que solo aplica a ciertos ficheros va en `.claude/rules/` (se carga al tocarlos).

## Reglas del propietario
- Mínimo consumo de créditos en cada ejecución, prompt y chat. Camino crítico; sin desvíos (p. ej. F10) salvo que se pida.
- Topónimos solo en español (Mahón, Ciudadela, Ibiza, Vizcaya, Guipúzcoa, Alicante, Castellón…), nunca en otras lenguas.
- No lanzar ejecuciones productivas ni publicar (visor, releases) sin permiso explícito en ese mensaje.
- Sin vigilantes ni revisiones programadas salvo que se pidan.
- Objetivo (08-11): un motor repetible (se ejecutará miles de veces, con el Gestor), no conservar resultados antiguos: relanza y regenera si hace falta.
- Respuestas cortas, en español. D-18: sin estudios, difusión, estado operativo ni propuestas de contenido por iniciativa propia: solo criterio técnico y opciones.
- No fusionar ninguna PR hasta ver la CI en verde en la PR y en `main`.

## Mapa
- Plan y cola de tareas: `docs/PLAN.md` (solo lo edita el planificador). Arquitectura de agentes y fases P00-P60:
  `docs/ARQUITECTURA/FRAMEWORK_AGENTES_Y_ESTRUCTURA.md`. Historia: `docs/REGISTRO_DE_CAMBIOS.md`.
- `.claude/rules/`: `gobernanza` (VERSIÓN + legacy), `registro`, `huellas` (M05/N08), `workflows`, `contratos`
  (política, población, provincias), `diagnostico-local` (motor en local).
- `.claude/hooks/guardia_git.py`: bloquea `git commit` con marcas de conflicto y `git push` forzado.
- `.claude/skills/`: `cierre-sesion` y las de rol.

## Coordinación entre sesiones
- Suele haber varias sesiones en paralelo con territorios repartidos. Antes de tocar ficheros compartidos
  (workflows, catálogo, política, `herramientas/`, `modulos/`, `ddd_core/`), avisa a la otra sesión y pregunta.
- Registro: cada PR deja su entrada en `docs/registro/AAAA-MM-DD_<rama>.md`, sin número; no se edita
  `docs/REGISTRO_DE_CAMBIOS.md` (lo numera el job «Numeración del Registro» al fusionar).
- Si `main` está en rojo, comprueba si el fallo es tuyo (ejecuta los tests en `origin/main`) antes de tocar nada.
- Un solo chat operador lanza. Tras un fallo, no relanzar: informar de la causa.
- Delegación (propietario, 07-11): el propietario delega el qué en el planificador («DDD Plan»); sus órdenes de
  tarea, prioridad y turno valen como del propietario. Solo lanzar ejecuciones y publicar exigen permiso del
  propietario en el chat que ejecuta. Fusiona el Operador (o el auto-merge) con `pruebas` en verde.
- Entre sesiones solo llega `send_message` del MCP `claude-code-remote` (con `session_id`); `SendMessage` por nombre no.
- Roles: propietario (permisos, decisiones) → planificador (qué, por olas) → Coordinador (recibe cierres, PR/CI, tablero
  `docs/ESTADO.md`, lecciones) → Operador (único que lanza/publica) → implementadores (una tarea, una PR).
- El control de seguridad bloquea ediciones que amplían la autoridad de otra sesión y mecanismos de fusión sin
  revisión, aunque los pida el planificador: exige la autorización del propietario en el chat que ejecuta.
- Datos oficiales nunca de memoria: de un fichero con fuente y sha256 (una tabla a mano dio Badajoz 6 y no 5).

## Ejecución 00 (`ejecucion-completa-proyecto.yml`)
- «Reutilizar progreso existente» reutiliza checkpoints M04 aunque haya cambiado el contrato. Tras cambiar umbrales,
  motor o fuente, usa «Generar desde fuente territorial acreditada» o «Ejecutar desde el principio».
- Si cambia el producto territorial (M06), el par electoral queda incompatible (`TERRITORIAL_READY_PAIR_INCOMPATIBLE`):
  1. si el paquete electoral ha caducado → `preparacion-resultados-electorales.yml` con reutilizar=false;
  2. `preparacion-legislatura-vigente.yml` `prepare_one` del territorio;
  3. 00 en «Reutilizar progreso existente» (hace 03/04).
- Los artefactos de Actions caducan; un producto viejo puede ser válido en el catálogo y no descargable.
- «Reutilizar» no ejecuta 02/04 ni archivo R2 y re-registra receipts de runs fallidos: para 04+R2 usa «Generar desde fuente»; verifica 04 y R2 antes de publicar. Restaura el último checkpoint REGISTRADO: si el run bueno no llegó a registrar (fallo de push), toma uno
  anterior (Murcia volvió al M03 en 3035, `CHECKPOINT_RUN_ID` en el log del paso M04). Mira ese valor antes de concluir.
- La 00 encadena sola par (`prepare_one`) y otra 00 como github-actions[bot] si la 04 se salta por falta de par;
  desde #389 solo si la puerta 02 pasó.
- Desde la 1.6.0 el run-name de la 00 lleva el territorio; en runs antiguos, `territorios/*/evidencia/ejecuciones_completas/<run>.json`
  o `TERRITORY:` de «Planificar». `/timing` da 0 min facturables (repo público): usa la duración de los jobs. La API
  resetea conexiones en lotes largos: reintentos y caché.
- Identifica cada run por su territorio (`TERRITORY:` en el log del job «Planificar»), nunca por el orden: toda 00 que
  llega a M06 encadena sola «Activación de Legislatura» y otra 00 «Reutilizar» como `github-actions[bot]`, y se cuelan.

## Visor y dashboard
- El visor solo muestra lo que está en `orchestracion/publicaciones_visor.json`. Publica con
  `production_run_id=<run 00 completo>` por cada territorio nuevo; con el campo vacío solo entra `latest_validated`.
- Los M08 publicados están en git como blobs: `publicaciones_visor.json` (`kind=canonical_m08`, run más reciente) →
  `gh api repos/<r>/git/blobs/<blob_sha> -H "Accept: application/vnd.github.raw"` (ZIP; comprobar el sha256).
  Solo traen el ganador por distrito (no votos por partido); versión ligera en `datos/resultados/` (#445).
  El M06 de los artefactos caduca (14 días): la extracción T-67 recuperó 16/63 composiciones; el resto, regenerar con 00.
- El dashboard (`herramientas/generar_estado_operativo.py`) acepta un M08 de otro run si el manifiesto de ese run
  acredita la 02 con el M06 vigente y la 04 en success (#354).

## Sesión cloud, Mac del propietario y lanzamientos
- En la sesión cloud `gh workflow run` falla (GraphQL bloqueado): lanza con REST,
  `gh api -X POST repos/<r>/actions/workflows/<f>.yml/dispatches -f ref=main -f "inputs[k]=v"`.
- Tras un rebase, la rama remota diverge y el reset/force push se deniega: fusiona `origin/main` o usa `git revert`.
- Los procesos en segundo plano (nohup/setsid) mueren al terminar el turno. Las cadenas largas
  (00 → legislatura → 00 electoral) las encadena la propia 00: `territorial_only` con `cadena_electoral=true`
  (#448; sin duplicados, estado en `chain` del manifiesto, el eslabón electoral no publica). Ya no hace falta el Mac.
- Errores de un run sin descargar logs: `gh api repos/<r>/check-runs/<job_id>/annotations`. Si hace falta el log,
  pide `gh run view <id> --log-failed | grep -E "::error|Traceback|Error"` (con `tail` solo sale la limpieza).
  Los logs de jobs se leen con la herramienta MCP `get_job_logs`; los grandes se guardan en fichero y se filtran.
- Mac (zsh): nunca uses `path` como variable (es `PATH`); los scripts van a un fichero (`pbpaste > f.sh`), no
  pegados (`!` da «event not found»); `gh` está en `~/.local/bin`; sin rutas con `<…>` ni globs sin coincidencia.
- Interior (Infoelectoral) rechaza runners y sesión cloud: el ZIP nacional por mesa está en el release
  `fuente-infoelectoral-02202307` y la 03 lo usa como espejo con la misma huella. Desde la nube se baja con
  `gh api repos/<r>/releases/assets/<id> -H "Accept: application/octet-stream"` (`gh release download` usa GraphQL).
- Los 49 GeoJSON M06 (~50 MB) no se versionan: el publicador los baja del blob y verifica el sha256 contra
  `datos_abiertos/INDEX.json` (necesita GH_TOKEN). `gh api repos/<r>/actions/jobs/<id>/logs` funciona desde la nube
  (los artefactos no); sus marcas de tiempo dan la duración por test.
- Escaños 2019-11: BOE-A-2019-18147 (la corrección; BOE-A-2019-17344 solo remite a los cuadros). El XML de 2019 difiere
  del de 2023: siglas en fila 1, datos desde fila 3, pares Votos/Escaños; siglas tal cual, homologación en HOMOLOGACION_2019.
- Escaños oficiales 2023: BOE-A-2023-18907 en `configuracion/resultados_oficiales_congreso_2023.csv`; la red del
  entorno Default permite `boe.es`.

## Historial de lecciones
- 2026-10-29/31 · Murcia/Valencia (M04 7.4.15–18, exención Beniel) y Congreso (piloto Huesca, 50 provincias, espejo Infoelectoral) · #324–#371.
- 2026-11-01 · T-02: CRS 25830, M04 7.6.0 multisección, dedupe de manifiesto, encadenado con puerta 02 · #374 #383 #387 #389.
- 2026-11-01 · Bloqueos de población: exención municipal en contrato, techo en política, reparación inútil si estructural · #380 #384 #391.
- 2026-11-02 · Activación por elección, Gestor con provincias, robots con app propia, exención en islas · #376–#398.
- 2026-11-07 · Paso 1 de agentes: CLAUDE.md < 100 líneas, `.claude/rules/` por rutas y hooks de git · #427 #428.
- 2026-11-07 · Agentes en uso, registro por ficheros, CI en 4 min, archivista R2, huella de checkpoint, cadenas sin Mac · #441–#448.
- 2026-11-08 · Ola 2 y 3: ensembles, archivista D-17, siglas D-20, Gestor 2.0, huella M05 calculada, M05 7.4.3, congreso_350 · #500–#547. Detalle en `.claude/rules/`.
- 2026-11-08 (noche) · Relevo de chats, ids solo del Planificador, tests sobre estado vivo, T-90b/T-109/T-113 · #549–#555. Detalle en `.claude/rules/`.
