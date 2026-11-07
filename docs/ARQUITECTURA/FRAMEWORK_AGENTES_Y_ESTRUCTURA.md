# Framework de agentes, estructura y arquitectura funcional de DDD

**Versión:** 1.0.0
**Fecha:** 2026-11-07
**Estado:** borrador de referencia. Es una propuesta de diseño, no una arquitectura certificada ni desplegada.
**Origen:** sesión de planificación del 02 al 07-11-2026 (chat «Planificador»), más cuatro imágenes de ChatGPT, una infografía de Claude Code, la auditoría V2 de ChatGPT y el metaagente v1.0. Los originales están en `docs/ARQUITECTURA/referencias/`.

> Qué es y qué no es: recoge lo que sirve para el futuro (fases, estructura `.claude/`, catálogo de agentes, reglas aprendidas, estado del proyecto). No cambia código, contratos ni workflows. Lo afirmado sobre la infografía de Claude Code y sobre los diagramas de ChatGPT no está verificado contra el producto real.

## 1. Ambición y principios

Objetivo: que DDD crezca hasta ser un proyecto de referencia en redistricting geoespacial: reproducible, con procedencia comprobable y extensible a otros países.

Principios, en orden de importancia:

1. **Lo más pequeño que funcione.** Un agente solo existe donde hace falta juicio. Lo mecánico va a CI o a scripts.
2. **Quien construye no certifica.** La verificación la hace otro contexto, con el diff y la especificación.
3. **Determinista primero.** Reglas repetibles en CI, hooks y `herramientas/`; el modelo solo juzga.
4. **Evidencia antes que confianza.** Cada afirmación de estado (diseñado, implementado, probado, verificado) lleva su prueba.
5. **Humano en lo irreversible.** Lanzar, fusionar y publicar se aprueban fuera de los chats, ligados al HEAD exacto.
6. **Estado en ficheros, no en chats largos.** Cada sesión arranca ligera desde `PLAN.md`, el registro, las skills y este documento.
7. **Coste medido.** Se mide coste por provincia cerrada, éxito a la primera y causas raíz por día. Tope de gasto semanal explícito.

## 2. Fases propuestas P00 a P60

Una sola tubería. Autonómico (AUT) y Nacional (NAC) no son tuberías distintas: el **universo** es una clave en cada paso (`universo`, `edición`, `territorio`, `estrategia`, `escenario`).

| Fase | Contenido | Equivale hoy a |
|---|---|---|
| P00 | Gobierno de campañas y activación | Gestor de Campañas, Activación por Elección, workflow 00 |
| P10 | Fuentes: P11 territoriales, P12 electorales, ambas por universo y edición | workflows 01 y 03, paquetes preparados |
| P20 | Producción territorial | M01 a M06 |
| P21 | Población y secciones | M01 |
| P22 | Geometría y alias | M02 |
| P23 | Grafo | M03 |
| P24 | Semillas | M04 |
| P25 | Optimización: canónico y GerryChain (misma interfaz, estrategia elegible) | M05 y estrategias GerryChain 25 y 50 |
| P26 | Consolidación y certificación territorial | M06 y auditoría geométrica |
| P30 | Escenarios: ensembles, candidatos y sensibilidad | piloto de ensemble (Salamanca, La Rioja, Sevilla) |
| P40 | Producción electoral, por universo | M07 y M08, workflow 04 |
| P50 | Archivo y distribución: catálogo de procedencia, visor, descargas | visor, `publicaciones_visor.json` |
| P60 | Publicación académica | nuevo |

La numeración P21 a P25 es ajustable. La decisión sobre GerryChain es del propietario: es **parte de la producción territorial (P25)**, no una rama aparte; los ensembles (muchos candidatos) van en P30.

**Avisos**
- **No renombrar ficheros** `modulos/0X_*`: están en las huellas M05 y en las evidencias N08, y en los tests de gobernanza (R015, R016). El cambio es primero de nombre visible (workflows, visor, docs) y los ficheros se renombran en una migración propia.
- Los workflows «Generación de Distritos Autonómicos» y «Incorporar Resultados Electorales» procesan también provincias: dejar de nombrarlos por universo.
- Cargar fuentes regionales no debe invalidar las nacionales (y al revés): se guardan por `universo` y `edición`.

## 3. Arquitectura funcional propuesta por ChatGPT (P0 a P8) y qué hacemos con ella

Imagen: `referencias/chatgpt_2_arquitectura_funcional_P0-P8.png`. Capas: P0 planificación y activación; P1 fuentes territoriales; P2 fuentes electorales; P3 producción territorial; P4 experimentación (GerryChain, ensembles); P5 integración electoral; P6 verificación y certificación; P7 conservación científica (R2, artefactos, manifiestos); P8 publicación y difusión (visor, Zensical, descargas, DOI).

| Elemento | Decisión |
|---|---|
| Separar fuentes territoriales y electorales (P1, P2) | Adoptar (P11, P12) |
| Verificación y certificación como capa propia (P6) | Adoptar como transversal: puertas y auditorías en varios puntos |
| Conservación científica (P7) | Adoptar: R2 (ya se prueba su conectividad en #426) y manifiestos con hash |
| Experimentación después de producción (P4) | **Corregir**: GerryChain es estrategia de producción (P25); solo los ensembles son experimentación (P30) |
| Cloudflare R2 | Adoptar: los artefactos de Actions caducan a los 14 días y dan 403 desde la nube |
| Zenodo (DOI) | Adoptar en P60 |
| Zensical (documentación) | Aplazar |
| DVC, STAC, «DDD Atlas» | Aplazar; STAC tendrá sentido al crecer hacia otros países |

Imagen 1 (`chatgpt_1_flujo_P00-P60.png`): flujo P00 a P60 con flechas desde P20 a P30, P40, P50 y P60. Es la base de la tabla de la sección 2. Imagen 3 (`chatgpt_3_nucleo_catalogo_procedencia.png`): «núcleo común: catálogo de procedencia y productos» con GitHub, R2, Zensical, DDD Atlas, DVC/STAC y Zenodo; la idea útil es el catálogo de procedencia como núcleo (fuentes, versiones, runs, candidatos, SHA, auditorías, publicaciones).

## 4. AI Control Plane de ChatGPT (imagen 4)

`referencias/chatgpt_4_ai_control_plane.png`: cuatro agentes (operaciones, auditoría, documental, planificación), una capa MCP/API y «permisos mínimos, aprobaciones humanas, logs, evaluaciones». La propia imagen dice «arquitectura propuesta, no funcionalidad certificada como desplegada».

- **No adoptar** como producto: duplica los roles que ya tenemos y consume créditos.
- **Sí adoptar** los cuatro principios de la franja inferior: permisos mínimos, aprobaciones humanas, registro de acciones y evaluaciones.
- Equivalencias: operaciones = operador y forense; auditoría = revisor; planificación = el chat de planificación más `PLAN.md`; documental = skill de cierre de sesión y el catálogo de procedencia.

## 5. Estructura de directorios objetivo (`.claude/`)

Basada en la infografía «Claude Code Project Structure» (`referencias/claude_code_estructura_proyecto_nov2026.webp`, autor Ananya Ghosh Chowdhury, nov 2026). No he verificado `workflows/` ni los «33 eventos de hooks» que cita; lo demás coincide con lo que conozco de Claude Code.

```
CLAUDE.md                  corto (<100 líneas): reglas del propietario y mapa
CLAUDE.local.md            notas personales (ignorado por git)
.mcp.json                  servidores MCP del equipo (pocos: cada uno añade contexto)
.claude/
  settings.json            permisos allow/ask/deny, entorno, hooks
  settings.local.json      ajustes personales (ignorado)
  rules/                   un tema por fichero; con paths: se cargan solo al tocar esos ficheros
    gobernanza.md          paths: modulos/**, ddd_core/**, herramientas/**  (cabecera VERSIÓN + copia legacy)
    registro.md            paths: docs/REGISTRO_DE_CAMBIOS.md  (numeración, sin marcas de conflicto)
    huellas.md             paths: modulos/05*, docs/ESTUDIOS/N08_*  (huellas M05 y evidencias N08)
    workflows.md           paths: .github/workflows/**  (lista de lanzables, diseño A)
  skills/                  una carpeta por skill, con SKILL.md (solo nombre y descripción en el arranque)
  agents/                  un .md por subagente (nombre, descripción, herramientas, modelo, memoria)
  hooks/                   scripts deterministas (bloqueos)
  workflows/               (según la infografía) JS que orquesta muchos subagentes; aplazado
  agent-memory/            memoria por agente (p. ej. forense/MEMORY.md con el catálogo de causas)
```

**Skills a crear** (cada una de una página, con lo aprendido): `planificador`, `operador`, `implementador`, `lanzar-00`, `diagnosticar-run`, `revisar-pr`, `publicar-visor`, `presupuesto`, `diseñar-agente`. `cierre-sesion` ya existe.

**Hooks prioritarios:** bloquear commit con marcas de conflicto (`<<<<<<<`, `=======`, `>>>>>>>`); bloquear `git push --force`; avisar si se edita un fichero versionado sin subir su cabecera ni dejar copia en `legacy/`.

**Permisos (`settings.json`):** permitir lectura (`gh api` de solo lectura, tests locales); pedir confirmación para dispatch de workflows y publicación; denegar force push y borrado de ramas. Probar si el clasificador de la sesión en la nube lo respeta: en la sesión del 02 al 07-11 bloqueó lanzamientos como «Production Deploy» y «Create Public Surface» aunque el propietario los hubiera autorizado.

## 6. Capas de agentes y catálogo

| Capa | Herramienta | Para qué | Coste |
|---|---|---|---|
| CI | GitHub Actions | Reglas mecánicas: marcas de conflicto, numeración del registro, gobernanza, caducidad de artefactos, archivado a R2 | Cero de modelo |
| Skills | `.claude/skills/` | Roles y procedimientos que un chat necesita en su contexto | Bajo |
| Subagentes | `.claude/agents/` | Trabajo acotado, de solo lectura, con contexto aparte y salida JSON | Medio |
| Chats con rol | Sesiones de Claude Code | Trabajo largo, con espera y decisiones: operador, implementador, motor (Opus) | Alto: sesiones ligeras |

**Regla para elegir:** mecánico, a CI; procedimiento que el chat necesita, a una skill; trabajo acotado que quieres aislar, a un subagente; largo y con decisiones, a un chat con rol.

| Agente | Fase | Hace | Modelo | Permisos |
|---|---|---|---|---|
| Revisor independiente | P20 a P50 | Revisa cada PR: unidades y CRS, gobernanza, huellas, numeración, tests rojo/verde | Sonnet; Opus si toca el motor | Solo lectura |
| Forense de runs | P20 a P40 | Dado un run, da la causa en 5 líneas con el catálogo de causas | Sonnet | Solo lectura |
| Operador de campañas | P00, P50 | Lanza lo autorizado, verifica manifiestos, publica | Sonnet | Lista cerrada |
| Ingeniero de motor | P24, P25 | M04, M05 y GerryChain en local, una PR por causa | Opus | Escribe código, sin lanzar |
| Agente de fuentes | P10 | Vigencia, hashes y edición; conflictos entre universos | Sonnet | Solo lectura |
| Analista electoral | P40 | Tablas y hemiciclos (casi todo es un script) | Sonnet | Solo lectura |
| Redactor académico | P60 | Evidencia a métodos y procedencia | Sonnet u Opus | Solo lectura |

**No serían agentes sino jobs de CI:** guardián de `main` y archivista (copia de artefactos con SHA-256 a R2 antes de los 14 días).

**Aprobación fuera de los chats:** pasar lanzamientos y publicaciones a workflows con **Environments y revisores requeridos** de GitHub (un clic del propietario, sin modelo). Hay que comprobar si el plan de GitHub del repositorio lo permite. El operador pasaría a planificar y verificar.

**Reglas comunes:** ninguno vigila por sí solo salvo que se pida; estado en `PLAN.md`, registro y skills; máximo dos escritores sobre el núcleo compartido; un único operador que lanza.

## 7. Metaagente arquitecto-constructor v1.0: qué se adopta

Original en `referencias/META_AGENTE_ARQUITECTO_CONSTRUCTOR_v1.0.md` (1384 líneas; leído completo el 07-11). Es un prompt de instrucciones maestras, no un runtime.

**Adoptar como referencia (destilado en la skill `diseñar-agente`, no como prompt residente):**
- Criterio rector: el sistema más pequeño que cumple (sección 0 y 3).
- Ficha de agente: misión, exclusiones, entrada y salida, herramientas, autoridad, aceptación, recursos, recuperación (sección 7).
- Delegación autocontenida (sección 8) y esquema de handoff (sección 23).
- Estados de tarea (`PENDING`, `READY`, `RUNNING`, `REVIEW`, `WAITING_APPROVAL`, `BLOCKED`, `COMPLETED`, `FAILED`) y de efectos externos (`PREPARED`, `AUTHORIZED`, `IN_FLIGHT`, `CONFIRMED`, `UNKNOWN`): si es `UNKNOWN`, reconciliar antes de reintentar (sección 9). Encaja con la puerta de Cádiz con digest vacío.
- Resultado de calidad `PASS`, `PASS_WITH_EXCEPTIONS`, `FAIL`, `BLOCKED` (sección 9.2).
- Aprobación ligada al candidato exacto (HEAD o digest) e identidad por manifiesto de hashes (secciones 11 y 15).
- Gate de entrega y tabla de madurez diseñado, implementado, probado, verificado (secciones 24 y 25).
- Casos de calibración (29E): «candidato modificado tras la revisión» y «reparaciones agotadas con criterio fallido» coinciden con lo vivido; sirven como evals del revisor.
- Definition of Done de 12 puntos (sección 30), ADR (27) y plantilla de entrada mínima (31).
- Perfil DDD (sección 28): se reutilizan roles, workflows y contratos vigentes; lanzar, fusionar y publicar no son efecto colateral de un plan.

**No adoptar ahora:** controlador con *leases*, ocho esquemas JSON y almacén de eventos (su propio criterio rector lo desaconseja; ya tenemos Actions, `PLAN.md` y el registro); cargarlo como instrucciones de sistema (coste fijo por chat).

## 8. Evals y libro de costes

- **Conjunto de oro** para revisor y forense: las causas raíz de la sección 9 y los casos ADV-01 a ADV-16 de `referencias/AUDITORIA_CHATGPT_PLAN_V2_2026-11-02.md` (sección 7.2). Un agente no se da por listo hasta cazar los defectos históricos sobre el diff original.
- **Libro de costes:** cada ejecución de agente anota tokens, resultado y si pasó a la primera.
- **Métricas objetivo** (al 02-11 la tasa de éxito a la primera de las 00 era de ~20 %): coste por provincia cerrada, porcentaje de 00 que pasan a la primera (objetivo > 60 %), causas raíz cerradas por día.
- **Regla de la auditoría:** como mucho dos ciclos de reparación por causa; 00 productiva cero por defecto; nunca relanzar «para ver qué pasa».

## 9. Catálogo de causas raíz (semilla para `diagnosticar-run`)

| Causa | Síntoma | Arreglo y referencia |
|---|---|---|
| «Reutilizar» restaura un M06 anterior a los arreglos | Las Palmas falla igual con el código nuevo (`bajo límite=1`) | 00 «Ejecutar desde el principio» (run 41432561787) |
| Validador sin campo municipal | Mogán exento no se ve | Respaldo `CUMUN` o 5 primeras cifras del `CUSEC` (#398) |
| Reparación M05 mueve el distrito exento | Otro distrito queda sin exención | M05 no mueve el municipio exento (#399) |
| Contrato ya completo no reaplica la política | Cádiz y Baleares siguen con techo 1,15 | `apply_policy_population_limits` (#403) |
| Exención detectada por el formato del id de unidad | Cádiz cuenta como duro el distrito 7 exento | M05 7.8.7 lee el campo de municipio; techo de Baleares 1,28 (#404) |
| Puerta 04 sin descargar el M08 | `DURABLE_LINEAGE_INCOMPATIBLE`, digest vacío | `electoral_product_available=false` y 00 «Reutilizar» (#407) |
| Residuo municipal sobre el techo que M05 no redibuja | Murcia y Madrid bloqueadas | M04 7.6.6, alivio de residuos (#419) |
| Ensemble: geometría en grados | Aristas «débiles» de 1502 con 0,04 m | Reproyectar a `working_crs` (#409) |
| Ensemble: secciones MultiPolygon | `geometric_contiguity` en distritos 1 y 2 | `preserve_atomic_multipart_sections=true` (#411) |
| Runner con falso verde | Salida 0 con candidatos fallidos | Códigos de salida 3 y 4 (#410) |
| Publicación de ensemble | Falta `ensemble_sha256`; copia web con 532 features; guarda solo para CRS proyectado | #418, #421, #424 |
| Marcas de conflicto en el registro de cambios | `main` roto | Hotfix #422; hook y check de CI propuestos |

## 10. Reglas operativas aprendidas

- Identificar cada run por `TERRITORY:` en el log de «Planificar», nunca por orden. Toda 00 que llega a M06 encadena sola la 04.
- Cambiar M04, M05, política o fuente invalida los checkpoints: usar «Ejecutar desde el principio» o «Generar desde fuente territorial acreditada».
- Los artefactos de Actions caducan a los 14 días y dan 403 desde la sesión en la nube: diagnosticar en local con los volcados de `diagnostico/*` y pedir los grafos al Mac del propietario si faltan.
- El auto-merge no siempre actúa: el propietario fusiona; antes de empujar, comprobar que no hay marcas de conflicto y que el test de gobernanza pasa.
- Los permisos de lanzamiento los da el propietario en el chat que ejecuta; el clasificador de la nube puede bloquear mensajes entre chats.
- Un solo operador lanza. Tras un fallo, no relanzar: informar de la causa.
- Gobernanza: cada fichero versionado sube su cabecera VERSIÓN y deja copia en `legacy/` con ANTERIOR. El número del registro se pregunta antes de añadir entradas (último visto en `main`: 1.0.94 el 07-11).

## 11. Estado del proyecto a 07-11-2026 y pendientes

**Hecho:** 49 de 52 provincias completas (cerradas entre el 02 y el 03-11: Las Palmas, Baleares, Cádiz, Madrid, Murcia); autonómicas 18 de 19 (falta Andalucía). Piloto de ensembles: Salamanca 10/10 publicada como escenario (run 41614546499, `ensembles=1`), La Rioja 10/10 y Sevilla 10/10 (4 hashes únicos) sin publicar. Visor con campos de escenario (T-27 a, b, c).

**Pendiente de producto:**
- Málaga (distrito 10, 161.454 sobre el techo), Barcelona (`hard` de 2 a 1) y Alicante (de 156.889 a 144.394, aún sobre el techo): M04 7.6.6 no las cierra; sin contradicción aritmética probada. Siguiente: estudio de motor en Opus con presupuesto fijo.
- Publicar los ensembles de La Rioja y Sevilla.
- Andalucía y la otra región, comarcas, auditoría de calidad, exenciones municipales (9) y de partición (7) sin `decided_at` ni evidencia ligada, `CONTRACT_POLICY_STALE`.
- **Hemiciclo y tabla de resultados** (petición del propietario, el 03-11, de bajo coste): con los M08 de las provincias completas, sumar escaños de tres maneras: reparto real previo, elección anterior y sistema mayoritario uninominal propio, con totales de España. Mensaje cortado en «hasta que…»: confirmar el alcance con el propietario.
- Decisión del plan de 100 $ tras una semana de métricas.

## 12. Plan inmediato (paso 1) y prompt de arranque

Orden: (1) checks de CI (marcas de conflicto, numeración del registro); (2) `CLAUDE.md` recortado, `rules/` y `hooks/`; (3) skills; (4) conjunto de oro; (5) revisor y forense; (6) Environments con aprobación. Producto en paralelo, a demanda y con tope.

```yaml
objetivo: "Paso 1 del plan de arquitectura de agentes de DDD: configuración de Claude Code y comprobaciones de CI, con el mínimo gasto"
resultado_esperado: |
  1) CI: dos checks nuevos: sin marcas de conflicto en ficheros versionados; numeración consecutiva de docs/REGISTRO_DE_CAMBIOS.md.
  2) CLAUDE.md recortado (<100 líneas) y .claude/rules/ con paths: gobernanza, registro, huellas M05/N08, workflows.
  3) .claude/hooks/: bloquear commit con marcas de conflicto y git push --force.
  4) .claude/skills/: planificador, operador, implementador, lanzar-00, diagnosticar-run, revisar-pr, publicar-visor, presupuesto, diseñar-agente.
entorno: "Repo jfmurciego/DiputadodeDistrito, sesión cloud. Lee CLAUDE.md, docs/PLAN.md y docs/ARQUITECTURA/FRAMEWORK_AGENTES_Y_ESTRUCTURA.md primero."
autorizacion: "Crear rama y abrir PR (las fusiona el propietario). SIN lanzar 00, SIN publicar, SIN fusionar, sin cambiar suelo/techo/K/atomicidad, sin renombrar modulos/*."
exito: "CI verde; test de gobernanza y R015/R016 pasan; hooks probados con un caso que falla y otro que pasa."
restricciones: "Ahorro: sin esperas activas ni avisos intermedios. Pregunta el último número del registro antes de añadir entradas. Una PR por bloque (CI primero)."
baseline: "Arquitectura P00-P60 de este documento; metaagente v1.0 solo como referencia (secciones 7, 9, 25, 29E, 30)."
```

## 13. Índice de referencias (`docs/ARQUITECTURA/referencias/`)

| Fichero | Qué es |
|---|---|
| `chatgpt_1_flujo_P00-P60.png` | Flujo P00 a P60 de ChatGPT |
| `chatgpt_2_arquitectura_funcional_P0-P8.png` | Arquitectura funcional P0 a P8 |
| `chatgpt_3_nucleo_catalogo_procedencia.png` | Núcleo común: catálogo de procedencia y herramientas |
| `chatgpt_4_ai_control_plane.png` | AI Control Plane (propuesta) |
| `claude_code_estructura_proyecto_nov2026.webp` | Infografía de la estructura de un proyecto de Claude Code |
| `META_AGENTE_ARQUITECTO_CONSTRUCTOR_v1.0.md` | Metaagente v1.0 (6-11-2026) |
| `AUDITORIA_CHATGPT_PLAN_V2_2026-11-02.md` | Auditoría V2 de ChatGPT (plan de ingeniería verificable) |
