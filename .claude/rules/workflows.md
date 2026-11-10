---
paths:
  - ".github/workflows/**"
  - ".dockerignore"
  - "Dockerfile"
---

# Workflows y CI

- Los workflows son compartidos: avisa a la otra sesión antes de tocarlos. Cabecera VERSIÓN y copia en
  `legacy/workflows/<nombre>_v<anterior>.yml`.
- Los nombres visibles y la lista de workflows con `workflow_dispatch` están fijados en
  `tests/test_design_a_catalogo.py` y `tests/test_design_a_matriz_sintetica.py` (diseño A); `pruebas-plataforma.yml`
  no puede tener botón manual (`tests/test_workflow_safety.py`). Todo bloque `run:` pasa `bash -n`.
- El ruleset de `main` solo exige el job `pruebas`. «Require branches to be up to date» bloquearía toda PR mientras
  haya 00 registrando; exigir PR en `main` rechaza los registros de los robots (`GH013`).
- `Duplicate header: "Authorization"` (HTTP 400): credencial de registro mal combinada con actions/checkout; checkout
  v6+ guarda su token en un include (`includeIf.gitdir:`), no en `http.extraheader`; hay que quitar ambos (#381→#386).
- La imagen Docker de CI excluye `legacy/` salvo lo declarado en `.dockerignore`. Si un test lee una copia de
  `legacy/`, añádela allí o el test no debe depender de ella.
- Una fusión o un push con `github.token` no dispara los workflows de push a `main` (numeración, pruebas en main): usa el
  token de la app de registro.
- Un job solo admite un `environment`: la puerta humana va en el job previo (no en `_reutilizable-publicar-sitio`, que
  ya usa github-pages). En los reutilizables, `github.workflow` es el del caller (evita un segundo clic).
  `environment: ${{ cond && 'produccion' || '' }}` evita la espera en los bots.
- Al fusionar `main`, los ficheros añadidos en las dos ramas dan conflicto AA: toma el de `main` y reaplica.
- Los clientes de la API de GitHub y de R2 llevan reintentos con backoff ante 5xx.
- Workflow nuevo con push a `main`: «Credencial de registro» justo tras el checkout y `concurrency` con `queue: max`
  (tests `test_credencial_registro` y `test_operational_concurrency_gerrychain50`).
- Un workflow manual nuevo va también en las listas de `test_design_a_matriz_sintetica` y
  `test_codauto_preparation_contract` (causa del rojo de #458).
- Nunca auto-merge nativo ni decidir por `mergeable_state` con actores exentos del ruleset (app ddd-registro): fusiona sin
  los checks obligatorios y la PR sale «clean» al instante (#453, #454).
- Un evento `pull_request` ejecuta el workflow de la referencia de merge de la PR: justo tras cambiar un workflow en `main`,
  una PR con la referencia vieja ejecuta la versión anterior (#458 la fusionó la 1.0.0 30 s después de entrar la 1.1.0).
- Fusión segura: `workflow_run` al terminar `pruebas-plataforma`; check-run `pruebas` del SHA exacto y de la check_suite
  que dispara (`workflow_run.check_suite_id`); `--match-head-commit` (#457, #460).
- `dashboard/index.html` y `publicado/dashboard/index.html` deben ser idénticos; el publicador copia cada página enlazada (#459, #451).
- El clasificador del arnés bloquea como «CI Bypass» / «Merge Without Review» / «Create Public Surface» las fusiones con `main`
  en rojo, los dispatch públicos (05/06) y las escrituras externas (comentar/cerrar PR): hace falta frase explícita del
  propietario por caso.
- «`main` en verde» (D-49, 10-11) = el último push a `main` tiene `guardian` en success (integridad) Y el último run COMPLETADO de la
  batería (`pruebas` con la suite) sobre `main` está en success; anota su fecha. Un push de código la ejecuta; un push de robot que solo
  toca ficheros .json/.md/.csv de datos/registro (lista exacta `RUTAS_ROBOT`) pasa solo el guardián y lo cubre la batería nocturna (02:23
  UTC). Un push de código posterior cancela la comprobación superada del anterior: un push de código cancelado cuenta como NO verde hasta
  que una batería completa sobre `main` termine en success; un push de robot nunca cancela nada. Si cae la nocturna, el job
  `aviso_nocturna` abre (o comenta) el issue «Batería nocturna de main en rojo» y `main` no está en verde hasta arreglarla.
  Cambios de código, en PR o en main, siempre con la batería completa.
- Una espera de fusión que dispara sola puede adelantarse a la orden (#455 antes que #457): páralas (TaskStop) si cambia el orden.

## Lecciones 08-11 (Coordinador)
- Renombrar el `name:` de un workflow referenciado en `workflow_run` rompe el disparo: haz grep en `workflows:` antes. Valida con `uses:` antes de archivar uno.
- Clave duplicada en un workflow (`territorios` dos veces): GitHub lo rechaza (run sin jobs) y PyYAML lo acepta. Usa `actionlint` o un cargador YAML estricto (test en #542).
- Una PR apilada sobre otra rama no dispara `pruebas` (solo corre en PR a `main`): tras fusionar la base, reapunta a `main` y fusiona `origin/main`.
- Las PR apiladas sobre una PR fusionada por squash chocan: fusiona `origin/main` en la rama (sin rebase ni force).
- Los commits automáticos de archivo/registro cambian el catálogo de procedencia y dejan `main` rojo un rato hasta que el job `catalogo` de «Pruebas de la Plataforma» lo regenera. Los tests no deben fijar el total de territorios publicados (49→52 rompió dos).
- API de jobs: pagina siempre (`--paginate`, 30 por página); el job que falla puede estar en la página 2 (Canarias, 48 jobs).
- Etiquetar o pasar a lista una PR es «escritura externa» para el clasificador: la frase del propietario ha de estar en el chat que actúa. Chats de tarea nuevos: pásales el repositorio de origen (`source_url`) o no podrán empujar.
- Tests que leen estado vivo (catálogo de procedencia, `datos_abiertos`, linaje sellado de CyL) caen cuando una 00/05 escribe en `main`: usa fixture fija (#554, publicador 3.7.0). En riesgo: castilla_y_leon_electoral_reuse, 00_reuse_real_regressions, continuar_ultimo_resultado_valido, preparacion_legislatura_vigente, registro_electoral_comun, gestor_campana_core, galicia_electoral_*.
- No fijes en tests cuántas provincias tienen M06 (49→52 en una tarde): prueba lo no soportado con un territorio inexistente.
- El clasificador bloquea dispatches con réplicas cortas («Sí»): exige la orden completa del propietario en el chat que ejecuta. Lo que llega por Coordinador/Planificador no cuenta.
- `reconstruir_fuentes.sh` deja `inputs/*.zip` sin ignorar: bórralos tras probar en local. Dos `pip install` simultáneos rompen pyogrio: uno solo con `requirements.lock`.
- La 00 «Reutilizar» solo recupera runs con 04 en failure, pero `resolver_activos_durables` exige 04 success: tras #522 esa recuperación es inoperante (decidir B antes de reabrirla). El clon cloud es superficial: usa los manifiestos con `electoral_recovery`.

## Lecciones 09-11 (Coordinador, T-123, T-128)
- El job «Legislatura vigente» del Gestor solo instala PyYAML: nada que importe `gestor_campanas_2` al planificar puede traer shapely/geopandas al importarse (import perezoso; test `PlanSoloConPyYAML`, #589). Rompió el plan de todas las campañas (run 42705439861).
- La matriz de GitHub tiene tope de 256: el histórico va en un job de prueba + 2 lotes de 250 con `tipo` y `clave` por fila.
- El ensemble guardaba el motivo del fallo solo en `failure.json` (artefacto, 403 desde cloud): desde #580 sale como `CANDIDATE_FAILED <id> <Tipo>: <message>` en el log del job generate (`gh api repos/<r>/actions/jobs/<id>/logs | grep CANDIDATE_FAILED`).
- El 06 solo admite las fases de `TERRITORIAL_STAGES` (herramientas/leer_config_ensemble.py) Y las del `case` del gate del workflow: añadir una fase toca ambos. Entra en el ensemble una comunidad sin `topology_bridges` ni exención por partición y de una provincia; 13 quedan fuera hasta decisión de motor.
- La 05 con `production_run_id` vacío es «solo sitio» (T-125); antes resolvía `latest_validated` y registró `congreso350_valladolid` (retirado en T-126). El registro rechaza añadir `congreso350_*`.
- Una PR que añade ficheros debe regenerar `orchestracion/catalogo_procedencia.json`; el bot de archivo reescribe evidencia que los tests leen vivos (Cantabria): fixture fija (#569).

## Lecciones 10-11 (Coordinador)
- El ruleset activo `proteger-main` exige el check `veredicto` (job del Revisor), no `pruebas`; admin y la app de registro lo esquivan. No lo hagas no-bloqueante ni muevas/renombres el job sin decisión del propietario. La fusión automática fusiona al ver `pruebas` en success sobre el HEAD exacto: no mira Revisor, ni main, ni revisión humana; una PR que espera correcciones va en borrador o con no-automerge.
- Una PR apilada se fusiona con su primer HEAD (#624): no apiles más de dos; el squash deja conflictos add/add en la siguiente (versión de la rama si main = PR fusionada); reapunta con `gh api -X PATCH pulls/<n> -f base=main`.
- Cuenta `gh api .../actions/runs` topa a 1.000 por consulta: ventanas `created=ini..fin` (6 h), bisección y caché por run; minutos = suma de jobs (el `/timing` da 0).
- Desde la nube no se descargan artefactos (blobs Forbidden): solo metadatos por REST; solo boe.es e ine.es responden entre las fuentes externas.
- La hija «Reutilizar» del bot falla con DURABLE_LINEAGE_INCOMPATIBLE si el catálogo conserva un resultado electoral viejo con la 04 en failure y digest vacío: la 00 buena queda TERRITORIAL_READY_ELECTORAL_PENDING sin resultados electorales.
- Los adaptadores del motor nuevo dependen de nombres de fichero (glob ancho cogió el GeoJSON de distritos): fija nombre y extensión; la composición no trae todos los campos de la validación (islas: DDD_PARTITION).
- Tests con fracciones exactas (100·1,15 da 114,999…); imagen de CI sin `.git`: nada de `git grep` en tests; comprueba que los tests aleatorios no son vacuos.


## Lecciones 10-11 (cierres de chats, 2.ª tanda)
- Sin el repositorio de origen (`source_url`) un chat de tarea no puede empujar; sin él la sesión sale `no-git-repo`: ciérrala y recréala.
- Borrado irreversible (poda ARC, runs): entorno protegido sin exención de bots, informe como artefacto antes del push y verificación de todas las filas antes de borrar la primera; el Operador repite el inventario.
- Semilla pública con el id del territorio: si el id cambia, cambia el mapa; sembrar con el código de la tabla maestra vía resolutor (D-61/6). La huella del laboratorio depende de GEOS/shapely (RESULTADO.json guarda el entorno).
- Al subir VERSIÓN de un fichero de `ddd_motor2/` también se exige copia en `legacy/ddd_motor2/` (el revisor da FAIL si falta).
- `desplegar-visor-publico.yml` y `generar-alternativas-territoriales.yml` solo piden la aprobación `produccion` si `github.workflow ==` su nombre; al renombrar desaparece sin avisar. El nombre de la 00 lo usan el forense, `legislatura_vigente.py` (TITLE_00) y `metricas_proceso.py` (RUN_NAME). El corte exige prueba explícita de que la aprobación sigue (D-61).
- El registro rechaza `congreso350_*`; en el corte debe rechazar también `nacNN-350`.
- Ahorro de CI (1.9.0): clasificar en un job sin concurrencia, grupos únicos por run fuera del caso cancelable, diff `--no-renames`; clave `concurrency` duplicada la acepta PyYAML pero no GitHub. Tras squash de PR apilada el merge de origin/main choca con contenido idéntico: diff vacío → «ours». Reducir comprobaciones exige la frase del propietario en el chat que ejecuta («CI Bypass»).
- Lista de Actions: 24 ficheros (23 sin la Poda de R2); cuatro «Interno ·» aceptadas; fusión automática y forense intactos hasta el corte.
- CLAUDE.md está en 100 líneas: regla nueva exige compactar otra. Parches de ESTUDIOS: `git apply --check`, luego sustituir el id de decisión con sed. PR sensible: borrador + etiqueta no-automerge por REST y salir de borrador con `pulls/<n>/ccr/ready_for_review`. Los MCP de GitHub se desconectan a ratos: `gh api` REST sigue.
- Naturalidad/GerryChain: seccionado INE desde ine.es; pyogrio con `where` exige leer la columna filtrada; contigüidad con puentes en vértice (Madrid, Barcelona); GerryChain 1.0 usa ids internos (guardar id real); elegir por naturalidad sin tope propio lleva el desvío al borde de la tolerancia (≈15 %), de ahí D5/D8.
- Histórico autonómico: medir en `fuentes/observatorio_autonomicas/index.json` (clave sekzioak) antes de descargar; `siglas_sin_homologar.json` se sobrescribe por pasada: fusionar a mano.
- Desde la nube solo `boe.es` e `ine.es`; zenodo.org, github.io y developers.cloudflare.com dan 403: DOI y aviso de Cloudflare los comprueba el propietario. Nombres de release `fuente-*` y URLs de descargas manuales son propuesta hasta confirmarlos.
- Elección como dimensión (10-11): «vigente por run_id mayor» estaba en ~10 sitios (herramientas y un workflow): antes de cerrar una dimensión nueva, grep de `canonical_m0[68]` y `max(.*run_id` en `herramientas/` y `.github/`. Un helper único (`resultados_ligeros.vigente_por_eleccion`) y heredar vía `composicion_m06.m06_vigentes`. Test por consumidor con entrada 2026 simulada de run_id mayor. Fechas con `datetime.date.fromisoformat`, no solo regex. Sin pyproj/geopandas en la nube: `pip install pyproj` antes de los tests del registro.
- Homologación 2026: reglas y candidaturas 2026 solo con `eleccion=202611`; otra elección, solo su tabla `interior`. Sigla sin regla = fallo cerrado. La tabla de equivalencia 2023 se llama `_2023`. El registro rechaza dos entradas con el mismo blob (simular con `blob_sha` y `sha256` ficticios); fixtures de sha con `[-40:]`.
- Proceso (10-11): el rol implementador es una tarea por chat (rechaza ampliaciones: abre otro). El revisor da BLOCKED con CI pendiente: no es un defecto; si el HEAD cambia, vale otra revisión solo si el cambio no es trivial. Un cambio de turno sobre ficheros compartidos lo concede el Coordinador si ningún chat vivo los toca. Un ensayo/estudio de una PR abierta se lee con `git checkout origin/<rama> -- <ruta>` y `git reset` (borra la copia: el hook de parada exige commit de lo no seguido).
