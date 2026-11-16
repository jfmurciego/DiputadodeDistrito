# T-374 · ¿Se puede meter el Revisor de PR dentro de P90 Automático?

Documento de decisión para el propietario. Solo diseño: no cambia ningún workflow. Fecha: 2026-11-16.

## 1. Resumen (30 segundos)

- **Hoy** el Revisor de PR (`revisor-pr.yml`) está aparte, como excepción de D-135.
- **Hallazgo previo a leer nada más:** el ruleset activo `proteger-main` (leído con la API, solo lectura) exige **un único check: `veredicto`**
  (el del Revisor). **No exige `pruebas`.** `pruebas` solo lo lee la fusión automática (`auto-merge.yml`). El encargo y la nota de D-135 hablan
  del ruleset exigiendo `pruebas`; en la práctica el riesgo es otro (ver §3).
- **Recomendación:** opción A (dejar el Revisor aparte) y cerrar T-374 como «excepción permanente». Las demás opciones o cuestan más de lo que ahorran
  (un fichero menos) o no se pueden verificar sin hacer pruebas reales en la rama `main`.

## 2. Qué está en juego (hechos del repositorio)

| Dato | Fuente |
|---|---|
| El ruleset `proteger-main` exige solo el check `veredicto`; admin y la app de registro lo esquivan. Otro ruleset («Restrict Deletions») está desactivado. `branches/main/protection`: 404 (no hay protección clásica). | `gh api repos/…/rulesets/26311854` |
| El Revisor corre solo con la etiqueta `revisar-ia`. Ya se dispara en `opened, synchronize, reopened, ready_for_review, labeled`; el `if` del primer job lo salta en las demás. Si se salta, `veredicto` queda *skipped*, que cuenta como cumplido. | `revisor-pr.yml` 1.1.0 |
| P90 define el check `pruebas` (job agregador) y escucha `pull_request` sin `types` (= opened, synchronize, reopened). `pruebas` solo corre en esos tres. | `p90-automatico.yml` 1.0.0 |
| La fusión automática se dispara al terminar P90 en una PR, y solo fusiona si el último check-run `pruebas` **de la suite de ese run** está en `success`; `skipped` o ausente = no fusiona. Respeta `no-automerge`. | `auto-merge.yml` 1.3.0, `decidir_auto_merge.py` |

## 3. El problema, bien dicho

Para que el Revisor viva dentro de P90, P90 tendría que escuchar también `labeled` y `ready_for_review` (el Revisor los necesita: se pone la
etiqueta o se saca del borrador y debe arrancar). Entonces, en esos eventos, P90 arranca entero y todos sus jobs se saltan por su `if`, salvo el del
Revisor. Cada job saltado deja un check-run con resultado *skipped*; en particular `pruebas`.

Qué daño real puede hacer ese `pruebas` *skipped*:

1. **Sobre el ruleset: ninguno directo**, porque no exige `pruebas`. Sí cuenta *skipped* como cumplido (§4), y eso ya ocurre hoy con `veredicto`
   (por diseño, T-293).
2. **Sobre la fusión automática: ninguno si no se toca `decidir_auto_merge.py`.** Solo acepta `success` dentro de su suite. Un `skipped` da «NO».
3. **Sobre las personas y los informes** («main en verde», el Coordinador, el tablero): sí confunde. Un HEAD puede mostrar un `pruebas` verde de
   la ejecución buena y otro `pruebas` *skipped* más reciente de la ejecución por etiqueta. Qué muestra la interfaz de GitHub «el último por nombre»
   no he podido verificarlo en la documentación.
4. **Riesgo grave solo si alguien «arregla» el punto 3 haciendo que `pruebas` se ponga en `success` en el evento de etiqueta** (por ejemplo copiando el resultado
   anterior): entonces la fusión automática vería `success` en la suite de la etiqueta y fusionaría una PR cuya suite quizá sigue pendiente o fallida.
   Es el escenario que el revisor de #845 quería evitar. Cualquier diseño debe prohibirlo.

## 4. Lo que dice la documentación oficial de GitHub

Consultado el 2026-11-16 en `raw.githubusercontent.com/github/docs/main/content/…` (docs.github.com no resuelve desde la nube).

- **Checks obligatorios y *skipped*** — `repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches.md`:
  «Required status checks must have a `successful`, `skipped`, or `neutral` status before collaborators can make changes to a protected branch».
  Es la regla de ramas protegidas; la página equivalente de rulesets no la he podido localizar, así que **que el ruleset trate *skipped* igual
  lo doy por cierto por la nota previa de D-135, no por documentación**.
- **Filtros `types`** — `actions/reference/workflows-and-actions/events-that-trigger-workflows.md`, secciones `pull_request` y `pull_request_target`:
  sin `types`, solo `opened`, `synchronize` y `reopened`; las demás actividades (`labeled`, `ready_for_review`…) se activan con `types`. Los `types` son del
  **workflow entero**, no de un job: no se puede decir «`labeled` solo para este job». Lo único que se puede hacer por job es un `if`.
- **`if` a nivel de job** — `actions/reference/workflows-and-actions/workflow-syntax.md`, `jobs.<job_id>.if` (la página remite a un texto común que no
  he descargado). Un job con `if` falso no se ejecuta; qué check-run deja exactamente (*skipped*) lo confirma el comportamiento ya observado en
  este repositorio (`veredicto` hoy, y el hallazgo de #845), no la página que cito.
- **`pull_request_target`** — mismo fichero de eventos: se ejecuta en el contexto de la rama base/por defecto, «rather than in the context of the merge commit»,
  y tiene acceso a secretos; GitHub avisa «Avoid using this event if you need to build or run code from the pull request». Su `GITHUB_SHA` es el último
  commit de la rama por defecto (no el HEAD de la PR).
- **`workflow_run`** — mismo fichero: «is able to access secrets and write tokens, even if the previous workflow was not»; `GITHUB_SHA` = último commit de la rama por defecto;
  máximo tres niveles encadenados; solo reacciona a `completed`/`requested`/`in_progress` de otro workflow, no a etiquetas.
- **Workflows reutilizables** — `actions/reference/workflows-and-actions/reusing-workflow-configurations.md`: se llaman desde un job con `uses:`; los permisos
  de `GITHUB_TOKEN` solo pueden rebajarse; los runners se evalúan con el contexto del llamador; las variables `env` del llamador no se propagan.
  **No dice** cómo se llaman los check-runs de los jobs llamados (hay que probarlo).

## 5. Opciones

### A. Revisor fuera de P90, como hoy (excepción permanente)

- **Check-runs por evento.** `opened/synchronize/reopened`: P90 → `cambios`, `guardian`, `suite (n)`, `pruebas`…; Revisor → `comprobar` (success) y `revisar`/`veredicto` *skipped*.
  `labeled` con `revisar-ia` y `ready_for_review`: solo el Revisor trabaja. P90 no arranca: **no hay `pruebas` *skipped***.
- **Riesgo para el ruleset.** El que ya existe y está aceptado: `veredicto` *skipped* cuenta como cumplido salvo con `revisar-ia`.
- **Seguridad.** Sin cambios: `pull_request` del repositorio, `CLAUDE_CODE_OAUTH_TOKEN` solo en jobs con `if` de repo propio, no borrador y no Bot.
- **Coste / esfuerzo.** Cero. Un fichero más (`revisor-pr.yml`) además de `auto-merge.yml`; ya son las dos excepciones de P90.
- **Contra.** No cumple del todo D-129 («uno por familia»).

### B. Job `veredicto` dentro de P90 con `types` ampliados

- **Check-runs por evento.**
  - `opened/synchronize/reopened`: igual que hoy más `veredicto` *skipped* (si no hay etiqueta).
  - `labeled` / `ready_for_review`: **sale un `pruebas` *skipped*** (más `guardian`, `suite`, etc. *skipped*) y el `veredicto` real. Además se genera un
    run de P90 que, al terminar, dispara `auto-merge.yml` (que no fusiona, ver §3.2, pero gasta un job y deja un aviso).
- **Riesgo para el ruleset.** Sin riesgo nuevo en el ruleset (no exige `pruebas`). Sí riesgo de lectura humana (§3.3) y el riesgo grave si alguien
  convierte el `pruebas` del evento de etiqueta en `success` (§3.4).
- **Variante B2 (descartada).** Hacer que `pruebas` en `labeled` copie el resultado del HEAD anterior. Si copia `success`, la fusión automática fusiona al poner
  cualquier etiqueta distinta de `no-automerge`; si la suite estaba pendiente y se copia «success por defecto», fusiona sin suite. Inaceptable.
- **Seguridad.** Igual que A (mismo `pull_request`). Hay que reimplementar el `if` del Revisor dentro de un workflow que además tiene jobs con permisos de escritura
  y concurrencia propia por PR (`ddd-pr-N-pruebas` con `cancel-in-progress`).
- **Coste / esfuerzo.** Medio: tests de P90 (`test_workflow_safety` y los que fijan el `if` de jobs), más una PR de workflow con revisor independiente. Ahorro: un fichero.
- **Contra.** Resucita justo el hallazgo de #845 y confunde `pruebas` en el tablero.

### C. Disparar el Revisor por otra vía

- **C1 · `workflow_run` de P90.** El Revisor arrancaría al *terminar* P90. Pero P90 no corre con `labeled`, así que poner la etiqueta **no lanzaría nada**: se perdería «a demanda».
  Además `GITHUB_SHA` es el de `main`, no el de la PR; el check `veredicto` no quedaría sobre el HEAD de la PR y el ruleset lo esperaría para siempre
  (o habría que crearlo a mano por API). No viable sin un diseño nuevo de checks por API.
- **C2 · `pull_request_target` solo con `labeled`.** Se ejecuta con el código del Revisor de `main` y con secretos, pero el Revisor necesita **leer y ejecutar herramientas sobre el contenido de la PR**
  (checkout del HEAD, `gh pr diff`, un modelo con Bash). GitHub avisa de no usarlo para ejecutar código de la PR. El diff es contenido no fiable (inyección de instrucciones en el texto leído por el
  modelo) con un token de pago en el contexto. Además D-135 ya descartó `pull_request_target` para fusionar. Sin forks la superficie baja, pero el check queda también atado a `main`
  (misma duda del check sobre el HEAD que en C1, no verificada).
- **Check-runs / ruleset / seguridad / coste.** C1: `veredicto` fuera del HEAD de la PR → bloquea todas las PR (o exige tocar el ruleset). C2: seguridad peor que hoy y sin garantía de adjuntarse al HEAD.
  Esfuerzo alto en ambas, ahorro nulo. **Descartada.**

### D. Revisor como workflow reutilizable llamado desde P90

- **Check-runs por evento.** El llamador sería un job de P90 (`veredicto`) con `uses: ./.github/workflows/revisor-reutilizable.yml`. Los eventos son los de P90
  (hay que ampliar `types` igual que en B), así que el `pruebas` *skipped* aparece exactamente igual que en B.
- **Riesgo para el ruleset.** Los mismos de B, más uno propio: los jobs llamados suelen mostrarse en la interfaz como «llamador / llamado»; el check exigido se llama
  `veredicto` a secas. Si el nombre cambia, el ruleset no lo reconoce: o bloquea (pendiente para siempre) o, peor, queda sin check obligatorio. La documentación citada no lo aclara;
  habría que probarlo en una PR real y, si cambia, el propietario tendría que editar el ruleset.
- **Seguridad.** Los permisos solo se rebajan y los secretos hay que pasarlos explícitos o con `secrets: inherit`; un fallo ahí deja al revisor sin token o con demasiado.
- **Coste / esfuerzo.** Alto: fichero reutilizable nuevo, cambio de P90, tests, posible cambio del ruleset por el propietario. Ahorro: ninguno (sigue habiendo un fichero).
- **Contra.** Suma los problemas de B y añade el de los nombres. **Descartada.**

## 6. Comparación

| | A. Aparte (hoy) | B. Job en P90 | C. Otra vía | D. Reutilizable |
|---|---|---|---|---|
| `pruebas` *skipped* en `labeled`/`ready_for_review` | No | **Sí** | No (pero otros fallos) | **Sí** |
| Cambia el ruleset | No | No | Posible | Posible |
| Riesgo de fusionar con suite pendiente | No | Solo si se «arregla» mal | No | Solo si se «arregla» mal |
| Seguridad frente a hoy | Igual | Igual | Peor (C2) / sin check (C1) | Igual, más delicado |
| Esfuerzo | 0 | Medio | Alto | Alto |
| Ahorro | 0 | 1 fichero | 0 | 0 |
| Verificable con documentación | Sí | Parcial | Parcial | No (nombres de checks) |

## 7. Lo que no he podido verificar (para no darlo por hecho)

1. Que el ruleset trate *skipped* como cumplido: la documentación de ramas protegidas lo dice; la de rulesets no la localicé. Lo avala D-135 y el comportamiento de `veredicto`.
2. Qué `pruebas` muestra la interfaz cuando hay uno *success* y otro *skipped* sobre el mismo HEAD.
3. Cómo se nombran los check-runs de un workflow reutilizable llamado.
4. Si un check creado por `pull_request_target` / `workflow_run` aparece sobre el HEAD de la PR (la documentación solo dice que su SHA es el de la rama por defecto).
Cualquiera de los cuatro exigiría una PR de prueba real; no se ha lanzado nada.

## 8. Recomendación y decisión que se pide

**Recomiendo A.** El ahorro de B/D es un fichero; su coste es reabrir el hueco que encontró el revisor de #845 y tocar un check que protege `main`. C no es seguro.

**Decisión concreta para el propietario (una frase):**
«T-374 se cierra: `revisor-pr.yml` queda como excepción permanente aparte, igual que `auto-merge.yml` (D-135)».
Si prefiere B, necesito además que autorice una PR de ensayo con `no-automerge` para comprobar los puntos 2 y 3 del §7, y que apruebe que `decidir_auto_merge.py` no se toque.

Acción de seguimiento (cero código, si se elige A): corregir la nota de `.claude/rules/workflows.md` y de D-135 que dicen que el ruleset exige `pruebas`: exige `veredicto`.
