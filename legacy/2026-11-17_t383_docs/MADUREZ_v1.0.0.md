<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Tabla de madurez de agentes, roles y robots (metaagente v1.0 §25)
FECHA: 2026-11-07
ESTADO: candidato
CAMBIOS: T-75. Primera tabla diseñado/implementado/probado/verificado con evidencia por componente.
MOTIVO: aplicar el método del metaagente v1.0 sobre lo que existe (nivel N2).
ANTERIOR: ninguna (fichero nuevo)
-->

# Madurez de la arquitectura de agentes (a 2026-11-07, `main` tras #471)

Criterios (§25): **Diseñado** = responsabilidad y contrato escritos; **Implementado** = fichero ejecutable o
configuración en el repo; **Probado** = prueba identificable ejecutada; **Verificado** = criterios aplicables con
evidencia y revisión independiente o caso real. Un rol de chat se «implementa» con su skill; no hay runtime que la
haga cumplir (ver `FICHAS_AGENTES.md` §1).

| Componente | Diseñado | Implementado | Probado | Verificado | Evidencia / límite |
|---|---|---|---|---|---|
| Revisor (subagente) | Sí | Sí | Sí: oro 23/24 | Parcial | `evals/oro/LIBRO_DE_COSTES.md` (T-39); revisión real PR #425 (`evals/revisiones/`). Oro y memoria de las mismas fuentes |
| Revisor en CI | Sí | Sí | No | No | `revisor-pr.yml` 1.0.0; pendiente de que corra con el secreto actualizado (`docs/ESTADO.md`). No es check obligatorio |
| Forense (subagente) | Sí | Sí | Sí: oro 20/20 | Parcial | T-40 en el libro de costes; caso real T-58 hecho en línea, sin subagente. Mide causas conocidas, no nuevas |
| Forense en CI | Sí | Sí | No | No | `forense-00.yml` 1.0.0; sin issue de una 00 fallida citado como evidencia |
| Auto-merge | Sí | Sí (1.2.0) | Sí | Sí | `tests/test_auto_merge.py`; prueba real #465 (`pruebas` 20:16:54, fusión 20:17:25, `docs/ESTADO.md`). Incidentes 1.0.0: #453, #454, #458 |
| Guardián | Sí | Sí | Sí | Sí | `tests/test_comprobar_guardian_main.py`; job `guardian` en cada PR y push a `main` |
| Numeración del registro | Sí | Sí | Sí | Sí | `tests/test_numerar_registro.py`; commits «registro: numerar» en `main` (p. ej. 0db5aea) |
| Archivista R2 | Sí | Sí | Sí | Parcial | `tests/test_archivar_artefactos_r2.py`; run 42393003447 falló con HTTP 500 → T-47b. Sin run verde citado aquí |
| Métricas del proceso | Sí | Sí | Sí | Parcial | `tests/test_metricas_proceso.py` (T-65 #458); salida en `orchestracion/metricas_proceso.json`; sin línea base usada para decidir |
| Hook `guardia_git.py` | Sí | Sí | Parcial | No | `.claude/settings.json` (#428); sin test en `tests/` |
| Propietario | Sí | — | — | — | `CLAUDE.md` «Reglas del propietario»; aprobación en entorno `produccion` (T-41) |
| Planificador | Sí | Sí (skill) | No | Parcial | `.claude/skills/planificador/SKILL.md`; olas reales del 07-11 (`PLAN.md` 1.0.15). Sin criterio de éxito por ola |
| Coordinador | Sí | Sí (skill) | No | No | #464; tablero `docs/ESTADO.md`. **Sin beneficio medido** (ADR-001) |
| Operador | Sí | Sí (skill) | Parcial | Parcial | Runs del 07-11 con aprobación en `produccion` (`docs/ESTADO.md`); caso #462 mostró que la regla de «en pausa» faltaba (añadida en la skill) |
| Implementador | Sí | Sí (skill) | Parcial | Parcial | PR de T-47…T-72 con entrada en `docs/registro/`; reglas guardián y R015 en CI |
| Ingeniero de motor | Parcial | No | No | No | Solo en FRAMEWORK §6 y skill `presupuesto` (Opus); sin skill ni ficha propia |
| Agente de fuentes | Parcial | No | No | No | FRAMEWORK §6; no construir (`FICHAS_AGENTES.md` §5) |
| Analista electoral | Parcial | No | No | No | FRAMEWORK §6; cubierto por scripts (`resultados-ligeros.yml`) |
| Redactor académico | Parcial | No | No | No | FRAMEWORK §6; P60 sin empezar |
| Estados §9 y handoff §23 | Sí (propuesta) | No | No | No | `ESTADOS_Y_HANDOFF.md` (este PR) |
| Libro de costes | Sí | Parcial | — | Parcial | `evals/oro/LIBRO_DE_COSTES.md`: agentes con tokens; chats sin medir |

Resultado global para el alcance «arquitectura de agentes de DDD»: **PASS_WITH_EXCEPTIONS**. Excepciones: revisor y
forense en CI sin verificar en real; Coordinador sin beneficio medido; estados de tarea y efecto sin adoptar;
coste de chats sin medir.
