# Traspaso del Coordinador — 16-11-2026 (noche)

VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ANTERIOR: ninguna (fichero nuevo)

Sesiones: Coordinador saliente `session_01KQDtFvHdfhWXuS4s8HXzdv` (Sonnet) · Planificador `session_01KQDtFsPWJU3AMdHjHmWcvp` (Opus; releva a `session_01KQDtFsURitLodmiR3KkgF3`, archivada de hecho) · Operador `session_01KQDtFqw1LBgGn6nCuxP8Yx` (Opus).
Rol del Coordinador: skill `coordinador`. Reglas de oro: recibe cierres, sigue PR/CI/runs por REST (`gh api`; GraphQL no va), un revisor independiente por PR (el mismo agente se reutiliza con SendMessage para el delta), archiva chats terminados tras pedir lecciones (≤6 líneas), no implementa, no lanza, no publica, no edita `docs/PLAN.md`, escala solo decisiones y causas de fallo. Respuestas cortas en español, sin estudios por iniciativa propia (D-18). Mínimo gasto. Todas las PR llevan `no-automerge`.

## Cómo se fusiona (lo que ha funcionado hoy)
- Orden explícita del propietario en SU chat: «fusiona N» (o «fusiona N cuando esté verde»). El clasificador a veces deniega la fusión (#818, #840, #846, #852): NO se rodea; se pide al propietario que diga «fusiona N» o fusione él.
- Antes de fusionar: CI `pruebas` en verde sobre el SHA exacto de la PR, `guardian` y `pruebas` de main en verde (regla en `.claude/rules/workflows.md`: ahora mira P90, `p90-automatico.yml`, evento push + nocturna), PR fuera de borrador (los implementadores cloud no pueden: `mcp__github__update_pull_request draft=false` y etiqueta `no-automerge` por REST `POST issues/N/labels`).
- Comando: `gh api -X PUT repos/jfmurciego/DiputadodeDistrito/pulls/N/merge -f merge_method=squash -f sha=<40hex>`. «Base branch was modified» tras otra fusión: esperar a que acabe la CI de main y reintentar. Fusiones seguidas: vigilar «main en verde» después (hoy 4 seguidas dieron verde).
- Un fallo de `pruebas` sobre un SHA ANTERIOR (cancelado por un push nuevo) no cuenta: solo el SHA vigente. Mirar `gh api repos/.../actions/jobs/<id>/logs` (los check-runs dan `id` = job id) y filtrar `FAIL:|AssertionError`.

## 1. PR abiertas (16-11 ~23:35 UTC)
| PR | Qué | Estado | Qué falta |
|---|---|---|---|
| #865 | T-389 (T-365b): 5 contratos del histórico regenerados con las tablas de T-364b | revisor sin bloqueantes; CI roja en 9abd89c por un test que leía `legacy/`; arreglado en df4619c | CI verde y «fusiona #865» |
| #866 | T-376: P30 Resultados electorales (`p30-resultados-electorales.yml`) | revisor 2 pasadas sin bloqueantes en c6eeb1d; en curso: D-148 (botón UN territorio por ejecución, sin matriz) + aserción working-directory en `test_credencial_registro` | nuevo commit, delta al revisor (`ac8acb013dddc9285`), CI. **NO fusionar antes del fin del ensayo del 29-11**; orden T-375→T-376→T-377 |
| #867 | T-391: `source_sha256` de los 3 contratos de ensayo = MANIFEST + F10 reanclado (25ada01c…) | revisado por mí (hashes = MANIFEST; sha del YAML = F10). El Operador YA verificó el release (3 assets, sha y LF OK). CI en curso | CI verde y «fusiona #867» (es lo que desbloquea la 03 del ensayo) |
| #868 | T-392: la equivalencia congelada ignora la versión de las acciones de terceros (helper `tests/_uses_sin_version.py`) | revisada por mí; CI en curso | CI verde y «fusiona #868» |
| #863 | Dependabot: bump anthropics/claude-code-action 1.0.269→1.0.276 (p90 y revisor-pr) | CI roja SOLO por el test de equivalencia de T-366 | tras fusionar #868: `@dependabot rebase` (la rama de Dependabot probada por T-392 no compartía historia con main) y fusionar si verde |
| #869 | Plan 1.0.58 del Planificador (D-148) | solo docs | CI verde y fusionar |
| #842 | T-365: 5 fichas de campaña del histórico | BORRADOR a propósito (se reescriben para P00) | no tocar |
No existen aún las PR de T-375 (P10) ni de T-377 (P20).

## 2. Sesiones vivas
| Tarea | Sesión | Modelo | Qué hace |
|---|---|---|---|
| T-375 P10 Fuentes (D-136) | `session_01KQDtFtRgJ2wHHDrgodZxrx` | Sonnet | `p10-fuentes.yml`; matriz directa (un job por territorio); grupo de concurrencia = nombre del catálogo como P30 (coordinado) |
| T-376 P30 (D-137/D-148) | `session_01KQDtFrwnyMpEuUTaC5JL83` | Sonnet | #866 |
| T-377 P20 (D-139/D-148) | `session_01KQDtFsFXac3JYp5DcpP3xY` | Opus | `p20-distritos.yml`, un territorio por ejecución (B), retira alternativas, entradas ensemble de P40 y 31 configs ensemble a legacy si nada vivo las lee |
| T-389 | `session_01KQDtFt4fks1ZK3sjNCqvWo` | Sonnet | #865 |
| T-391 | `session_01KQDtFt6y9trZLwKxKLhyad` | Sonnet | #867 |
| T-392 | `session_01KQDtFvDvv7WLYuzL5MxY6L` | Sonnet | #868 |
| Operador | `session_01KQDtFqw1LBgGn6nCuxP8Yx` | Opus | verificó el release de ensayo; espera frases D-52 del propietario |
Los cierres de T-389/T-391/T-392 incluyen lecciones ≤6 líneas: pedirlas y archivar tras fusionar. Revisores reutilizables (SendMessage): `ac8acb013dddc9285` (#866), `a7c112a08879443c5` (diseño P00), `af4d0b52feed45219` (P40), `a39aa95bf8a17cd96` (#865). Máximo ~4-5 implementadores a la vez.

## 3. Efectos pendientes del propietario y del Operador (no los hace el Coordinador)
- **Ensayo 29-11:** #867 → main verde → ficha del Operador (`docs/autorizaciones/2026-11-15_ensayo-noche-29-11.md`, rama `operador/fichas-r6-congreso32`, aún sin fusionar) → frase D-52 del propietario en el chat del Operador. El release `fuente-ensayo-congreso-2026-11-29` ya está publicado y verificado.
- **P40:** prueba real «solo el sitio» sin simular, por el Operador, con frase del propietario; comprobar que el visor queda igual. Lo no probado en Actions está en `docs/registro/2026-11-16_t372-p40-publicacion.md`.
- **T-380 (ensembles):** #849 fusionada; falta publicar el visor y borrar las 3 Releases `ensemble-congreso-{la-rioja-cccc4a1e8df2,salamanca-2b68dd0a396a,sevilla-9987893f2689}` (≈35 MB), cada cosa con frase del propietario. T-380 no está HECHA hasta entonces.
- **Zenodo (#859 fusionada):** antes de crear `ZENODO_TOKEN`/`ZENODO_SANDBOX_TOKEN` en el entorno `publicacion`: política de ramas (solo main) o revisores en ese entorno, y desactivar la integración GitHub–Zenodo; después sandbox por el Operador con frase. Nunca tokens en el chat.
- **Ruleset `proteger-main`:** exige solo `veredicto` (no `pruebas`); D-144: añadir `pruebas` (T-386 comprobó que existe en toda PR; riesgo: PR abierta con GITHUB_TOKEN no dispara CI). Lo hace el propietario en Ajustes o el Operador con frase. Corregir en `.claude/rules/workflows.md` (~l.38) y D-135 que el ruleset no exige `pruebas` (pendiente en la PR de lecciones).
- **Contraste aut11 del extracto del padrón:** sin resultado todavía (el propietario lo corre en su Windows; pasos en este traspaso abajo). Desbloquearía dar por bueno #797 (ya fusionada).
- Subida a R2 de las 644 piezas: HECHA (642 saltadas + 2 subidas, 0 fallidas).

## 4. Encargos en espera
- **T-379 PR 2a/2b/3/4** (Opus): detrás de T-377 y del conforme del diseño (ya dado, `docs/ESTUDIOS/T378_P00_CAMPANA/` 1.1.4, decisiones D-143/D-145/D-147). 2a = entorno `registro` limitado a main con humo real ANTES de borrar secretos del repo; si no hay humo verde antes del 28-11, la 2a va después del ensayo. La 00 actual es el caso base de la noche del 29-11.
- **T-383** (docs renumerada, la última), **T-381** (detección de checkpoints incompatibles, tras T-377).
- **T-385/T-386** hechas (T-386 = comprobación del check `pruebas`).
- La **PR 1 de T-379** (estado de campaña, `herramientas/campana_estado.py`) está fusionada (#861).

## 5. Lecciones aún no guardadas (para la PR de lecciones de CLAUDE.md/`.claude/rules/`; las de hoy ya fusionadas fueron #828, #835, #837, #844)
# Lecciones recibidas (15-11) para la PR de lecciones
## T-323/T-326 (archivado)
1. HEAD no sirve para el padrón dinámico (sin Content-Length/ETag): medir cabeceras reales antes.
2. La copia R2 del padrón no es byte-idéntica al CSV vivo: D-119 compara el EXTRACTO filtrado contra el del paquete R2.
3. El CSV de ~1,6 GB se lee en streaming sin guardarlo.
4. Un test de «sin ::error::» pasa en falso si la excepción se traga como ::warning::.
5. copytree con ignore_patterns("MANIFEST.json") descarta también los de subcarpetas; DDD_EN_PR se pasa con -e al docker run solo en PR.
Pendiente: contrastar el extracto con un paquete real aut11 r4 antes de la P50. #797 f94065f, #798 553411d (borradores).
## T-349b (archivado)
1. La 00 en «Generar desde fuente»/«Desde el principio» no pasa por validate_durable_assets: lee recibos en crudo; el filtro de id va en build_plan antes de planificar, para todos los modos.
2. Descarta solo alias conocidos (variantes()): un recibo sin territory_id (fixture sintética) no es alias.
3. territorial_identity con esperado devuelve territory_id=variante: comparar identity["territory_id"]==canónico reconoce la huella vieja sin habilitar reuso.
4. Fixtures de flujo: git show <base>:config+evidencia por territorio (sin inputs/ ni resultados/, ~140 MB→4 MB) + enlaces a modulos/herramientas/ddd_core en raíz temporal.
5. Antes de atribuirte un fallo, compáralo con el commit anterior y con main en worktrees aparte.
6. Suite como CI local: repartir_tests.py --grupos 5 --grupo N en paralelo con DDD_EN_PR=1 (~8 min).
## T-325 (#820@d44c371)
1. Commons/Wikipedia dan 429 (Retry-After ~30 s) desde IP compartida: batch y esperar. wikidata.org y thumb.wikimedia.org bloqueados; upload.wikimedia.org sí (/thumb/<ruta>/960px-<nombre>).
2. pageimages de es.wikipedia da banderas y prop=images sale alfabético: usar generator=search en Commons + extmetadata, filtro por título y hoja de contactos.
3. El workflow de publicación copia visor/v2/ entero y de v3 solo 4 ficheros: recursos nuevos en visor/v2/.
4. CC BY/BY-SA exigen indicar cambios: guardar `cambios` por imagen, mostrarlos en el pie, créditos y NOTICE; LICENSE solo con decisión del propietario.
5. Tests JS no corren en la CI de unittest (sin Node).
6. `git checkout <fichero>` tras una mutación de prueba pierde la edición sin commitear.
## T-332/T-333 (#800@54a70db, #801@ba60dde)
03 = workflow + resolutor propio sin tocar elecciones_vigentes; terminal ENSAYO_OK con source_class en selected_source; fail-closed PENDIENTE_T333/exit 53/57; formato Minsait supuesto (si no encaja, solo infoelectoral_mesas); fixtures con claves 2026 para ejercer M07; t220 y geopandas.
## T-353 (#824 fusionada 94e4336, archivado)
1. Recibos y f10_auto_tareas.json anclan el sha del contrato: al tocar un contrato, `git grep <sha viejo>` fuera de docs/legacy/fixtures.
2. El test de barrido debe tolerar temporales de otros tests (FileNotFoundError) si corre en paralelo; con control positivo y negativo en árbol temporal.
3. Todo test nuevo con ids viejos debe derivarlos de territorio_ids (id_legacy("aut02")); correr test_t220_renombrado antes de empujar (guardián SinIdsViejos).
4. test_motor2_aceptacion.HuellaFija falla con ortools distinto (9.15 vs 9.14.6206): no es de main; fijar la versión de la CI.
5. La identidad electoral no incluye el sha del contrato.
6. Un implementador que dice «falla igual en main» sin prueba: exigir run de main o worktree de origin/main.
## T-356 (#829 fusionada, archivado) — ya recogidas en #828 las de PowerShell; añadir:
4) `-eq` de PS ignora mayúsculas; el sidecar .ok no basta: recalcular sha256 y comparar contra R2 (Metadata.sha256 + ContentLength).
5) fuentes_r2.json lo tocan varias PR (#827, #797, #829): partir de main; si diverge, `git merge origin/main` + unión por clave, nunca rebase.
3) Sin pwsh en la nube los bugs de PS salen en el PC del propietario: catch con tipo+mensaje+línea+pila en una línea y `error` por pieza en el JSON; -Limite 1 -SoloBajar antes del lote.
## T-323b (#797 fusionada)
Probar con python3.11 (el de la CI), no el 3.13 local (f-string con backslash en la expresión = SyntaxError en 3.11); tests que fijan `if:` exactos de preparacion-fuentes.yml: caducada, reutilizacion (+ huerfana/preflight por `in`); la copia R2 del padrón va con tabulador y el INE sirve ';': comparar en forma canónica.
## T-362 hotfix (#836)
Un test que afirma sobre INDEX.json o un MANIFEST vivo con ids concretos se rompe al registrar ids nuevos: dict sintético. En el contenedor cloud: pip install -r requirements.lock --ignore-installed PyYAML (+ shapely).
## T-360 (#839, en revisión)
Quitar un grupo único exige re-derivar, no rebasar (pull --rebase sobre YAML/JSON compartidos choca): delta JSON por claves + reaplicar desde el HEAD vigente; test de concurrencia con barrera antes del primer push y backoff con la misma forma que el de producción (con backoff lineal fijo, una cadena se quedó sin turno 10 veces); los bloques run: pierden la sangría al extraerlos en tests.
## T-360 cierre (#839 fusionada 5bad36c)
Test de «4 no bastan, 10 sí» con 14 cadenas: backoff de la misma forma que producción (exp+jitter); una barrera por intento lo vuelve vacuo. Remoto bare con pre-receive que sale 1 = prueba real y barata de exit 75. persistir_evidencia_pre_m04 captura RuntimeError→54: excepciones nuevas heredando RuntimeError se colapsan. Cola de concurrencia = started_at−created_at de /runs/<id>/jobs; --paginate de /commits falla por el proxy: page= a mano.
## T-325 (#820)
Test que exige legacy/ falla en CI (imagen sin .git y con parte de legacy): comprobar solo árbol git (patrón test_t127). Clon superficial: git fetch --unshallow antes de merge.
## T-364/T-365/T-332b
Atlas «""» no siempre inexistente: contrastar con seccionado del año; F10 se reancla al tocar contrato; revisor: deltas tras cambios de regla.
## T-365 cierre (#841 fusionada c163205)
1. load_params_yaml resuelve como ruta todo string con «/» o extensión: en textos de contratos M01-M06 (k_rationale…) nada de «/».
2. K se compara con el catálogo maestro 2025; histórico = meta.historico_epoca + contrato de su elección (territory_contract 1.5.0, rama acotada a <t>_hAAAA_MM); territory_contract fuera del cierre M05. Prueba bit a bit contra copia legacy sobre 172 contratos.
3. M01 exige población = seccionado exactos; topology_bridges claves u/v (int sin cero).
4. Desde la nube: www.ine.es y nazioenbehatokia.eus sí, R2 no; zips M06/M08 cambian de hash por fecha: comparar composición CSV. Coste: Opus ~2,5 h, 0 min Actions.
## T-366 (#845 P90)
1) GitHub declara INVÁLIDO (run push fallido sin jobs, sin mensaje por API) un workflow cuyo workflow_run.workflows se nombra a sí mismo; comprobar pronto con actions/runs?head_sha= si el run es «.github/workflows/x.yml|push|failure».
2) labeled/ready_for_review en el workflow que define `pruebas` crean un check-run skipped en otra suite sobre el HEAD (el ruleset lo cuenta como cumplido): no mezclar.
3) Un job con needs en el run de la PR ejecuta código de la PR: ahí sin secretos de la app; la fusión corre por workflow_run (definición de main).
4) Al mover jobs entre ficheros, bajar el concurrency de workflow (cancelar por PR) a cada job.
5) legacy/workflows no está en la imagen CI: tests de equivalencia con fixtures + sha256, sin skipTest, con control negativo.
6) El revisor encontró lo que el autor declaró como «riesgo»: exigir resolverlo, no aceptarlo.
## T-380 (#849)
El registro del visor no tiene comando de baja: load/validate/save_registry (formato canónico) y regenerar el catálogo con catalogo_procedencia.py. Las configuraciones ensemble las leen workflow, gestor_campanas_2, legislatura_vigente y 11 tests (las retira T-377). Python 3.11 local necesita pyproj/pyyaml/shapely (geopandas solo para M05Determinism). Los implementadores cloud no pueden pasar a «listo» (sin gh/MCP github): lo hace el Coordinador. Tras fusionar, la P50/P40 retira los ensembles del sitio.
## T-378 (#850)
docs.github.com no resuelve desde la nube (ENOTFOUND): usar raw.githubusercontent.com/github/docs/main/content/actions/reference/limits.md. gh api --paginate falla tras el proxy (sigue enlaces repositories/{id}, 403): paginar a mano con &page=N. Límites verificados: matriz 256/ejecución, 20 jobs a la vez en Free, 10 niveles de anidamiento, 50 reutilizables, job 6 h, salida de matriz = solo la última fila, reutilizables locales = mismo commit del llamador. workflow_dispatch de un fichero que no está en main: solo por API desde la rama y tras una primera ejecución; workflow_run solo dispara desde main. Coste r3/r4 (15-11 00:00→16-11 12:00): 161 runs 00 (4.926 min) + 81 Legislatura (219 min) ≈ 72 min/territorio.
## T-368 (#851 P70)
1) Un job con needs de otro saltado queda saltado salvo !cancelled() en su if: al fundir un workflow_call con un botón con resolutor, todos los jobs aguas abajo lo necesitan. 2) test_credencial_registro exige «Credencial de registro» tras el checkout en todo job cuyo run mencione persistir_producto_electoral_operacional/git push, aunque el resolutor solo lea. 3) La ANTERIOR de un workflow nuevo que sustituye a varios debe ser UNA ruta (test r015); el resto en CAMBIOS. 4) Un test que fija workflow_dispatch de ficheros borrados está en 7 tests (catálogo, matriz, codauto, cuota, corte 5.0.0 + generar_equivalencias_5_0_0.py y su doc generado). 5) Inputs de GitHub no admiten tildes: `eleccion`. 6) Pendiente: quitar de `paths` del pull_request de la 00 la ruta del fichero borrado.
## T-374 (#852) — hallazgo verificado
El ruleset `proteger-main` (id 26311854) exige SOLO `veredicto` (integration 15368), no `pruebas`; veredicto skipped cuenta como cumplido. Nada obliga a `pruebas` en verde: lo garantizan auto-merge (pruebas success de su suite) y la regla «CI verde en la PR y en main». Corregir D-135/workflows.md l.~38. Docs de GitHub: raw.githubusercontent.com/github/docs/main/content/...; skipped=cumplido solo verificado en about-protected-branches.md; troubleshooting de checks da 404; sin verificar: nombres de check-runs de reutilizables y si pull_request_target/workflow_run adjuntan checks al HEAD de la PR.
## T-370/T-372/T-384/T-364b
Todo workflow nuevo con upload-artifact se clasifica en tests/test_artefactos_ci_cuota.py (grep upload-artifact en tests/ al crear). Implementadores cloud sin gh: el Coordinador pone `no-automerge` y saca de borrador. El Atlas «2020» usa códigos del seccionado 2021; `python3.11 -m pip` (no pip) para el lock; geopandas escribe CUSEC con ancho >10. Si un implementador queda «a la espera de una señal» (T-364 esperó horas a que se fusionara #840), el Coordinador debe avisarle al fusionar: una sesión inactiva no despierta sola.
## T-387/T-379/T-388 (diseño P00, estado de campaña, Zenodo)
Reutilizable no puede subir permisos del llamador (startup_failure aunque el job tenga if falso): llamar con contents: read y registro en reutilizable propio. Los secretos de repositorio los lee cualquier rama lanzada por API: «la rama no escribe en main» solo es firme con secretos de ENTORNO limitado a main; un job con environment lanzado desde rama no permitida falla, no se salta. Una PR creada con GITHUB_TOKEN no lanza workflows (sin veredicto). `queue: max` y su 100 solo bajo actions-nga; la cola por defecto sustituye a la que espera: «rechazar una segunda campaña» exige comprobarlo en un job, no con concurrency. Una salida numérica no basta para clasificar una causa (el exit 75 tiene 3 orígenes, uno no transitorio): exige el código impreso. Sanear en lugar de rechazar mantiene «rojo por territorio» sin inyección en el issue. Un 400/422 genérico no autoriza una acción irreversible (serie de DOI): discriminar por campo y exigir input explícito. `a && secrets.X || secrets.Y` cruza secretos: un paso por destino. Criterio de recuento explícito (25 usos de la app = líneas con secrets.DDD_REGISTRO_APP_ID fuera de comentarios). El ruleset proteger-main exige solo `veredicto`; `pruebas` existe en toda PR (comprobado en 60).
## T-389 (#865) / T-377 / Operador
Las 5 tablas T-364b se regeneran en ~6 min desde la nube (INE baja sin R2). El test de contratos asumía BLOQUEADA_SIN_DATO ⇔ secciones_sin_dato; con provincias apartadas es también «0 filas». `pip install -r requirements.lock` choca con PyYAML de Debian: --ignore-installed PyYAML. Un workflow no puede llamarse a sí mismo (doc: «Loops in the workflow tree are not permitted», reuse-workflows.md l.195): matriz de cadenas de jobs exige reutilizable; D-148: botón de P20/P30 = un territorio por ejecución, varios = P00. La sesión cloud no puede crear/editar releases (403 del proxy): el propietario los crea en la web con los ficheros que entrega el Operador (SendUserFile); un fichero de ensayo debe llegar con LF (CRLF cambia la huella).

## 6. Qué vigilar
- «main en verde» tras fusiones seguidas (varias PR probadas contra una base anterior).
- D-148 (un territorio por ejecución) aplicado de verdad en T-376 y T-377 (P10 mantiene matriz directa).
- Los apartados de P00 salen VERDE si no hay hechos de fuentes/checkpoints (decisión de T-379 PR 1): la PR 3 debe aportarlos.
- Sesiones inactivas: una sesión parada «a la espera» no despierta sola (T-364 esperó horas a que se fusionara #840): avisar al fusionar.
- Costes (libro): T-364 6,08 · T-365 14,09 · T-366 7,63 · T-368 2,80 · T-369 0,97 · T-370 1,53 · T-372 3,47 · T-374 0,56 · T-378 3,29 · T-379 PR1 4,00 · T-380 0,67 · T-384 0,64 · T-387 5,14 · T-388 1,41 · T-360 9,80 · T-325 6,46 (USD).

## Pasos del contraste aut11 (PowerShell, propietario)
```powershell
cd C:\ddd
git clone --depth 1 https://github.com/jfmurciego/DiputadodeDistrito.git repo   # o git pull si ya existe
python -m pip install pyyaml==6.0.2
cd C:\ddd\repo
python herramientas\contrastar_extracto_p10.py --paquete-dir C:\ddd\paquete --padron C:\ddd\65034.csv --declaracion territorios\aut11\config\aut11_2025.yaml --edicion 2025 --provincias 06 10
echo $LASTEXITCODE
```
(`C:\ddd\paquete` = `paquete.zip` de `arc-e/paquetes-p10/8e6e46097ff67e2155c605b3c8d36561ff564293c55824e69dc6fa2645e005e4.zip` descomprimido: debe tener `manifest.json` y `prepared_sources.zip`; `65034.csv` de https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv.) Salida: IGUAL rc 0 / DISTINTO rc 1 / rc 2 sin un único 65034.csv.
