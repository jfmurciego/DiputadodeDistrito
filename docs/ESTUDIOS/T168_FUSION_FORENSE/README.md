# T-168 — Comprobación de la fusión automática y del forense (solo lectura)

Fecha: 2026-11-10 · `main` en 6ed8643 · Decisión D-53 (propietario vía Planificador). No se ha editado ningún workflow,
no se ha lanzado ni fusionado nada. Datos: REST (`pulls`, `commits/<sha>/check-runs`, `rulesets`); tabla completa en
`fusiones_desde_07-11.csv` (96 PR fusionadas).

## Resumen

- Ninguna de las 61 PR fusionadas por `ddd-registro[bot]` se fusionó sin `pruebas` en success sobre su HEAD exacto
  (terminado entre 20 s y 4,5 min antes de la fusión). Las dos veces del incidente de la v1.0.0 (#453, #454) no se han repetido.
- Fusiones **sin CI verde** desde el 07-11, todas manuales del propietario (administrador, el ruleset lo deja pasar):
  **#538** (16:53:19, `pruebas` terminó 16:54:15, luego success) y **#625** (06:30:37, `pruebas` terminó 06:32:01, luego success).
- Fusiones con HEAD en verde pero `main` en rojo después: **#539** (propietario) y **#617** (bot); #631 (bot, 08:46) aún sin
  `pruebas` sobre su squash al consultar.
- **#624**: fusionada por el bot 28 s después de `pruebas` en verde, con su único HEAD `1229ea2`; el revisor había dado
  `PASS_WITH_EXCEPTIONS` sobre ese mismo SHA (1 menor). Sin revisión humana en la PR. Las correcciones posteriores
  («menores de la revisión final») llegaron en otra PR, #631. El automatismo no mira revisor, revisión humana ni `main`.
- Hallazgo a verificar: el ruleset `proteger-main` exige hoy por REST el contexto **`veredicto`** (GitHub Actions), no
  `pruebas` como dice `.claude/rules/workflows.md`. Elusión permitida para el rol administrador (id 5) y la app de registro.

## 1. Qué hace hoy cada uno

### `auto-merge.yml` (v1.2.1, «_Interno — Fusión automática»)
1. Disparador: `workflow_run` de «Pruebas de la Plataforma», `completed`. No hay `pull_request`, ni botón, ni auto-merge nativo.
2. Job `fusionar` solo si: evento del run = `pull_request`, conclusión `success` y `path` = `pruebas-plataforma.yml`.
3. Permisos del token: `contents/checks/pull-requests: read`. Secretos: `DDD_REGISTRO_APP_ID`/`DDD_REGISTRO_APP_KEY` (firma un JWT y pide
   un token de instalación de la app ddd-registro); sin ellos no fusiona. Concurrencia por `head_sha`, `cancel-in-progress`.
4. Busca PR **abiertas** cuyo HEAD sea el SHA del run (`commits/<sha>/pulls`) y, por cada una, `decidir_auto_merge.py` exige:
   abierta, no borrador, base `main`, rama del propio repo, sin etiqueta `no-automerge`, HEAD = SHA evaluado y check-run `pruebas`
   de ese SHA **y de la check_suite que dispara** en completed/success.
5. Fusión: `gh pr merge --squash --match-head-commit <SHA>` con el token de la app (así el push a `main` dispara numeración,
   catálogo, etc.; con `github.token` no los dispararía).
6. **Lo que NO exige**: `main` en verde; veredicto del revisor; revisión humana ni hilos resueltos; tiempo mínimo desde el
   último push; que `veredicto` (requerido por el ruleset) esté en verde: la app lo esquiva.

### `forense-00.yml` (v1.0.1, «_Interno — Forense de la 00»)
1. Disparador: `workflow_run` de «00 Ejecución Completa del Proyecto», `completed`; solo continúa si la conclusión es `failure`
   (no `cancelled` ni `timed_out`).
2. `comprobar`: sin `CLAUDE_CODE_OAUTH_TOKEN` se salta. `diagnosticar` (15 min): `claude-code-action` (fijada por SHA) con
   Sonnet, 25 turnos, permisos `contents/actions/checks: read`, herramientas `Read,Grep,Glob,Bash(gh api|gh run view|git fetch|show|log)`;
   salida JSON validada por esquema (máx. 5 líneas). Lee `.claude/agents/forense.md` y su memoria de `main`.
3. `issue` (`issues: write`): abre «Forense 00 · run <id> · <causa>», sin duplicar (busca ese prefijo en los últimos 100 issues).
   No relanza, no publica, no toca PR.
4. Observaciones: la «solo lectura» descansa en el prompt y en los permisos del token (`gh api:*` admitiría POST si el token lo
   permitiera; hoy no). La deduplicación solo mira la primera página (100): fallará con más de 100 issues más recientes.

## 2. Dependencias por nombre

| Elemento | Depende de | Si se renombra / consolida |
|---|---|---|
| auto-merge | `name:` «Pruebas de la Plataforma» (lista `workflows:`), ruta `pruebas-plataforma.yml`, job `pruebas`, etiqueta `no-automerge`, secretos `DDD_REGISTRO_APP_*`, app ddd-registro (bypass del ruleset), rama `main`, `herramientas/decidir_auto_merge.py`, `tests/test_auto_merge.py` | Renombrar el `name:` de pruebas o el job `pruebas` deja de disparar o de encontrar el check: **no fusiona nada** (falla en silencio). Renombrar la etiqueta quita el freno de las PR `no-automerge`. Mover el fichero rompe la condición de `path`. |
| forense | `name:` «00 Ejecución Completa del Proyecto», `CLAUDE_CODE_OAUTH_TOKEN`, `.claude/agents/forense.md` y memoria, prefijo del título del issue, jobs `diagnosticar`/`issue` (fijados en `tests/test_agentes_ci.py`) | Renombrar la 00 apaga el forense sin error. Cambiar el prefijo del título duplica issues. |
| skills/CLAUDE.md | `no-automerge` en implementador/operador/coordinador; «Numeración del Registro» y catálogo se disparan por el push que hace la app | Renombrar `no-automerge` exige tocar las tres skills. |
| ruleset `proteger-main` | contexto requerido y bypass del administrador y de la app | Un cambio de nombre del job requerido bloquea toda PR no exenta. |

Lección ya registrada: renombrar `name:` referenciado en `workflow_run` rompe el disparo; hacer grep en `workflows:` antes.

## 3. ¿Se fusionó algo sin CI verde desde el 07-11?

Criterio: `pruebas` del HEAD fusionado (check-runs del SHA exacto) y de la fusión resultante en `main`. Universo: 96 PR
fusionadas (61 por `ddd-registro[bot]`, 35 por `jfmurciego`). Lista completa en el CSV.

| PR | Fusionada por | Fecha (UTC) | `pruebas` en el HEAD | `pruebas` en `main` tras la fusión | Nota |
|---|---|---|---|---|---|
| 538 | propietario | 11-08 16:53:19 | success, pero terminó 16:54:15 (**después**) | success | `no-automerge`; fusión manual antes de acabar la CI |
| 625 | propietario | 11-10 06:30:37 | success, terminó 06:32:01 (**después**) | success | fusión manual 1,5 min antes |
| 539 | propietario | 11-08 17:32:29 | success (16:49) | **failure** | `no-automerge`; HEAD verde, `main` rojo |
| 617 | bot | 11-10 01:27:53 | success (01:26:50) | **failure** | HEAD verde, `main` rojo |
| 631 | bot | 11-10 08:46:14 | success (08:45:50) | sin check al consultar | pendiente |
| 624 | bot | 11-10 06:29:28 | success sobre `1229ea2` (06:29:00) | success | ver abajo |

- Fusiones del bot sin `pruebas` verde en el HEAD: **ninguna** (61/61 con success completado antes). Ninguna llevaba `no-automerge`
  (las 20 con esa etiqueta las fusionó el propietario).
- Límite: no puedo reconstruir el estado borrador/lista en el instante de fusión; el filtro `draft` actúa en el momento de la
  decisión y no consta histórico.
- `main` previo a la fusión: solo comprobable desde 11-09 21:41 (la paginación de runs se cortó por el proxy). En esa ventana
  solo #597 (propietario, 00:22:08) se fusionó con el último run completado de `main` en failure.

### Caso #624
Creada 06:21:55 con un único commit `1229ea2` (06:21:40); el revisor comentó 06:23:06 `PASS_WITH_EXCEPTIONS` para ese SHA; `pruebas`
success 06:29:00; fusión por el bot 06:29:28 (28 s). No hay revisión ni comentarios humanos en la PR. Las correcciones de la revisión
final (y la parte B de la competición) llegaron después en #628 y #631. El mecanismo hizo lo que está diseñado (HEAD exacto
con `pruebas` verde), pero **ese diseño no incluye esperar a la revisión humana**: «lista para revisar» equivale a «se fusionará
en cuanto pase la CI».

## 4. Consolidar en un único workflow auxiliar

Qué cambiaría: un fichero con `on.workflow_run.workflows: [Pruebas…, 00 …]` y dos jobs filtrados por `github.event.workflow_run.name`.
- Ahorro real: ninguno en minutos (los jobs omitidos no facturan); en la lista de Actions, un solo nombre en lugar de dos.
- Riesgos: (a) la lógica de fusión (con secretos de escritura de la app) quedaría junto a la de un agente LLM con otro secreto;
  (b) `permissions`, `concurrency` y `if` pasan a ser por job y es fácil cruzarlos (el forense usa `queue: max` por run, la fusión
  `cancel-in-progress` por SHA); (c) un fallo del forense marcaría en rojo el mismo workflow que fusiona; (d) los tests actuales
  (`test_auto_merge`, `test_agentes_ci`, diseño A) fijan ficheros y nombres: habría que reescribirlos; (e) `workflow_run` ejecuta
  siempre la versión de `main`: no se prueba en la PR (lección #458); (f) cada finalización de cualquiera de las dos dispararía el
  workflow entero y la mayoría de ejecuciones saldrían con todos los jobs omitidos.
- Conclusión: no compensa; si se quiere, hacerlo solo con la fusión y el revisor, nunca con el forense.

## 5. Recomendaciones

1. **Exigir HEAD revisado** en `decidir_auto_merge.py`: comentario `<!-- ddd-revisor -->` con el HEAD completo y veredicto
   `PASS`/`PASS_WITH_EXCEPTIONS` (si el revisor está activo); `FAIL` o veredicto de otro SHA → NO. Hoy un FAIL del revisor no frena.
2. **Fusión por consentimiento**: etiqueta de aceptación (p. ej. `automerge`) en vez de «todo lo que no sea borrador»; o retraso
   mínimo (p. ej. 15 min desde el último push) para dar margen a correcciones. Mientras tanto, abrir en borrador toda PR que vaya
   a recibir correcciones y quitar el borrador solo al terminar.
3. **Exigir `main` en verde** (último run completado de `pruebas-plataforma` en `main` = success) antes de fusionar, tal como fija
   la regla del propietario; hoy el automatismo no lo comprueba.
4. **Verificar el ruleset**: confirmar si el contexto requerido es `veredicto` o `pruebas`; si debe ser `pruebas`, corregirlo (el
   administrador del repo; no es cambio de workflow) y valorar quitar el bypass del rol administrador para que las fusiones manuales
   también esperen a la CI (#538 y #625).
5. Fusión manual: no fusionar mientras `pruebas` esté en curso; el propietario puede usar `gh pr merge --match-head-commit`.
6. Forense: paginar la búsqueda de duplicados, filtrar por `workflow_run.id` en el título completo y considerar `timed_out`.
7. No consolidar ni renombrar sin grep previo de `workflows:`, `name:` de jobs y etiquetas (tabla de §2).
