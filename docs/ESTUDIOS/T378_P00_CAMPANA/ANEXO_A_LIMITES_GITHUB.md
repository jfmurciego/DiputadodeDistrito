# T-378 · Anexo A · Límites de GitHub Actions verificados

VERSIÓN: 1.1.0 · FECHA: 2026-11-16 · ANTERIOR: `legacy/docs/ESTUDIOS/T378_P00_CAMPANA/ANEXO_A_LIMITES_GITHUB_v1.0.0.md`
CAMBIOS 1.1.0: cada fila re-verificada el 16-11 contra la fuente oficial con su ruta exacta; filas 1-17 con la misma
numeración (el diseño 1.1 cita 11 y 9 para matriz → reutilizable y 10 niveles, 12 para salidas de matriz, 13 para el
mismo commit, 14 para lanzar desde otra rama); añadidas 18 (`fail-fast`), 19 (cola por defecto de un grupo), 20
(`max-parallel`) y 21 (`workflow_run` encadenado); nota de que la fila 6 solo aplica con la versión «actions-nga» de
la documentación. MOTIVO: D-145 (arreglos del revisor del diseño 1.0).

Consulta: **16-11-2026**. `docs.github.com` no resuelve desde la sesión en la nube; se lee la fuente pública de esa
documentación, el repositorio `github/docs` (rama `main`), en
`https://raw.githubusercontent.com/github/docs/main/<ruta>`. La columna «Fuente» da la ruta; todas respondieron 200.
Citas literales, en inglés. GitHub avisa de que los límites pueden cambiar.

Rutas abreviadas: **L** = `content/actions/reference/limits.md` (publicada en docs.github.com/en/actions/reference/limits);
**S** = `content/actions/reference/workflows-and-actions/workflow-syntax.md`;
**C** = `data/reusables/actions/actions-group-concurrency.md` (incluida en S, `concurrency`).

| # | Límite | Valor | Cita | Fuente |
|---|---|---|---|---|
| 1 | Jobs por matriz | 256 por ejecución | «A job matrix can generate a maximum of 256 jobs per workflow run.» | L, tabla «Existing system limits» |
| 2 | Duración de una ejecución | 35 días | «35 days / workflow run … This period includes execution duration, and time spent on waiting and approval.» | L, ídem |
| 3 | Duración de un job (runners de GitHub) | 6 h | «Each job in a workflow can run for up to 6 hours of execution time.» | L, ídem |
| 4 | Jobs a la vez, runner estándar | Free 20 (macOS 5); Pro 40; Team 60 | tabla «Job concurrency limits for GitHub-hosted runners»: «Standard … runner \| Free \| 20 \| 5» | L |
| 5 | Re-ejecuciones | 50 por ejecución | «A workflow run can be re-run a maximum of 50 times. This limit includes both full re-runs and re-runs of a subset of jobs.» | L, «Existing system limits» |
| 6 | Cola con `queue: max` | 100 por grupo | «When using `queue: max` in the `concurrency` section, up to 100 jobs or workflow runs can be queued per concurrency group.» (fila dentro de `{% ifversion actions-nga %}`) | L, ídem; y C |
| 7 | Espera de aprobación de un entorno | 30 días | «A workflow may wait for up to 30 days on environment approvals.» | L, ídem (P00 no usa entorno con aprobación; solo P40 si lo pide) |
| 8 | Tamaño del fichero de workflow | 500 KB | «A workflow file larger than 500 KB will not start runs.» (la 00 actual: 113 KB) | L, ídem |
| 9 | Anidamiento de reutilizables | 10 niveles | «You can connect up to ten levels of workflows.» | `content/actions/reference/workflows-and-actions/reusing-workflow-configurations.md` |
| 10 | Reutilizables distintos desde un workflow | 50 (árbol incluido) | «You can call a maximum of 50 unique reusable workflows from a single workflow file. This limit includes any trees of nested reusable workflows.» | ídem |
| 11 | Matriz que llama a un reutilizable | Sí | «Jobs using the matrix strategy can call a reusable workflow.» | `content/actions/how-tos/reuse-automations/reuse-workflows.md` |
| 12 | Salidas de una matriz de reutilizables | Solo la última | «the output will be the output set by the last successful completing reusable workflow of the matrix which actually sets a value.» | ídem |
| 13 | Versión de los reutilizables locales | Mismo commit | «… the called workflow is from the same commit as the caller workflow.» | `data/reusables/actions/reusable-workflow-calling-syntax.md` |
| 14 | Lanzar desde otra rama | Solo por API y tras una primera ejecución | «the "Run workflow" button will be present if the workflow file exists on the default branch. Once a workflow has run at least once, you can dispatch it against any branch or tag via the … API» | `content/actions/reference/workflows-and-actions/events-that-trigger-workflows.md` |
| 15 | `workflow_run` (disparo de la IA de cierre) | Solo desde la rama por defecto | tabla del evento: «workflow_run … Last commit on default branch \| Default branch» | ídem, `## workflow_run` |
| 16 | API con el token del workflow | 1.000 peticiones/h por repositorio | «The rate limit for `GITHUB_TOKEN` is 1,000 requests per hour per repository.» | `data/reusables/rest-api/primary-rate-limit-github-token-in-actions.md` |
| 17 | API con la app (token de instalación) | 5.000/h como mínimo | «… 5,000 requests per hour …» | `data/reusables/rest-api/primary-rate-limit-github-app-installations.md` |
| 18 | `fail-fast` de una matriz | `true` por defecto | «… will cancel all in-progress and queued jobs in the matrix if any job in the matrix fails. This property defaults to `true`.» | `data/reusables/actions/jobs/section-using-a-build-matrix-for-your-jobs-failfast.md` (incluida en S) |
| 19 | Cola por defecto de un grupo de concurrencia | 1 en espera; la nueva sustituye a la anterior | «`single` (default): At most one job or workflow run can be `pending` in the concurrency group. When a new job or workflow run is queued, any existing `pending` job or workflow run in the same group is canceled and replaced.» | C |
| 20 | `max-parallel` | Limita los jobs de la matriz a la vez | «To set the maximum number of jobs that can run simultaneously when using a `matrix` job strategy, use `jobs.<job_id>.strategy.max-parallel`.» | `content/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations.md` |
| 21 | `workflow_run` encadenado | Máximo 3 niveles | «You can't use `workflow_run` to chain together more than three levels of workflows.» | fuente de la fila 14, `## workflow_run` (P00 → P90 es 1 nivel) |

**No figura en la documentación** (no se da valor): un tope de jobs por ejecución aparte del de la matriz; si los jobs
internos de un reutilizable llamado desde una matriz cuentan para los 256; si `max-parallel` sobre una matriz de
reutilizables limita filas o jobs internos (el diseño no depende de ello: cada cadena tiene un solo job a la vez); el
tiempo máximo en cola de un job en runners de GitHub (el de 24 h es solo para runners propios). Se comprueban en la
prueba de humo y en la validación (diseño, §10).

**No verificado aquí:** el plan de la cuenta (Free = 20 jobs a la vez); lo confirmó el propietario (D-143).
