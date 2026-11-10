<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: ADR-001 — Enfoque de agentes de DDD
FECHA: 2026-11-07
ESTADO: candidato (decisión PROPUESTA)
CAMBIOS: T-75. Primera aplicación del método del metaagente v1.0 (§3, §27) a DDD.
MOTIVO: el metaagente solo se usaba como referencia; faltaba el ADR del enfoque.
ANTERIOR: ninguna (fichero nuevo)
-->

# ADR-001 — Workflow determinista con pasos LLM y chats con rol

Estado: **PROPUESTO** (lo acepta el propietario). Fecha: 2026-11-07.
Ámbito y responsable: organización de agentes, chats y CI de DDD; decide el propietario, propone el planificador.
Baseline afectada: `docs/ARQUITECTURA/FRAMEWORK_AGENTES_Y_ESTRUCTURA.md` 1.0.0 (§1 principios, §6 capas).
Requisitos / riesgos: producción reproducible y con procedencia; humano en lo irreversible (lanzar, fusionar,
publicar); coste medido (`.claude/skills/presupuesto/SKILL.md`); riesgo de fusiones sin CI (#453, #454, #458) y de
fusión de una PR en pausa (#462).

## Problema

DDD ya funciona con CI, skills, dos subagentes y varios chats con rol, pero la elección se hizo por acumulación
(FRAMEWORK §6 y §12), sin ADR. El metaagente (§3) exige justificar el enfoque, las alternativas y la condición
para reconsiderarlo, y que cada agente adicional tenga un beneficio comprobable.

## Opciones (§3 del metaagente)

| Enfoque | Encaje en DDD | Evidencia |
|---|---|---|
| A. Proceso determinista sin LLM | Toda la producción (M01–M08, puertas, publicación) y los robots de CI | `.github/workflows/ejecucion-completa-proyecto.yml`, `pruebas-plataforma.yml`, `numerar-registro.yml` |
| B. Una llamada estructurada a un LLM | Revisor y forense en CI: entrada fija, salida JSON, sin ciclo largo | `pruebas-plataforma.yml` (jobs `comprobar`/`revisar`/`veredicto`) 1.0.0, `forense-00.yml` 1.0.0 |
| C. Un agente con herramientas | Implementador e ingeniero de motor: una tarea, una PR | skill `implementador` |
| D. Workflow determinista con pasos LLM | **Elegido como marco**: Actions es el control; los LLM solo juzgan (revisar, diagnosticar, implementar) | FRAMEWORK §1 principio 3 |
| E. Supervisor con especialistas | Planificador → Coordinador → Operador → implementadores, coordinados por `send_message` | skills `planificador`, `coordinador`, `operador`; `CLAUDE.md` «Coordinación» |
| F. Sistema dirigido por eventos | Solo donde ya hay eventos de GitHub: `workflow_run` (auto-merge, forense), `push` (numeración), `schedule` (archivista, métricas) | cabeceras de esos workflows |

## Decisión

**D**, con A como capa por defecto, B para revisión y diagnóstico aislados, C para cada tarea y una E mínima de
chats con rol. F solo sobre eventos nativos de GitHub, sin almacén de eventos propio.

Razones:
1. Las invariantes (población, contigüidad, huellas, gobernanza) ya son código determinista y tests; un LLM no
   debe evaluarlas (metaagente §4, plano de control).
2. Los efectos irreversibles ya pasan por controles fuera del modelo: entorno `produccion` con revisor requerido
   (skill `operador` paso 3), ruleset `proteger-main` que exige `pruebas` (cabecera de `pruebas-plataforma.yml` (jobs `comprobar`/`revisar`/`veredicto`)) y hook
   `guardia_git.py`.
3. Revisor y forense justifican su separación con beneficio medido: 23/24 y 20/20 en el conjunto de oro
   (`evals/oro/LIBRO_DE_COSTES.md`).

Supuestos: un único propietario humano; repositorio público (minutos de Actions sin coste,
`CLAUDE.md` «Ejecución 00»); sesiones cloud sin estado entre turnos.

## Descartes

- Controlador propio con *leases*, ocho esquemas JSON y almacén de eventos (metaagente §10–§13): coste de
  operación sin requisito que lo exija; Actions, `PLAN.md` y el registro cubren el estado (FRAMEWORK §7).
- Cargar el metaagente como instrucciones de sistema: coste fijo por chat (FRAMEWORK §7).
- AI Control Plane de cuatro agentes (FRAMEWORK §4): duplica roles existentes.
- Más especialistas del catálogo §6 sin caso medido (fuentes, analista electoral, redactor académico): ver
  `FICHAS_AGENTES.md` §3.

## Consecuencias

- Beneficios: lo mecánico no gasta modelo; la revisión es independiente del autor; el humano aprueba fuera del chat.
- Coste: cada chat con rol es caro (FRAMEWORK §6) y los handoffs entre chats pierden contexto: casos #462
  (fusionada estando en pausa, revertida en #467 y reaplicada en #470) y #453/#454/#458 (fusionadas sin CI por el
  auto-merge 1.0.0; arreglado en T-54b #457 y T-54c #460).
- Límite: el estado de tarea vive en texto (`PLAN.md`, `docs/ESTADO.md`) sin estados formales ni transiciones
  validadas; ver propuesta en `FICHAS_AGENTES.md` §4.

## Compatibilidad y transición

No cambia código, workflows, skills ni `PLAN.md`. Las propuestas de `FICHAS_AGENTES.md` §4–§5 y `MADUREZ.md` son
incrementales y se adoptan por PR propia si el planificador las encarga.

## Validación y reconsideración

Se comprueba con `docs/ARQUITECTURA/MADUREZ.md` y las métricas de `orchestracion/metricas_proceso.json`
(`metricas-proceso.yml`). Reconsiderar si:
- la capa E (Coordinador y planificador como chats separados) no muestra beneficio medido en dos olas: menos
  fusiones indebidas o menos tiempo de cierre por tarea frente a la semana del 02 al 07-11;
- hay un segundo caso de efecto externo `UNKNOWN` no reconciliado (como #462): entonces formalizar estados (§9) en
  un fichero de máquina en vez de texto;
- aparece un segundo operador o trabajo concurrente sobre el núcleo compartido: entonces hace falta exclusión real
  (metaagente §10), no solo turnos en `PLAN.md`.

## Trazabilidad

| Requisito | Decisión | Componente | Prueba/gate | Evidencia | Estado |
|---|---|---|---|---|---|
| Humano en lo irreversible | ADR-001 | entorno `produccion`, `no-automerge` | aprobación en GitHub | skill `operador` §3; caso #462 | PASS_WITH_EXCEPTIONS (#462) |
| Fusión solo con CI verde | ADR-001 | `auto-merge.yml` 1.2.0 | check-run `pruebas` del SHA | #457, #460; prueba #465 | PASS desde 1.2.0 |
| Quien construye no certifica | ADR-001 | `revisor`, `pruebas-plataforma.yml` (jobs `comprobar`/`revisar`/`veredicto`) | oro 23/24 | `evals/oro/LIBRO_DE_COSTES.md` | PASS (oro); en CI pendiente de secreto (`docs/ESTADO.md`) |
| Coste medido | ADR-001 | skill `presupuesto`, `metricas-proceso.yml` | libro de costes | `evals/oro/LIBRO_DE_COSTES.md` | parcial: chats sin medir |
