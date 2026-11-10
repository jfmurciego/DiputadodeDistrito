<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Fichas de roles y agentes y veredictos (metaagente v1.0 §4, §7)
FECHA: 2026-11-07
ESTADO: vigente (incorporado en skills por T-77)
CAMBIOS: T-77. Topes de coste por chat, ficha del ingeniero de motor, libro de costes de chats, estados en skills.
MOTIVO: incorporar los veredictos INCORPORAR de T-75.
ANTERIOR: legacy/2026-11-07_t77_fichas/FICHAS_AGENTES_v1.0.0.md
-->

# Fichas de roles y agentes de DDD

Fuente de cada dato: el fichero citado en `main` a 2026-11-07 (tras #471). **ND** = no definido hoy en ningún
fichero (hueco a cubrir). Separación §7: *rol* (skill o `.md`), *instancia* (sesión o job concreto) y *proceso*
(chat cloud o runner de Actions); una skill no es una instancia activa.

## 1. Chats con rol (sesiones de Claude Code)

Comunes a todos los chats, salvo que se diga otra cosa:
- Herramientas efectivas: las de la sesión cloud (lectura/escritura del repo, `gh api` REST, MCP GitHub y
  `claude-code-remote`); hook `guardia_git.py` bloquea commit con marcas de conflicto y `git push` forzado
  (`.claude/settings.json`). **No hay allowlist por rol**: la restricción es la instrucción de la skill.
- Recursos (topes por chat, T-77; al llegar al tope, parar y cerrar con la evidencia, sin ampliar por cuenta propia):
  propietario sin tope; planificador ~1 ola por chat; Coordinador, relevo al cambiar de ola; Operador, un lote autorizado;
  implementador, una tarea y dos ciclos de reparación por causa; ingeniero de motor, dos ciclos y luego estudio con
  presupuesto fijo. Libro de costes (`.claude/skills/presupuesto/SKILL.md`): una fila por agente, run y chat cerrado.
- Delegación: subagentes `revisor` y `forense`; profundidad y concurrencia **ND**.

| Ficha | Propietario | Planificador | Coordinador |
|---|---|---|---|
| Identidad | Humano (jfmurciego) | skill `planificador`; chat «DDD Plan» (session_01KQDtFsB1xxRnUwERbZc1pQ) | skill `coordinador`; session_01KQDtFrqVxd7Y6n1cvDtQy4 |
| Misión | Permisos y decisiones de criterio (suelo, techo, K, atomicidad, exenciones, publicar) | Qué y prioridades por olas; cola `T-xx` en `docs/PLAN.md` | Recibir cierres, seguir PR/CI/runs, tablero `docs/ESTADO.md`, lecciones |
| Exclusiones | — | Código, lanzar, seguir CI o chats | Código, lanzar, publicar, editar `PLAN.md`, fusionar o aprobar |
| Entrada | Propuestas con contexto mínimo | `PLAN.md`, `ESTADO.md`, FRAMEWORK §11–12, escalados del Coordinador | Líneas «T-xx · qué · PR · siguiente · bloqueo» |
| Salida | Decisión con fecha (`PLAN.md` §2) | Tarea con id, prioridad, alcance, dependencias, turno y criterio de hecho | `ESTADO.md`; una PR de lecciones |
| Autoridad | Aprueba entorno `produccion`; fusiona `no-automerge` | Órdenes de tarea y turno valen como del propietario (`CLAUDE.md`, delegación 07-11); no lanzar ni publicar | `archive_session` de chats terminados |
| Aceptación | — | **ND** criterio medible de una ola | **ND** beneficio medido (ver §5) |
| Recuperación | — | Cambios de criterio: consultar al propietario antes (caso T-64) | Escala al planificador solo decisiones y causas |

| Ficha | Operador | Implementador | Ingeniero de motor |
|---|---|---|---|
| Identidad | skill `operador` (+ `lanzar-00`, `publicar-visor`) | skill `implementador` | skill `ingeniero-motor` (modelo Opus, skill `presupuesto`) |
| Misión | Único que lanza y publica | Una tarea, una PR | M04, M05 y GerryChain en local, una PR por causa (FRAMEWORK §6) |
| Exclusiones | Código, contratos, política, `PLAN.md`; fusionar PR sin `no-automerge` | Lanzar, publicar, fusionar; ficheros compartidos sin turno | Lanzar; cambiar suelo, techo, K o atomicidad sin decisión |
| Entrada | Permiso del propietario en su chat, por lote | Tarea `T-xx` de `PLAN.md` | Tarea con evidencia de run (`diagnostico/*`) |
| Salida | Línea por run «territorio · run · resultado · paso/causa · siguiente» | PR con entrada en `docs/registro/` y línea de cierre | PR + modo de 00 necesario (`.claude/rules/huellas.md`) |
| Autoridad | `dispatches` REST; el efecto espera en `produccion` hasta el Approve del propietario | Rama y PR | Igual que implementador |
| Aceptación | Run identificado por `TERRITORY:` | Guardián y R015 verdes; test rojo→verde | Motor real en local (`.claude/rules/diagnostico-local.md`) |
| Recuperación | Tras fallo, no relanzar: `diagnosticar-run` | Dos ciclos de reparación por causa | Dos ciclos; luego estudio con presupuesto fijo (FRAMEWORK §11) |

## 2. Subagentes y robots

| Ficha | Revisor | Forense |
|---|---|---|
| Identidad | `.claude/agents/revisor.md`; en CI `pruebas-plataforma.yml` (jobs `comprobar`/`revisar`/`veredicto`, desde la 1.7.0; antes `revisor-pr.yml` 1.0.1) | `.claude/agents/forense.md` + `.claude/agent-memory/forense/MEMORY.md`; en CI `forense-00.yml` 1.0.0 |
| Misión | Veredicto JSON ligado al SHA del HEAD | Causa en cinco líneas con `causa_id` |
| Herramientas | Local: Read, Grep, Glob, Bash. CI: `Bash(git diff/show/log)`, `gh pr diff/view` | Local: Read, Grep, Glob, Bash. CI: `Bash(gh api:*)`, `gh run view`, `git fetch/show/log`; token `contents: read, actions: read` |
| Autoridad | Ninguna; el job `veredicto` falla con FAIL pero **no es check obligatorio** | Ninguna; el job siguiente abre issue (`issues: write`) |
| Recursos | Sonnet, `--max-turns 30`, 20 min | Sonnet, `--max-turns 25`, 15 min |
| Aceptación | Oro 23/24 (T-39) | Oro 20/20 (T-40) — `evals/oro/LIBRO_DE_COSTES.md` |
| Recuperación | Sin secreto `CLAUDE_CODE_OAUTH_TOKEN`, se salta limpio | Ídem |
| Límite | En local, `Bash` sin filtro: solo lectura por instrucción, no por runtime | Ídem; el oro mide causas conocidas, no nuevas (libro de costes) |

| Ficha | Auto-merge | Guardián | Archivista | Numeración |
|---|---|---|---|---|
| Fichero | `auto-merge.yml` 1.2.0 + `herramientas/decidir_auto_merge.py` | job `guardian` de `pruebas-plataforma.yml` + `herramientas/comprobar_guardian_main.py` | `archivar-artefactos-r2.yml` 1.0.0 | `numerar-registro.yml` 1.0.0 |
| Disparo | `workflow_run` de la CI | `push` y `pull_request` | cron diario 05:17 UTC y manual | `push` a `main` |
| Hace | Squash si `pruebas` del SHA y de esa suite está en success; fuera borradores y `no-automerge` | Marcas de conflicto, numeración del registro, R015 | Copia a R2 lo referenciado antes de 14 días; `orchestracion/archivo_r2.json` | Numera `docs/registro/` en `REGISTRO_DE_CAMBIOS.md` |
| Autoridad | Fusiona con la app de registro (exenta del ruleset) | Bloquea vía check `pruebas` | Escribe en `main` y R2 | Escribe en `main` |
| Recursos | 10 min | 10 min | 120 min | 10 min |
| Recuperación | Pendiente/failure: no hace nada | — | Reintentos exponenciales ante 5xx y 429 (T-47b, tras run 42393003447) | **ND** |
| Incidentes | 1.0.0 fusionó #453, #454 y #458 sin `pruebas` (T-54b #457, T-54c #460) | Rojo en `main` tras #458 (#459) | — | — |

## 3. Agentes del catálogo FRAMEWORK §6 no construidos

| Agente | Estado | Qué cubre hoy esa función |
|---|---|---|
| Agente de fuentes (P10) | no existe | `preparacion-fuentes.yml`, huellas sha256 de fuentes, espejo Infoelectoral (`CLAUDE.md`) |
| Analista electoral (P40) | no existe | `resultados-ligeros.yml`, T-53/T-55/T-56 (scripts de hemiciclo) |
| Redactor académico (P60) | no existe | nada; P60 sin empezar |

## 4. Estados y handoff

Propuesta en `ESTADOS_Y_HANDOFF.md`.

## 5. Veredictos (§4 del metaagente)

| Pieza | Veredicto | Motivo y evidencia |
|---|---|---|
| Enfoque mínimo (§3) | INCORPORAR | `ADR-001-enfoque.md` (este PR) |
| Criterio «sistema más pequeño» | YA CUBIERTO | FRAMEWORK §1, skills `presupuesto` y `disenar-agente` |
| Fichas §7 | INCORPORAR | Este documento; huecos ND: topes por chat, allowlist por rol |
| Ficha propia del ingeniero de motor | HECHO (T-77) | Skill `ingeniero-motor` |
| Estados de tarea §9.1 | HECHO en skills (T-77) | Columna de estado en la cola; `PLAN.md` lo aplica el planificador |
| Estados de efecto externo §9.3 y `UNKNOWN` | HECHO en skills (T-77) | Casos #462, #453, #454, #458 |
| Resultado de calidad §9.2 | YA CUBIERTO | Veredicto del revisor y forense (`.claude/agents/*.md`) |
| Handoff §23 | HECHO (T-77) | Línea de cierre ampliada en las skills; sin JSON |
| Tabla de madurez §25 | INCORPORAR | `MADUREZ.md` (este PR) |
| Aprobación ligada al HEAD (§11, §15) | YA CUBIERTO | `auto-merge.yml` 1.2.0; veredicto del revisor con SHA |
| Revisor como check obligatorio | CAMBIO ARQUITECTÓNICO | Hoy el ruleset solo exige `pruebas`; hacerlo obligatorio cambia la puerta de fusión y depende de un secreto |
| Allowlist de herramientas por rol en chats | CAMBIO ARQUITECTÓNICO | La restricción es por instrucción; aplicarla en runtime exige `settings.json` por rol o sesiones distintas |
| Controlador con leases y almacén de eventos (§10–§13) | YA CUBIERTO (descartado) | ADR-001; Actions + `PLAN.md` + registro |
| Coordinador | CAMBIO ARQUITECTÓNICO si no mide beneficio | Creado en #464 sin línea base; sin métrica de fusiones indebidas o tiempo de cierre por ola. Medir dos olas o fundir con el planificador |
| Agente de fuentes | YA CUBIERTO (no construir) | Lo mecánico está en workflows y huellas; sin caso que exija juicio |
| Analista electoral | YA CUBIERTO (no construir) | «Casi todo es un script» (FRAMEWORK §6); `resultados-ligeros.yml` |
| Redactor académico | INCORPORAR más adelante | Solo cuando arranque P60; hoy sin entrada |
| Libro de costes de chats | HECHO (T-77) | Skill `presupuesto`: una fila por chat cerrado |
