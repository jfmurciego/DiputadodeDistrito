<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Gobierno de agentes en runtime (allowlist por rol y revisor obligatorio)
FECHA: 2026-11-07
ESTADO: candidato
CAMBIOS: T-78. Allowlist de herramientas por rol aplicada por configuración (hook `rol_herramientas.py`,
  frontmatter de subagentes, deny en `.claude/settings.json`) y JSON del ruleset para exigir el Revisor.
MOTIVO: que la autoridad de cada rol no dependa solo de la instrucción del prompt.
ANTERIOR: ninguna (fichero nuevo)
-->

# Gobierno de agentes en runtime (T-78)

## 1. Qué se aplica por configuración

| Rol | Mecanismo | Efecto |
|---|---|---|
| Revisor, forense (subagentes) | `tools: Read, Grep, Glob, Bash` y `disallowedTools` en `.claude/agents/*.md` | Edit/Write/NotebookEdit/Agent no existen para el subagente |
| Revisor, forense (subagentes) | Hook global `.claude/hooks/rol_herramientas.py` (matcher `*`), rol por `agent_type` del hook | Bash solo de lectura (git diff/show/log…, `gh api` GET, `gh pr/run/issue view`, cat/grep/jq…); sin redirección a fichero, `tee`, `sed -i`, `find -delete/-exec`, python ni curl; MCP solo `get_/list_/read/search` |
| Revisor en CI | `--allowedTools` de `pruebas-plataforma.yml` (jobs `comprobar`/`revisar`/`veredicto`) (sin cambios) | Solo Read/Grep/Glob y `git diff/show/log`, `gh pr diff/view` |
| Operador | Mismo hook con `DDD_ROL=operador` en el entorno de su sesión | Edit/Write/NotebookEdit bloqueadas; Bash libre (lanza con `gh api -X POST …/dispatches`) |
| Todos | `permissions.deny` de `.claude/settings.json` | `mcp__github__create_repository`, `mcp__github__fork_repository` |
| Todos | `guardia_git.py` (ya existía) | Sin push forzado ni commit con marcas de conflicto |

T-78 no añade ningún `allow`: no amplía permisos de nadie.

### Pruebas
- `tests/test_t78_rol_herramientas.py`: 30+ casos de herramientas y comandos denegados y permitidos, rol por
  `agent_type`, operador por `DDD_ROL` y cableado de `settings.json` y frontmatter.
- Runtime real (Claude Code 2.1.319, 2026-11-07), `claude -p` con un subagente `revisor` al que se pidió
  `git commit --allow-empty`: el commit no se hizo y la herramienta devolvió
  `Bloqueado por rol_herramientas.py: Bash denegado al rol solo-lectura: git commit no es de lectura.`
- Runtime real, `DDD_ROL=operador claude -p` pidiendo Write: `PreToolUse:Write hook error: … Write denegada al
  Operador: no edita código ni el plan.`; el fichero no se creó.
- Hallazgo: los `hooks` del frontmatter de un subagente **no se dispararon** en 2.1.319 (el commit se hizo); por eso
  el hook va en `settings.json` y distingue el rol por `agent_type`, que el hook global sí recibe.

## 2. Qué no se puede restringir (y por qué)

- **Rol de una sesión principal.** Claude Code no sabe qué rol (skill) tiene un chat: el Coordinador, el planificador
  y los implementadores comparten `settings.json`. Lo único que distingue sesiones es su entorno: para el Operador,
  un entorno propio con la variable `DDD_ROL=operador` (lo crea el propietario; las variables se aplican al
  arrancar la sesión). Sin esa variable, el hook no restringe al Operador.
- **Bash del Operador.** Necesita `gh api -X POST` para lanzar; un Bash general puede escribir ficheros
  (`echo > f`). Se bloquean las herramientas de edición, no la shell.
- **Solo-lectura no es estanqueidad.** La lista de Bash es una allowlist por programa; un comando permitido con
  efectos raros (p. ej. `git fetch` escribe en `.git`) pasa. No sustituye a la revisión humana de la fusión.
- **Subagentes de otro tipo** (`general-purpose`, `Explore`, `Plan`) no heredan la restricción: no son roles de DDD.
- **`create_session`.** `permission_mode` y `extra_allowed_tools` solo pueden ser iguales o más restrictivos que los
  de la sesión que crea; para lanzar un Operador: `permission_mode: "default"` y sin `extra_allowed_tools`, en el
  entorno con `DDD_ROL=operador`. No hay campo para restringir herramientas por sesión creada.
- **Auto mode / bypassPermissions** no saltan los hooks PreToolUse (salida 2 bloquea siempre), pero sí la lista
  `deny` si alguien la quita del fichero: cambios en `.claude/settings.json` deben pasar por PR.

## 3. Revisor como check obligatorio (lo aplica el propietario)

Condición cumplida: `Revisor de PR` con los jobs `comprobar`, `revisar` y `veredicto` en success en 7 PR seguidas
con el secreto nuevo (runs 42411501421 `lecciones-ola1`, 42411675947 `t64-estudio-comarcas`, 42412425313
`reaplica-t64-462`, 42413110535 `t72-archivo-origen`, 42414366508 `t74-catalogo-procedencia`, 42414447056
`t75-metaagente`, 42414448091 `plan-ola-0711n`). El check se publica como `veredicto` de la app GitHub Actions
(`integration_id` 15368); ningún otro workflow tiene un job con ese nombre.

Cambio del ruleset `proteger-main` (id 26311854): añadir `veredicto` a `required_status_checks`, sin tocar lo demás.
En Settings → Rules → Rulesets → proteger-main → «Require status checks to pass» → añadir `veredicto` (GitHub
Actions). Equivalente por API (lo ejecuta el propietario, no un agente):

```json
{
  "name": "proteger-main",
  "target": "branch",
  "enforcement": "active",
  "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
  "bypass_actors": [
    {"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"},
    {"actor_id": 5568103, "actor_type": "Integration", "bypass_mode": "always"}
  ],
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {"type": "required_status_checks",
     "parameters": {
       "strict_required_status_checks_policy": false,
       "do_not_enforce_on_create": false,
       "required_status_checks": [{"context": "veredicto", "integration_id": 15368}]
     }}
  ]
}
```

`gh api -X PUT repos/jfmurciego/DiputadodeDistrito/rulesets/26311854 --input ruleset.json` (cuerpo completo,
copiado del ruleset vigente del 2026-11-07; solo cambia `required_status_checks`).

### Verificación después de aplicarlo
1. `gh api repos/jfmurciego/DiputadodeDistrito/rulesets/26311854 -q '.rules[]|select(.type=="required_status_checks")|.parameters.required_status_checks'`
   devuelve `[{"context":"veredicto","integration_id":15368}]`.
2. En la siguiente PR, `gh api repos/jfmurciego/DiputadodeDistrito/commits/<head>/check-runs -q '.check_runs[]|select(.name=="veredicto")|.conclusion'`
   y la PR no es fusionable hasta que `veredicto` termine.

### Límites que conviene saber
- `veredicto` solo falla con `FAIL`; `PASS_WITH_EXCEPTIONS` y `BLOCKED` pasan.
- En borrador, PR de fork o sin secreto, `revisar` y `veredicto` se saltan; GitHub cuenta un check saltado como
  cumplido. Al pasar a lista (`ready_for_review`) el workflow corre y el check se exige.
- `bypass_actors` (rol admin y la app 5568103) pueden fusionar sin el check. `auto-merge.yml` solo mira `pruebas`:
  si fusiona con un actor en `bypass_actors`, el check no lo frena. Ampliar o quitar bypass es decisión del
  propietario.
