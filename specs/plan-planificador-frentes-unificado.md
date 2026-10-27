# Plan: Planificador unificado de frentes DDD

## Metadata
prompt: `dame una alternativa de planificador para sacar este proyecto adelante`
issue: `N/A`
created: `2026-10-27`
task_type: feature
complexity: complex

## Task Description
El único planificador del proyecto, `ddd_core/national_campaign_planner.py`, solo mira el registro de la
campaña nacional de Congreso (`docs/ESTUDIOS/CAMPANA_NACIONAL_20261013/TASK_REGISTRY.json`). Ese registro
tiene 84 tareas y hoy solo devuelve `NAT-C-056`, que está en estado `READY` pero bloqueada fuera del
proyecto: espera la respuesta del CNIG al formulario enviado el 18-10-2026. Las otras 53 tareas pendientes
dependen de ella y `NAT-F-003` espera autorización del propietario.

Los agentes (Codex, Claude) que preguntan "¿qué hago ahora?" reciben una tarea imposible y entran en bucle,
mientras el frente que sí puede avanzar, el autonómico, no está modelado en ningún planificador. Según
`orchestracion/estado_operativo.json` hay 12 territorios con fuentes territoriales preparadas y generación
pendiente, y 3 territorios con fuentes electorales o resultados pendientes. Además, la última sesión de Codex
(26-10) se cortó por `usage_limit_exceeded` con 75 ficheros sin commit en `DDD-distritos-autonomicos`, y
había trabajo local sin subir en varias carpetas del Mac. Las ramas `rescate/*` ya subidas son
`rescate/DDD-orquestador-auto-20261027`, `rescate/DDD-n08-cantabria-20261027` y
`rescate/DDD-f10-consumer-verification-20261027`.

La alternativa es un **planificador unificado de frentes**, de solo lectura y determinista. Lee el estado
durable de todos los frentes (autonómico territorial, autonómico electoral, nacional Congreso, e
integración de trabajo en vuelo) y devuelve la siguiente acción ejecutable de verdad. Las esperas externas
y de propietario se clasifican como esperas explícitas, y cuando no hay nada ejecutable sale con un código
de parada limpio en vez de proponer tareas bloqueadas.

## Objective
Al terminar existirá `python -m ddd_core.planificador_frentes`. Para cualquier agente o humano:
1. Devuelve una lista priorizada de acciones `EXECUTABLE`, cada una con su ruta concreta: workflow e
   inputs, por ejemplo `gestor-campanas.yml` con `territorios=…`.
2. Separa en `waiting` las acciones `WAIT_EXTERNAL` (CNIG), `WAIT_OWNER` (NAT-F-003, R040) y
   `WAIT_INTEGRATION` (ramas `rescate/*` sin revisar), con motivo y evidencia.
3. Sale con código `0` si hay trabajo ejecutable y `3` si solo hay esperas. Así los agentes paran limpiamente.
4. No modifica el registro nacional, el estado operativo ni los tests existentes (que fijan `NAT-C-056=READY`).
5. Impone a los agentes una regla de checkpoint: antes de cada paso largo, commit y push a una rama de
   trabajo. Así un corte por cuota no vuelve a dejar trabajo solo en disco local.

## Problem Statement
- **Visión parcial:** el planificador nacional no ve el frente autonómico, que es el que puede avanzar.
- **READY falso:** `READY` en el registro nacional significa "dependencias satisfechas", no "ejecutable
  ahora". Una tarea que espera a un tercero se propone igual. No se puede cambiar su estado sin romper
  `tests/test_national_campaign_registry.py:143`, `tests/test_cnig_official_inquiry.py:22` y
  `tests/test_national_boundary_acquisition_ledger.py:90`, y además el registro es evidencia histórica.
- **Sin parada limpia:** un selector que nunca dice "no hay nada que hacer" provoca bucles en agentes
  autónomos.
- **Trabajo fuera de GitHub:** el estado real incluye worktrees locales y ramas de rescate que ningún
  planificador considera.

## Solution Approach
Nuevo módulo `ddd_core/planificador_frentes.py` que **compone** fuentes existentes sin sustituirlas:

| Frente | Fuente leída | Regla de acción |
|---|---|---|
| A. Generación territorial | `orchestracion/estado_operativo.json` → `territories[].ft/g` + `phase_evidence` | `ft=green` y `g≠green` → `EXECUTABLE`: `gestor-campanas.yml`, `publication_mode=territorial_only`, territorios agrupados por lote |
| B. Electoral | mismo fichero → `fe/re` | `g=green` y `fe≠green` → preparar fuentes electorales; `g=green`, `fe=green` y `re≠green` → incorporar resultados |
| C. Nacional Congreso | `TASK_REGISTRY/DEPENDENCIES/RESOURCE_LOCKS.json` vía `select_ready_tasks()` | candidatas READY filtradas contra el registro de esperas |
| D. Integración | nuevo `orchestracion/frentes/trabajo_en_vuelo.json` | rama `rescate/*` o `codex/*` declarada y sin revisar → `WAIT_INTEGRATION` con prioridad alta |

El registro de esperas está en un nuevo `orchestracion/frentes/esperas.json`. Es declarativo y versionado:
cada entrada lleva `id`, `kind` (`EXTERNAL|OWNER|LINEAGE`), `blocks` (IDs de tarea o territorios),
`evidence` (ruta y SHA-256) y `release_condition`.

Contenido inicial:
- `NAT-C-056`: EXTERNAL, CNIG, con evidencia en `CNIG_CONSULTA_OFICIAL_20261018.json`.
- `NAT-F-003`: OWNER.
- R040: OWNER, según `docs/SALIDAS_CHATGPT/PUNTO_REENGANCHE.md`.
- Bloqueos de linaje M06/M08 de Asturias, Cantabria y Castilla-La Mancha: LINEAGE, según
  `docs/REGISTRO_DE_CAMBIOS.md` 2026-10-26. Bloquean la reutilización, no la regeneración.

Prioridad determinista:
1. `D` (rescatar e integrar trabajo hecho, porque perderlo es irreversible).
2. `A`, empezando por los territorios con avance local conocido (Andalucía, Valencia, Cataluña, Murcia,
   Ceuta, Canarias).
3. `B`.
4. `C`.

Melilla queda como `WAIT_OWNER` (decisión de política K), porque Codex demostró que sus 44 secciones no
admiten 25 distritos. El desempate es por código INE de comunidad autónoma.

Salida JSON con esquema `ddd.planificador-frentes/1.0`, incluyendo `source_sha256` de cada fichero leído,
`execution_started=false` y `generation_authorized=false`, igual que el planificador nacional. El módulo
nunca dispara workflows: solo los propone.

## Relevant Files
Use these files to complete the task:

- `ddd_core/national_campaign_planner.py`: selector nacional que se reutiliza mediante `select_ready_tasks()` sin modificarlo.
- `orchestracion/estado_operativo.json`: estado durable por territorio (`ft/g/fe/re`, `phase_evidence`), generado desde catálogos y evidencias.
- `docs/ESTUDIOS/CAMPANA_NACIONAL_20261013/TASK_REGISTRY.json`, `DEPENDENCIES.json`, `RESOURCE_LOCKS.json`: registro nacional (solo lectura).
- `docs/ESTUDIOS/CAMPANA_NACIONAL_20261013/CNIG_CONSULTA_OFICIAL_20261018.json`: evidencia de la espera externa de `NAT-C-056`.
- `docs/ESTUDIOS/CAMPANA_NACIONAL_20261013/NATIONAL_PLANNER.md`: documentación del selector nacional; se enlaza al nuevo.
- `.github/workflows/gestor-campanas.yml`: ruta de ejecución autonómica (inputs `campana`, `estrategia`, `publication_mode`, `territorios`).
- `.github/workflows/preparacion-resultados-electorales.yml`, `.github/workflows/incorporacion-resultados-electorales.yml`: rutas del frente B.
- `docs/REGISTRO_DE_CAMBIOS.md`: registro obligatorio de cambios, con cabecera versionada y predecesor en `legacy/docs/`.
- `docs/SALIDAS_CHATGPT/PUNTO_REENGANCHE.md`: punto de reenganche para agentes; debe apuntar al nuevo planificador.
- `infraestructura/ordenes-manuales/ddd_auto.py` y la rama `rescate/DDD-orquestador-auto-20261027` (v1.3.0): orquestador local de Codex. Debe consumir el código de salida `3` como "parar".
- `tests/test_national_campaign_planner.py`: patrón de tests del selector existente.
- `herramientas/verificar_descubrimiento_tests.py`: CI exige tests descubribles por `unittest`.

### New Files
- `ddd_core/planificador_frentes.py`: composición de los frentes, clasificación, priorización y CLI.
- `orchestracion/frentes/esperas.json`: registro declarativo de esperas externas, de propietario y de linaje.
- `orchestracion/frentes/trabajo_en_vuelo.json`: ramas de rescate o trabajo pendiente de revisión e integración.
- `schemas/ddd-planificador-frentes.schema.json`: esquema de la salida y de los dos ficheros de entrada.
- `tests/test_planificador_frentes.py`: tests `unittest.TestCase` con fixtures pequeñas y una prueba sobre el estado real del repo.
- `docs/ORQUESTACION/PLANIFICADOR_FRENTES.md`: uso, códigos de salida y regla de checkpoint para agentes.

## Implementation Phases
### Phase 1: Foundation
Esquema JSON y los dos registros declarativos (`esperas.json`, `trabajo_en_vuelo.json`) con el contenido
inicial verificado contra la evidencia del repo: rutas y SHA-256 reales, ninguna entrada inventada.

### Phase 2: Core Implementation
Implementar `planificador_frentes.py`:
- Cargar y hashear las entradas.
- Derivar acciones A y B desde `estado_operativo.json`.
- Obtener C desde `select_ready_tasks()`.
- Aplicar las esperas.
- Añadir D.
- Ordenar de forma determinista, emitir JSON y salir con el código adecuado.

Fallar cerrado ante fichero ausente, JSON inválido, esquema incorrecto, territorio desconocido o espera
sin evidencia (código `2`).

### Phase 3: Integration & Polish
- Documentación.
- Enlace desde `NATIONAL_PLANNER.md` y `PUNTO_REENGANCHE.md`.
- Entrada en `REGISTRO_DE_CAMBIOS.md` con predecesor archivado.
- Integración opcional en `ddd_auto` (leer el código `3` → `STOP_CLEAN`).
- Regla de checkpoint documentada en `AUTO.md` y `PLANIFICADOR_FRENTES.md`.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 0. Asegurar el trabajo en vuelo (prerrequisito, fuera de este repo)
- En el Mac, rescatar `DDD-distritos-autonomicos` (75 ficheros), `DDD-distritos-nacionales` (10),
  `DDD-n06-expediente` (18 + 1) y `DDD-f10-receipts` (4) en ramas `rescate/<carpeta>-20261027` con push,
  sin tocar `main`.
- Verificar desde aquí con `git ls-remote --heads origin 'refs/heads/rescate/*'`.

### 1. Crear rama de trabajo
- `git fetch origin main && git checkout -b feat/planificador-frentes origin/main`.

### 2. Esquema y registros declarativos
- Crear `schemas/ddd-planificador-frentes.schema.json` (entradas y salida).
- Crear `orchestracion/frentes/esperas.json` con `NAT-C-056` (EXTERNAL),
  `NAT-F-003` (OWNER), `R040` (OWNER), `melilla-k` (OWNER) y los bloqueos LINEAGE de
  `asturias`, `cantabria` y `castilla_la_mancha`. Cada uno con su `evidence.path` y `sha256` calculado
  sobre el fichero real.
- Crear `orchestracion/frentes/trabajo_en_vuelo.json` con las ramas `rescate/*` existentes en origin y
  su SHA de cabeza.

### 3. Núcleo del planificador
- Crear `ddd_core/planificador_frentes.py` con:
  - `cargar_entradas()`.
  - `acciones_territoriales()`, `acciones_electorales()`, `acciones_nacionales()` (envuelve
    `select_ready_tasks`) y `acciones_integracion()`.
  - `aplicar_esperas()` y `priorizar()`.
  - `main()`.
- Agrupar las acciones A en un único `gestor-campanas.yml` sugerido, con `territorios` en formato CODAUTO
  separados por comas y `publication_mode=territorial_only`.
- Códigos de salida: `0` hay ejecutables, `3` solo esperas, `2` entrada inválida.

### 4. Tests
- `tests/test_planificador_frentes.py` (unittest) con estos casos:
  - Fixture con solo `NAT-C-056` READY y una espera EXTERNAL → sin ejecutables y código 3.
  - Territorio `ft=green, g=yellow` → acción A con su ruta.
  - Territorio `g=green, fe=yellow` → acción B de preparación electoral.
  - Espera sin evidencia o con SHA erróneo → código 2.
  - Rama en `trabajo_en_vuelo` → D antes que A.
  - Orden determinista con dos ejecuciones idénticas byte a byte.
  - Prueba sobre el estado real del repo: debe salir código 0 con al menos las acciones A de los 12
    territorios pendientes menos Melilla, y `NAT-C-056` en `waiting` con `kind=EXTERNAL`.
- Confirmar que los tests existentes que fijan `NAT-C-056=READY` siguen pasando sin cambios.

### 5. Documentación y gobernanza
- `docs/ORQUESTACION/PLANIFICADOR_FRENTES.md` con el uso, la tabla de reglas, los códigos de salida y la
  **regla de checkpoint para agentes**: commit y push a la rama de trabajo antes de cada paso de más de
  10 minutos y al final de cada territorio; nunca dejar más de un territorio sin subir.
- Añadir enlaces en `NATIONAL_PLANNER.md` y en `docs/SALIDAS_CHATGPT/PUNTO_REENGANCHE.md`, con versión
  nueva y predecesor en `legacy/`.
- Añadir una entrada en `docs/REGISTRO_DE_CAMBIOS.md` (cabecera versionada, predecesor en `legacy/docs/`).

### 6. Integración opcional con el orquestador local
- Tras integrar `rescate/DDD-orquestador-auto-20261027`, hacer que `ddd auto` invoque el planificador
  antes de cada intento y trate el código `3` como `STOP_CLEAN`, sin reintentar.

### 7. Validar
- Ejecutar los comandos de validación de abajo.
- Abrir un PR contra `main` y esperar a que `Pruebas de la Plataforma` salga en verde.

## Testing Strategy
- **Unitarios con fixtures mínimas:** un territorio por estado de color, un registro nacional de 2–3
  tareas y esperas de cada tipo.
- **Bordes:** fichero ausente, JSON con claves duplicadas o tipos erróneos, territorio en una espera
  que no existe en `estado_operativo.json`, ciclo en el DAG nacional (heredado de `select_ready_tasks`),
  SHA de evidencia que no coincide, lista vacía de ramas.
- **Determinismo:** dos ejecuciones con salida idéntica byte a byte, independiente del orden de los ficheros.
- **Estado real:** el test sobre los ficheros reales del repo confirma que hoy el planificador ya no devuelve
  `NAT-C-056` como ejecutable y sí devuelve trabajo autonómico.
- **No regresión:** suite completa `unittest discover`, con atención a `test_national_campaign_planner`,
  `test_national_campaign_registry`, `test_cnig_official_inquiry` y `test_national_boundary_acquisition_ledger`.

## Acceptance Criteria
- `python -m ddd_core.planificador_frentes` sobre `main` devuelve código `0` y lista como `EXECUTABLE` la
  generación territorial de Andalucía, Baleares, Canarias, Cataluña, Valencia, Madrid, Murcia, Navarra,
  País Vasco, La Rioja y Ceuta. Melilla aparece en `waiting` con `kind=OWNER`.
- `NAT-C-056` aparece solo en `waiting` con `kind=EXTERNAL` y evidencia `CNIG_CONSULTA_OFICIAL_20261018.json`.
- Con solo esperas, el código de salida es `3` y no hay acciones ejecutables.
- La salida es idéntica byte a byte entre dos ejecuciones y valida contra `schemas/ddd-planificador-frentes.schema.json`.
- Ningún fichero existente del registro nacional, de `estado_operativo.json` ni de los tests previos queda modificado.
- La suite `unittest discover` completa pasa, y el CI `Pruebas de la Plataforma` sale en verde en el PR.
- La regla de checkpoint está documentada y enlazada desde `PUNTO_REENGANCHE.md`.

## Validation Commands
Execute these commands to validate the task is complete:

- `python -m ddd_core.planificador_frentes; echo "exit=$?"`: ejecución sobre el estado real; espera `exit=0` y acciones A.
- `python -m ddd_core.planificador_frentes > /tmp/a.json; python -m ddd_core.planificador_frentes > /tmp/b.json; cmp /tmp/a.json /tmp/b.json`: determinismo.
- `python -m unittest tests.test_planificador_frentes -v`: tests nuevos.
- `python -m unittest tests.test_national_campaign_planner tests.test_cnig_official_inquiry -v`: no regresión del selector nacional.
- `DDD_SKIP_LEGACY_CHECK=1 python herramientas/verificar_descubrimiento_tests.py`: descubrimiento de tests exigido por el CI.
- `DDD_SKIP_LEGACY_CHECK=1 python -m unittest discover -s tests -p 'test_*.py'`: suite completa, la misma que ejecuta `pruebas-plataforma.yml`.
- `python -m unittest tests.test_r015_invariantes.GovernanceHeaders -v`: cabeceras y predecesores de los documentos versionados.
- `python -m ddd_core.national_campaign_planner --registry docs/ESTUDIOS/CAMPANA_NACIONAL_20261013/TASK_REGISTRY.json --dependencies docs/ESTUDIOS/CAMPANA_NACIONAL_20261013/DEPENDENCIES.json --locks docs/ESTUDIOS/CAMPANA_NACIONAL_20261013/RESOURCE_LOCKS.json`: el selector nacional sigue devolviendo exactamente lo mismo que antes.

## Notes
- No hacen falta librerías nuevas: `json`, `hashlib` y `argparse` de la biblioteca estándar, y `jsonschema` ya está instalado.
- El planificador **propone; no ejecuta.** Lanzar `gestor-campanas.yml` sigue siendo una decisión explícita
  del propietario, por lotes pequeños y con puerta de validación entre lotes.
- No se cambia `NAT-C-056` en el registro nacional. La espera vive en `esperas.json`, lo que respeta la
  evidencia histórica y los tests que la fijan. Cuando llegue la respuesta del CNIG basta con retirar la
  entrada de `esperas.json`.
- El push a GitHub desde la sesión en la nube está bloqueado hasta que se instale la app de Claude en el
  repo. Mientras tanto, la implementación puede hacerse aquí y subirse desde el Mac, o hacerse
  directamente con el Claude 2.1.112 del Mac.
- Riesgo: `estado_operativo.json` se regenera automáticamente. El planificador debe leerlo, nunca escribirlo,
  y registrar su SHA para detectar si cambió entre la planificación y la ejecución.
