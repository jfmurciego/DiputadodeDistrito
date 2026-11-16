# T-378 · Anexo A · Límites de GitHub Actions verificados

VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ANTERIOR: ninguna (fichero nuevo)

Consulta: **16-11-2026**. `docs.github.com` no resuelve desde la sesión en la nube (`ENOTFOUND`); se leyó la fuente
pública de esa misma documentación, el repositorio `github/docs` (rama `main`), en `raw.githubusercontent.com`. La
URL publicada de cada página se indica al lado. Citas literales, en inglés. Los límites «sujetos a cambio» según
GitHub.

| # | Límite | Valor | Cita | Página (publicada · fuente) |
|---|---|---|---|---|
| 1 | Jobs por matriz | 256 por ejecución | «A job matrix can generate a maximum of 256 jobs per workflow run.» | docs.github.com/en/actions/reference/limits · `content/actions/reference/limits.md` |
| 2 | Duración de una ejecución | 35 días | «Workflow run time — 35 days / workflow run … includes execution duration, and time spent on waiting and approval.» | ídem |
| 3 | Duración de un job (runners de GitHub) | 6 h | «Each job in a workflow can run for up to 6 hours of execution time.» | ídem |
| 4 | Jobs a la vez, runner estándar | Free 20 (macOS 5); Pro 40; Team 60 | tabla «Job concurrency limits for GitHub-hosted runners» | ídem |
| 5 | Re-ejecuciones | 50 por ejecución | «A workflow run can be re-run a maximum of 50 times.» | ídem |
| 6 | Cola con `queue: max` | 100 por grupo | «up to 100 jobs or workflow runs can be queued per concurrency group.» | ídem |
| 7 | Espera de aprobación de un entorno | 30 días | «A workflow may wait for up to 30 days on environment approvals.» | ídem |
| 8 | Tamaño del fichero de workflow | 500 KB | «A workflow file larger than 500 KB will not start runs.» (la 00 actual: 113 KB) | ídem |
| 9 | Anidamiento de reutilizables | 10 niveles | «You can connect up to ten levels of workflows.» | docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations · `content/actions/reference/workflows-and-actions/reusing-workflow-configurations.md` |
| 10 | Reutilizables distintos desde un workflow | 50 (árbol incluido) | «You can call a maximum of 50 unique reusable workflows from a single workflow file. This limit includes any trees of nested reusable workflows.» | ídem |
| 11 | Matriz que llama a un reutilizable | Sí | «Jobs using the matrix strategy can call a reusable workflow.» | docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows · `content/actions/how-tos/reuse-automations/reuse-workflows.md` |
| 12 | Salidas de una matriz de reutilizables | Solo la última | «the output will be the output set by the last successful completing reusable workflow of the matrix which actually sets a value.» | ídem |
| 13 | Versión de los reutilizables locales | Mismo commit | «When you reference a reusable workflow in the same repository using `$/` or `./` … the called workflow is from the same commit as the caller workflow.» | reutilizado en la sintaxis de `jobs.<job_id>.uses` · `data/reusables/actions/reusable-workflow-calling-syntax.md` |
| 14 | Lanzar desde otra rama | Solo por API y tras una primera ejecución | «the "Run workflow" button will be present if the workflow file exists on the default branch. Once a workflow has run at least once, you can dispatch it against any branch or tag via the GitHub API» | docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows · `content/actions/reference/workflows-and-actions/events-that-trigger-workflows.md` |
| 15 | `workflow_run` (disparo del forense / IA de cierre) | Solo desde la rama por defecto | tabla de eventos: «workflow_run … Last commit on default branch» | ídem |
| 16 | API con el token del workflow | 1.000 peticiones/h por repositorio | «The rate limit for `GITHUB_TOKEN` is 1,000 requests per hour per repository.» | docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api · `data/reusables/rest-api/primary-rate-limit-github-token-in-actions.md` |
| 17 | API con la app (token de instalación) | 5.000/h como mínimo | «use the installation's minimum rate limit of 5,000 requests per hour.» | ídem · `data/reusables/rest-api/primary-rate-limit-github-app-installations.md` |

**No figura en la documentación** (no se da valor): un tope de jobs por ejecución aparte del de la matriz; si los jobs
internos de un reutilizable llamado desde una matriz cuentan para los 256; el tiempo máximo en cola de un job en
runners de GitHub (el de 24 h es solo para runners propios); y si un workflow puede llamarse a sí mismo. P00 no
depende de ninguno de ellos más allá de lo que se comprueba en la validación (diseño, §9).

**No verificado aquí:** el plan de la cuenta (Free = 20 jobs a la vez); lo confirma el propietario.
