<!--
Nombre: Plan de trabajo DDD
Versión: 1.0.21
Fecha: 2026-11-07
Alcance: Cola de tareas para chats implementadores y operadores
Estado: candidato
Cambios/motivo: T-88 ampliada a los plugins oficiales de Anthropic (revisión de PR y desarrollo por fases)
Anterior: legacy/docs/PLAN_v1.0.20_20261107.md
-->

# Plan de trabajo — Diputado de Distrito

## Reglas para todos los chats
- Un chat = una tarea. Coge la primera tarea libre de la cola cuyas dependencias estén en «Tareas hechas».
- **Una PR por objetivo, no por tarea** (07-11): las tareas de un mismo chat sobre ficheros propios van en una sola PR.
  Se separa solo si toca ficheros compartidos (motor, workflows, política) o si debe poder revertirse sola. Evita
  cadenas largas: con squash, cada fusión deja en conflicto a la siguiente y repite la CI (~15 min por eslabón).
- Respeta `CLAUDE.md` (topónimos en español, mínimo consumo, coordinación entre sesiones, gobernanza VERSIÓN/legacy).
- El implementador pasa la suite local completa (`python -m pytest -q`) antes de abrir la PR.
- Fusiona el propietario. Nadie lanza ejecuciones productivas ni publica sin su permiso explícito.
- Nada de vigilar runs en el chat: los lanzamientos largos se hacen con scripts en el Mac del propietario
  (rama `lanzadores-mac`).
- Al terminar: mover la tarea a «Tareas hechas» con su PR o run y, si hubo lección cara, `/cierre-sesion`.
- Coordinación: el chat planificador («DDD Plan») lista, describe y asigna; no implementa. Cada chat le manda una
  línea (`send_message`) al abrir PR, lanzar run o cerrar tarea: «T-xx · qué · PR/run · siguiente · bloqueo», y le
  avisa antes de tocar ficheros compartidos (workflows, política, catálogo, `herramientas/`, `modulos/`,
  `ddd_core/`, este plan). Antes de lanzar, preguntar si otro chat ya lo hizo (01-11: Huelva/Valencia duplicadas).
- Las órdenes de lanzar o fusionar las confirma el propietario en el chat que ejecuta, no por mensaje entre sesiones.
- Chat operador único: es el único que lanza ejecuciones (00, activaciones, publicaciones). Los implementadores no
  lanzan; piden el lanzamiento al planificador, que lo pasa al operador. El propietario da permiso por lote, una vez,
  en el chat operador.
- El operador identifica cada run por su territorio (entrada TERRITORY del job «Planificar»), nunca por el orden
  de lanzamiento, y cuenta también los encadenados de github-actions[bot]. No relanza un territorio con un run en curso.
- Primero en local: ninguna 00 sin evidencia del motor en local (o del diagnóstico automático de T-14). En un lote,
  primero un territorio de prueba y luego el resto.
- Infraestructura (workflows, ruleset, credenciales): se valida con una sola ejecución antes de abrir paso al resto.
- `docs/PLAN.md` solo lo edita el planificador; el número de `REGISTRO_DE_CAMBIOS.md` lo asigna el planificador al
  abrir la PR. Los chats le mandan su cierre de tarea y él lo anota.

## 0. Estado al cierre del 07-11 (17:15)
- En `main`: agentes (oro, revisor, forense), registro por ficheros (T-46), delegación, CI en paralelo (4 min, T-50),
  Environments (T-41), archivista R2 (T-47 + reintentos #447), revisor y forense en CI (T-48), exenciones gobernadas
  (T-49), huella de checkpoint (T-51), cadenas sin Mac (T-52), resultados ligeros (T-53), motor 7.6.7 + Fuengirola
  (T-44), hemiciclo con el BOE (T-42/T-45). PR #431 a #448 cerradas.
- En curso: T-54 auto-merge (escrito; espera la autorización del propietario en «Implementador nuevo»), revisión de
  #425 con el revisor, T-55 elección anterior del hemiciclo (BOE 2019-11), relanzamiento del archivista.
- Pendiente del propietario: entorno `produccion` con revisor, secreto `CLAUDE_CODE_OAUTH_TOKEN`, permiso de las 00
  de Barcelona, Alicante y Málaga («Ejecutar desde el principio») y Andalucía («Generar desde fuente territorial
  acreditada»); con ellas, 52/52 provincias y 19/19 autonómicas.

## 1. Estado (2026-11-07)
- Autonómicas: 18/19 completas; Andalucía aparcada (T-07).
- Nacional (52): **49 completas** (del 02 al 03-11 cerraron Las Palmas, Baleares, Cádiz, Madrid y Murcia; #419, M04 7.6.6,
  fusionada; Madrid y Murcia en el visor). **Bloqueadas: Málaga, Barcelona y Alicante** (M04 7.6.6 no las cierra; sin
  contradicción aritmética probada) → T-44.
- Ensembles publicados como escenario: Salamanca (run 41614546499), La Rioja (42384534739) y Sevilla (42385012998) (T-43).
- Arquitectura de agentes (`docs/ARQUITECTURA/FRAMEWORK_AGENTES_Y_ESTRUCTURA.md`, §11 y §12):
  - **Paso 0** (framework P00-P60) · PR #427 · registro 1.0.95 · fusionada.
  - **Paso 1** · bloque 1 CI guardián de `main` · PR #428 · 1.0.96 · bloque 2 `CLAUDE.md`, `rules/` y hook de git ·
    PR #429 · 1.0.97 · bloque 3 skills de rol · PR #430 · 1.0.98. Hechos, **pendientes de fusión en orden
    #428 → #429 → #430** (encadenadas) y después la PR de este plan (1.0.99).
  - Siguientes del §12: (4) conjunto de oro → T-38; (5) revisor y forense → T-39, T-40; (6) Environments con
    aprobación → T-41.
- PR abierta sin tarea: #425 (portal Zensical y auditoría de archivo, Cantabria 50 verificado). Se revisa con T-39
  cuando exista; no se fusiona antes.
- Registro: 1.0.95 en `main` (#427); 1.0.96-1.0.98 en la cadena; 1.0.99 este plan; reservados 1.0.100 (T-38),
  1.0.101 (T-39) y 1.0.102 (T-40), 1.0.103 (T-42, #435), 1.0.104 (T-44, #436) y 1.0.105 (T-46, último manual).

### Asignaciones vigentes (07-11)
| Chat | Rol | Tarea | Siguiente |
|---|---|---|---|
| «Implementador nuevo» | constructor de agentes (Opus) | cadena #429-#430 al día; T-38 hecha en rama (PR tras #431) | T-39 + T-40 |
| «Implementador Motor» | ingeniero de motor (Opus) | T-44: Barcelona bien con `main`; Alicante (M04 7.6.7) y Málaga (exención) en una PR | 00 de las tres vía Operador |
| «T-42 Hemiciclo» | implementador (Sonnet) | T-42 (M08 desde blobs de `publicaciones_visor.json`) | — |
| «Implementador» | — | sesión inactiva | — |
| «Operador» | operador único (Sonnet) | T-43 hecha; **en pausa** | 00 de T-44, prueba de T-41 |
| «Paso 1 agentes DDD» | — | sesión inactiva; T-38 a T-40 pasan a «Implementador nuevo» | — |
| «DDD Plan» (este) | planificador | cola, registro, `PLAN.md` | — |

El propietario habla solo con el planificador para el qué; los permisos de lanzar, publicar y fusionar los da en el chat
que ejecuta (regla de siempre). Cada chat manda su línea de cierre al planificador (`send_message`).

### Ficheros con turno exclusivo (07-11)
- `ddd_core/m04_seed_engine.py`, `modulos/04_generar_semillas.py`, `modulos/05_optimizar_distritos.py`: «Implementador Motor» (T-44).
- `.claude/agents/`, `.claude/agent-memory/`, `evals/`: «Paso 1 agentes DDD» (T-38 a T-40).
- `herramientas/generar_hemiciclo.py` (nuevo) y plantillas del visor: «Implementador» (T-42).
- `.github/workflows/` lanzables y de publicación: «Implementador» solo para T-41, tras cerrar T-42; nadie más.
- `configuracion/politica_generacion_territorial_2025.yaml` y contratos `territorios/congreso_*`: libres; T-44 los pide
  al planificador si su tope agota el motor (decisión D-6).
- `docs/PLAN.md`: planificador. `docs/REGISTRO_DE_CAMBIOS.md`: número lo asigna el planificador al abrir cada PR.

## 2. Decisiones del propietario
### Tomadas (07-11 noche)
- D-8. El Observatorio Electoral de las Naciones (`nazioenbehatokia.eus`; Ion Ansa, Nora Galparsoro) se acepta como
  **fuente secundaria** para el histórico de generales (2011-2023, votos por partido y sección, seccionado INE de cada año),
  con contraste por muestreo frente a Infoelectoral y espejo propio con sha256 en el catálogo de procedencia (T-89).
  Se usa ya como contraste de T-71. Se pide permiso de reutilización a los autores (lo envía el propietario).
  La red del entorno Default permite `nazioenbehatokia.eus` (07-11).
### Pendientes
- D-5 (T-41). Crear en Settings → Environments el entorno `produccion` con el propietario como revisor requerido
  (repositorio público: disponible en cualquier plan). Sin él, T-41 se queda en el código.
- D-6 (T-44). Si tras el tope el motor no cierra una provincia: exención municipal, techo propio o documentarla
  como bloqueada (con la evidencia de T-44 delante).
- D-7 (T-42, T-43). Permiso de publicación en el visor del hemiciclo y de los ensembles de La Rioja y Sevilla
  (se da en el chat operador).
- D-4. Un cambio de M04 (T-44) invalida los checkpoints pre-M04 de los contratos con islas (Canarias, Islas Baleares,
  nacional Baleares, Las Palmas, Santa Cruz de Tenerife): visto bueno antes de que T-44 abra PR que toque M04.
- D-1. Completar Cantabria y Vizcaya por provincia o esperar a la activación por elección (T-04).

### Tomadas (07-11 noche)
- **R2:** se poda para quedar bajo los 10 GB gratuitos (T-76); el borrado solo con lista aprobada por el propietario.
  T-72 archiva solo el producto final.
- **Arquitectura de agentes (T-75, #474):** sí a los tres cambios: revisor obligatorio, allowlist de herramientas por rol en
  runtime y medir al Coordinador durante dos olas (coste por ola y fallos de coordinación).
- Red del entorno Default: `www.ine.es`, `www.mapa.gob.es`, `www.idescat.cat` (además de `boe.es`). `www.mapa.gob.es` resetea
  la conexión desde el proxy.
- **D-3:** se publica en el visor cada provincia al terminar su 00 (permiso por provincia en el chat del Operador).
- Secreto `CLAUDE_CODE_OAUTH_TOKEN` actualizado por el propietario (comprobar que el revisor corre en la próxima PR).
- Histórico 2019-11: todavía no. T-70 (D'Hondt): descartada.
- Archivo: R2 para el archivo de trabajo y Zenodo para versiones cerradas. Portal Zensical publicado en `/docs` del sitio.
- **T-64 (decisión del propietario):** nos quedamos con los partidos judiciales. #462 se reaplica en #470; la decisión de C-13
  sigue pendiente (#469).

### Tomadas (07-11)
- **Roles (07-11 noche):** el Coordinador (chat «Coordinador», Sonnet) es el socio operativo del propietario: recibe
  los cierres, sigue PR, CI y runs, archiva chats, junta lecciones y mantiene `docs/ESTADO.md`. El planificador solo
  planifica, por olas: cada ola, un chat nuevo que lee `PLAN.md` y `ESTADO.md`.
- **T-64 redefinida:** sin partidos judiciales de entrada. Estudio de comarcas no oficiales frente a partidos judiciales;
  si encajan razonablemente, se usan los partidos. #462 queda abierta sin fusionar hasta esa decisión.
- Cambios de criterio (unidades, fuentes, reglas): siempre se consultan al propietario antes de encargarlos.
- **Senado: descartado.** No tiene sentido para el proyecto; no se planifica ni se dedica tiempo alguno a él.
- D-4: visto bueno a M04 7.6.7 (Alicante); la próxima 00 de los territorios con islas empieza de cero.
- D-6 Málaga: exención de suelo municipal de Fuengirola (29054) en el contrato; techo y atomicidad sin cambios
  (Fuengirola 85.136 solo linda con Mijas y Benalmádena, atómicos; con cualquiera supera el techo).
- Una PR por objetivo, no por tarea (ver reglas).
- Fusiones sin intervención del propietario: el Operador fusiona por squash cada PR con `pruebas` en verde en la PR y en
  `main`, en el orden de la cola, y pone al día la siguiente (merge de `main`, sin force). Fallo de CI: no relanza; informa al
  planificador.
- Hemiciclo: primera entrega con las tres sumas sobre las 49 provincias completas, marcando las tres que faltan, con
  script y página en el visor (la publicación sigue necesitando permiso, D-7).
- Plan inmediato: §12 del framework en orden (oro, revisor y forense, Environments); producto en paralelo, a demanda
  y con tope.

### Tomadas (01-11)
- D-2: INE canónico; matrículas como alias, en español.
- #380 Cádiz y Barcelona: exención municipal en contrato y lanzamiento de 00.
- Álava: arreglar M04 para transferir varias secciones fronterizas (no exención ni aparcar).
- Madrid y Málaga: se mantiene la regla «un municipio que cabe bajo el techo no se divide»; reparación de población
  más profunda en contrato; si no basta, documentar como bloqueadas.
- Alicante: reparación más profunda (contrato). Pontevedra: reparación más profunda; si no basta, exención municipal.
- Las Palmas: exención municipal en contrato (no de toda Gran Canaria, 35-C01).
- Baleares: reparación más profunda (el reparto por islas no es viable: Ibiza+Formentera 1,41 de la media).
- Republicar en el visor La Rioja, Lugo, Santa Cruz de Tenerife y Tarragona.
- Ruleset: `puerta_admision` fuera de checks obligatorios (solo corre si la PR toca contratos).

## 3. Cola de tareas (07-11)
**Prioridad del propietario (07-11): poner en uso los agentes; nada le interrumpe hasta lograrlo.** Camino crítico:
fusionar #428 → #429 → #430 → #431 → T-38 (1.0.100) → T-39 (1.0.101) y T-40 (1.0.102). Producto (T-42 a T-44) en
pausa: sin PR, sin preguntas al propietario y sin lanzamientos hasta que el revisor y el forense estén en `main`.
T-41 va después. Las dudas de los chats van al planificador, no al propietario.

### T-38 · Conjunto de oro para revisor y forense (P1, §12 paso 4)
- Alcance: casos de evaluación en `evals/oro/`: las 12 causas raíz del §9 del framework (run o PR de referencia,
  síntoma, causa esperada en una línea) y ADV-01 a ADV-16 de `docs/ARQUITECTURA/referencias/AUDITORIA_CHATGPT_PLAN_V2_2026-11-02.md`
  §7.2 (diff o PR original, defecto esperado), más los casos de calibración 29E del metaagente («candidato modificado
  tras la revisión», «reparaciones agotadas con criterio fallido»). Un JSON por caso con esquema común y
  `herramientas/evaluar_oro.py` (biblioteca estándar) que puntúa una salida JSON de agente contra lo esperado y anota en
  `evals/oro/LIBRO_DE_COSTES.md` tokens, acierto y si fue a la primera.
- Fuera: crear agentes (T-39, T-40); lanzar nada; descargar artefactos (los casos citan PR, runs y `diagnostico/*`).
- Dependencias: #427-#430 fusionadas.
- Turno exclusivo: `evals/`, `herramientas/evaluar_oro.py` (nuevo).
- Chat: «Paso 1 agentes DDD». Modelo: Opus.
- Hecho: ≥ 30 casos con fuente verificable (PR, run o fichero en `main`); el evaluador da 100 % con la salida esperada y
  0 % con una vacía (test en `tests/`); gobernanza R015 y guardián de `main` en verde; PR con su número de registro.

### T-39 · Subagente revisor independiente (P1, §12 paso 5)
- Alcance: `.claude/agents/revisor.md` (Sonnet, solo lectura, salida JSON con veredicto ligado al SHA del HEAD:
  unidades y CRS, gobernanza VERSIÓN/legacy, huellas M05/N08, numeración del registro, tests rojo/verde); la skill
  `revisar-pr` lo invoca.
- Dependencias: T-38.
- Turno exclusivo: `.claude/agents/revisor.md`, `.claude/skills/revisar-pr/`.
- Chat: «Paso 1 agentes DDD».
- Hecho: sobre el diff original de los casos de revisión del oro caza ≥ 80 % de los defectos y no bloquea ninguna de
  tres PR limpias ya fusionadas; resultados y coste en el libro; primera revisión real: #425.

### T-40 · Subagente forense de runs (P1, §12 paso 5)
- Alcance: `.claude/agents/forense.md` (Sonnet, solo lectura; dado un run da la causa en cinco líneas) y
  `.claude/agent-memory/forense/MEMORY.md` con el catálogo de causas del §9; la skill `diagnosticar-run` lo invoca.
  Lee anotaciones (`check-runs/<job>/annotations`) y `diagnostico/auto/`, nunca artefactos.
- Dependencias: T-38. En paralelo con T-39 (ficheros distintos).
- Turno exclusivo: `.claude/agents/forense.md`, `.claude/agent-memory/forense/`, `.claude/skills/diagnosticar-run/`.
- Chat: «Paso 1 agentes DDD».
- Hecho: causa correcta en ≥ 10 de los 12 runs del oro, en ≤ 5 líneas; coste por diagnóstico anotado en el libro.

### T-41 · Lanzamientos y publicaciones con Environments y aprobación (P2, §12 paso 6)
- Alcance: los jobs con efecto (00 manual, «Activación por Elección», «05 Publicación del Visor», publicación de
  ensembles) declaran `environment: produccion`, de modo que cada dispatch espera el clic del propietario en GitHub
  (sin modelo). Los encadenados de `github-actions[bot]` y los registros con la app `ddd-registro` no deben quedar
  esperando: el entorno se aplica solo al dispatch manual (expresión en `environment`) o se documenta la excepción.
  Actualizar las skills `operador`, `lanzar-00` y `publicar-visor` (el operador pasa a preparar y verificar).
- Dependencias: D-5; T-42 cerrada (mismo chat); Paso 1 fusionado.
- Turno exclusivo: `.github/workflows/ejecucion-completa-proyecto.yml`, `activacion-*`, `desplegar-visor-publico.yml`,
  `_reutilizable-publicar-sitio.yml`, workflow de escenarios/ensembles; skills citadas.
- Chat: «Implementador» (código) + «Operador» (una sola prueba con permiso).
- Hecho: un dispatch manual queda en «Waiting» hasta aprobar y corre tras el clic; una 00 encadenada por el bot no
  espera; los robots registran en `main` sin `GH013`; suite de gobernanza de workflows en verde; validado con una sola
  ejecución antes de abrir paso al resto (regla de infraestructura).

### T-42 · Hemiciclo y tabla de resultados (P2, producto; alcance confirmado 07-11)
- Alcance: `herramientas/generar_hemiciclo.py` lee los M08 registrados de las 49 provincias completas y suma escaños de
  tres maneras: (a) reparto real 2023 (D'Hondt oficial), (b) elección anterior (generales 2019-11, si el repositorio
  tiene sus resultados; si no, la columna queda marcada «sin fuente» y se abre subtarea), (c) uninominal propio
  (ganador por distrito DDD). Salida JSON y CSV con totales de España por partido y lista de provincias que faltan
  (Málaga, Barcelona, Alicante); página del visor con hemiciclo SVG y tabla, conmutando las tres sumas.
- Fuera: publicar (D-7, chat operador); cambiar M08 o el motor.
- Dependencias: ninguna de código (puede empezar ya; la PR va tras la cadena #427-#430).
- Turno exclusivo: `herramientas/generar_hemiciclo.py`, plantilla/página nueva del visor.
- Chat: «Implementador». Modelo: Sonnet.
- Hecho: (a) en las 49 provincias coincide escaño a escaño con el oficial por provincia; (c) suma exactamente los
  distritos de esas 49 (uno por distrito); test con dos provincias sintéticas; página revisada en local con captura;
  topónimos en español y etiqueta «Nacional»; registro con su número.

### T-43 · Publicar los ensembles de La Rioja y Sevilla (P3, operador)
- Alcance: con la skill `publicar-visor`, republicación de ensemble con `ensemble_sha256` (#418, #421, #424) para
  `congreso_la_rioja` y `congreso_sevilla`; primero La Rioja como prueba, luego Sevilla. Solo añade en `ensembles`.
- Dependencias: D-7 (permiso en el chat operador). Sin código.
- Turno exclusivo: ninguno (escribe el workflow en `orchestracion/publicaciones_visor.json`).
- Chat: «Operador». Modelo: Sonnet.
- Hecho: `publicaciones_visor.json` con las dos entradas de ensemble y el visor mostrando 10 candidatos en cada una;
  línea de cierre al planificador con los runs.

### T-44 · Málaga, Barcelona y Alicante: estudio de motor con tope (P2, producto)
- Alcance: diagnóstico y arreglo del motor en local con los volcados de `diagnostico/auto/` (o pedir M01+M03 al Mac):
  Barcelona primero (hard=1, la más cerca), luego Alicante y Málaga. Sin cambiar suelo, techo, K ni atomicidad.
- **Tope**: dos ciclos de reparación por provincia (regla de la auditoría) y ninguna 00 sin M05 hard=0 y M06 OK en
  local. Agotado el tope, informe de factibilidad (¿existe partición sin partir municipios que caben bajo el techo?)
  y la provincia pasa a D-6.
- Dependencias: ninguna; si toca M04, D-4 antes de la PR.
- Turno exclusivo: `ddd_core/m04_seed_engine.py`, `modulos/04_generar_semillas.py`, `modulos/05_optimizar_distritos.py`.
- Chat: «Implementador Motor». Modelo: Opus.
- Hecho: por provincia, M05 hard=0 y M06 OK en local con el motor nuevo, o informe de factibilidad para D-6; sin
  regresión (GeoJSON e informe idénticos en Pontevedra, Álava y Cádiz); suite completa en local; una PR por causa.
  Luego la 00 «Ejecutar desde el principio» la pide al planificador (lanza el operador con permiso, un territorio de prueba primero).

### Lote del 07-11 (tarde) · autorizado por el propietario; sin intervenir hasta el final
Orden de fusión (Operador): #430 → #436, luego T-46 y el resto según lleguen. Al final, una sola lista para el
propietario: ajustes de Settings y permiso de las 00.

| Id | Objetivo | Chat | Turno exclusivo | Hecho |
|---|---|---|---|---|
| T-46 | Registro por ficheros (`docs/registro/`, número asignado por la CI al fusionar) y delegación del qué en el planificador dentro de `CLAUDE.md` | «Implementador nuevo» (Opus) | guardián, reglas y skills de registro, `CLAUDE.md` | Dos PR en paralelo no chocan en el registro; última PR con número manual (1.0.105) |
| T-48 | Revisor en cada PR y forense en cada 00 fallida, en CI (`claude-code-action`) | «Implementador nuevo» | dos workflows nuevos | Sin secreto se saltan limpiamente; con él, veredicto en la PR e issue con la causa |
| T-47 | Archivista R2: copia con sha256 de los artefactos antes de caducar, manifiesto `orchestracion/archivo_r2.json` | «T-47 Archivista R2» (Sonnet) | `archivar-artefactos-r2.yml`, herramienta nueva | Idempotente y con tests; una ejecución tras fusionar (permiso dado) |
| T-41 | Environments con aprobación solo en el dispatch manual | «T-42 Hemiciclo» (Sonnet), tras T-45 | workflows lanzables y de publicación | Los encadenados del bot no esperan; gobernanza de workflows en verde |
| T-45 | Proclamación oficial de 2023 (BOE) como dato para el hemiciclo | «T-42 Hemiciclo» | datos del hemiciclo | Contraste por provincia; diferencia CERA ubicada |
| T-49 | `decided_at`, `reason` y `evidence` en las 17 exenciones, comprobador en CI y `CONTRACT_POLICY_STALE` | «T-49 Exenciones gobernadas» (Sonnet) | política y contratos (salvo Málaga hasta #436) | Exención sin metadatos = CI en rojo |
| T-07 | Andalucía en local (motor) | «Implementador Motor» (Opus), tras #436 | motor | M05 hard=0 y M06 OK en local o evidencia para decisión |

Pendiente para la lista final del propietario: «Allow auto-merge» (P2), entorno `produccion` con revisor (D-5),
secreto `CLAUDE_CODE_OAUTH_TOKEN` (T-48) y permiso de las 00 de Barcelona, Alicante, Málaga y Andalucía.
La red del entorno Default ya permite `www.boe.es` y `boe.es` (07-11).

### Ola 2 (07-11 noche) · solo completar territorios y dejar el Gestor listo para la legislatura vigente
Histórico aplazado hasta entonces (T-81 a T-85 no se encargan); los votos por partido de 19 provincias esperan. R2: el
sobrecoste es de unos 23 céntimos al mes; no se poda (T-76 cerrada, #480 sin fusionar). Hecho de la ola: 52/52 y 19/19
«Cadena completa validada» y en el visor.

| Id | Objetivo | Quién | Estado |
|---|---|---|---|
| T-79 | Nacional: Alicante y Málaga (00 en `produccion`; si fallan: forense, reparación con el tope de T-44 en chat Opus de motor); Barcelona: completar electoral; Ceuta: 00 según forense (pob. INE 3826 ≠ M06 3723). Cada uno se publica al terminar (D-3) | Coordinador + Operador | Barcelona territorial success; Alicante en curso; Málaga en cola |
| T-80 | Andalucía autonómica: 03 falló por paquete electoral caducado (run 37150399030); preparar con `reutilizar=false`, `prepare_one`, 00 Reutilizar y publicar | Coordinador + Operador | Pendiente de permiso del propietario |
| T-86 | Gestor listo para la legislatura vigente | chat Opus del planificador | En curso |

### Ola del 07-11 noche
Cierres al Coordinador. Alcance y criterio de hecho: los del encargo de cada chat.

| Id | Objetivo | Chat | Hecho |
|---|---|---|---|
| T-72 | Archivo en origen: M06/M08 a R2 con sha256 en `registrar`, composición y votos por run | session_01KQDtFtH5s6XFb1sTEQE75B (Opus) | Fusionada (#471); falta una 00 de prueba (Operador, permiso del propietario) |
| T-71 | Recuperar composición y votos por partido de las 47 provincias sin ejecuciones (centroides INE 2023 sobre el M06 publicado) | session_01KQDtFtsKtpcWSzdeGAmwMS (Sonnet) | ≥ 40 de 47 exactas; las que no cuadren, a 00 con motivo. Añadido (D-8): contrastar los votos por partido y sección de 2023 con `nazioenbehatokia.eus/data/202307/sekzioa/{cpro}.json` e informar de las discrepancias |
| T-74 | Catálogo de procedencia único (`orchestracion/catalogo_procedencia.json`, derivado de 5 ficheros) | session_01KQDtFs6b53QY496wZn2gSX (Opus) | PR #473; check en CI |
| T-73 | Portal Zensical público (P3) en `/docs` del sitio, dentro de `_reutilizable-publicar-sitio.yml` | por abrir, tras T-71 (Sonnet) | `zensical build --strict` en verde, enlaces comprobados; sin publicar |
| T-75 | Aplicar el metaagente a DDD (solo documentación) | session_01KQDtFvFEZ1wPrxBQpGsj9w (Opus) | En curso |
| T-76 | Podar R2 bajo 10 GB; borrado solo con lista aprobada | session_01KQDtFtGG21KnDVVU6JUnni | En curso |
| T-77 | Incorporar T-75: estado de tarea y de efecto externo, línea de cierre ampliada, ficha del ingeniero de motor, topes y libro de costes por chat | session_01KQDtFsDv6WYYdvBHC1Ji7t (Sonnet) | Skills y fichas coherentes; PR con registro |
| T-78 | Gobierno de agentes en runtime: allowlist por rol y revisor como check obligatorio (JSON del ruleset, lo aplica el propietario) | session_01KQDtFru1JVfTuBosCwaVsu (Opus) | Herramienta denegada se bloquea; PR no-automerge |
| T-87 | Cadena de publicación con una sola aprobación: al cerrar la puerta 04 de una 00, un job en el entorno `produccion` (aprobación del propietario) dispara juntos la 05 del visor con `production_run_id` de esa 00 y `publicar-version-mapa.yml` (Release, Zenodo); el archivo R2 lo cubre T-72 y los resultados ligeros ya se encadenan con `publicaciones_visor.json`. Toca workflows compartidos: avisar al Coordinador | por abrir (Opus), después de la 00 de prueba de T-72 | PR no-automerge; sin aprobación no publica nada; probado con un territorio y sin publicar hasta el permiso del propietario |
| T-88 | Revisar las skills de verificación de plan y TDD de `mattpocock/skills` (MIT) y, ampliada (07-11), los plugins oficiales de revisión de PR y de desarrollo por fases de `anthropics/claude-code` frente a `revisar-pr`, el revisor de CI e `implementador`; llevar a `implementador` y `planificador` solo lo que falte, con el criterio de `disenar-agente`; sin instalar skills externas | por abrir (Sonnet), después de T-77 | Una PR con la comparación (qué se toma, qué no y por qué) y las skills ajustadas; sin aumentar el contexto cargado por defecto |
| T-89 | Espejo del Observatorio Electoral de las Naciones (D-8): bajar `data/index.json`, `data/{k}/sekzioa/{cpro}.json` de las 6 generales y `geo/sekzioak/{año}/{cpro}.json` de sus 6 seccionados, con fecha, URL y sha256 por fichero, a R2 (no a git); entrada en el catálogo de procedencia; contraste por muestreo (3 provincias × 2 elecciones) con Infoelectoral 2023 del release espejo y un lector Python del formato compacto (`s`,`k`,`f`,`b`,`r`) | por abrir (Sonnet) | Espejo completo y verificable; informe del contraste; sin publicar ni tocar el visor |
| T-64 | Estudio comarcas frente a partidos judiciales | cerrado; PR #469 | Pendiente: C-13 (decisión del propietario) |

## 3b. Histórico de la cola (01 a 03-11)

### T-15 · Las Palmas falla en M08 tras #394 (P0, BUG)
- Run 00 41358199178: reutiliza el M06 de 41336103808, M07 queda OK y la validación da «distritos bajo límite poblacional=1» (exit 3).
- Causa 1: las secciones M06 de Mogán (35012) no traen `DDD_MUNICIPALITY_PARTITION`; el validador lo resuelve con respaldo a CUMUN/CUSEC · PR #398 · registro 1.0.70.
- Causa 2 (reproducida en local con M01/M03 del run): la reparación M05 movía Mogán (exento) al distrito deficitario y dejaba sin exención al que lo perdía. Las unidades de municipios exentos quedan ancladas · PR #399 (fusionada) · registro 1.0.71.
- #398 y #399 fusionadas; Las Palmas relanzada con la 00 «Ejecutar desde el principio» (M05 está en la huella).

### T-16 · Endurecer el diagnóstico automático de T-14 (P1)
- T14-01 linaje por rutas del contrato (sin mtime) · T14-02 paquete PARTIAL · T14-03 `MANIFEST.json` con sha256 · T14-04 resultado del rebase · T14-05 `DIAG_PUBLISH_FAILED` · PR #401 (fusionada) · registro 1.0.72.
- Pendiente: una 00 de prueba que falle a propósito (permiso del propietario).

### T-17 · Tabla de las 52 provincias (operador, solo lectura)
- Estado por provincia (M06, electoral, visor, causa de PARADA) a partir de `estado_operativo.json` y los manifiestos de ejecución. Sin lanzar nada.

### T-18 · Causa de Cádiz y Baleares (operador)
- Runs 41417528357 (Cádiz) y 41417532454 (Baleares): `POPULATION_HARD_BLOCK` con techo 1,15 en lugar del de la política. Se leen los informes M05 de `diagnostico/auto/<territorio>/<run>/`.
- Resuelta por T-20.

### T-19 · Factibilidad de Madrid y Málaga (solo lectura)
- Calcular si existe alguna partición sin partir municipios enteros bajo el techo (distritos 52 y 10 de T-02b). Sin 00. Alimenta el estudio de motor (sección 5).

### T-20 · Techo de Cádiz y Baleares (RESUELTA)
- Causa: `materialize` trataba como `already_complete` los contratos con M01–M06 y no reaplicaba `population_limits` de la política (el contrato conservaba 1,15). Arreglo: `apply_policy_population_limits` · PR #403 · registro 1.0.74. Baleares pasa a 1,28 (T-24).

### T-21 · Inventario de excepciones gobernadas (solo lectura, hecha)
- 71 contratos, 165 entradas. `limits_profile: exception` marca en 53 territorios la regla del Congreso (1,15) y no una desviación real; desviaciones reales: techos de Cádiz, Baleares y Las Palmas; atomicidad de Andalucía, Cataluña, País Vasco y Valencia; suelo de Melilla. Las 9 exenciones municipales de suelo no tienen `decided_at`/evidencia estructurada (pendiente de prioridad baja: moverlas a la política).

### T-22 · Estudio de motor (en curso, PR #419)
- M04 7.6.6, alivio de residuos municipales sobre el techo (`m04_overcap_residual_relief`): residual → núcleo, municipio entero → distrito del residual vecino y núcleo → núcleo, siempre dentro del mismo municipio dividido y con conexidad comprobada. No cambia suelo, techo, K ni atomicidad; no toca M05. Resuelve Murcia (con la exención de Águilas) y Madrid en local; mejora Alicante y Barcelona sin cerrarlas; Málaga queda igual.

### T-23 · Murcia (hecha, sin PR)
- INE: Águilas 30003, Puerto Lumbreras 30033. Con la exención de Águilas desaparece el bloqueo de Lorca; queda el distrito 4 (Murcia residual + Alcantarilla + Beniel = 171.010 > 137.265): bloqueo del motor → T-22.

### T-24 · Baleares 1,28, gate de Cádiz y cierre de Las Palmas (hecha)
- Baleares techo 1,28 (política 1.7.4) y M05 7.8.7 (exención municipal por el campo de municipio, Cádiz) · PR #404; tests negativos de Las Palmas y decisión de 35012 · PR #405.

### T-25 · Escenarios de otro algoritmo: lectura (hecha)
- Una 00 del Gestor con otro algoritmo sobre una provincia completa registraba su producto como el canónico (`persist_state` verdadero). Recomendación: ensemble por territorio (vía A) y escenarios que no registran.

### T-26 · Ensemble genérico por territorio (hecha, #406)
- «06 Escenarios y Ensembles» (workflow_dispatch) con configuración por territorio; Aragón idéntico; el resto obtiene M01–M05 sin registrar; fase `ensemble_10`, el 50 sigue bloqueado.

### T-27 · Todos los escenarios en el visor (en curso, 3 fases)
- **(a) Registro** con `scenario_m06/m08`, `scenario_id`, `strategy`, `scenario_kind`, `canonical` · PR #413 · **fusionada**.
- **(b) Selector** con `optgroup` por escenario y conmutador Territorial/Electoral · PR #414 · **fusionada**.
- **(c) Escenarios sin catálogo**: `persist_state` falso en campañas de otro algoritmo sobre territorio certificado y promoción como escenario (`scenario_id`, `scenario_strategy`) · PR #415 · **fusionada**.
- Pendiente tras las tres: una ejecución real de un escenario completo (territorial y electoral) y su publicación en el visor.

### T-28 · Cádiz: receipt electoral sin linaje (hecha, #407)
- `electoral_product_available: false`; la 00 «Reutilizar» rehace 03/04 sobre el M06 vigente.

### T-29 a T-33 · Piloto de ensemble de Salamanca (hechas)
- T-29 poda de aristas débiles (#408); T-30 lectura: las geometrías del Congreso están en grados; T-31 medir la frontera compartida en metros (#409); T-32 el runner del ensemble ya no sale en verde con fallos (#410); T-33 unir las piezas de secciones MultiPolygon como M06 (#411). Resultado: Salamanca ensemble_10, 10/10 candidatos (run 41543954069).

### T-34 · Ensemble en La Rioja y Sevilla (hecha, #417)
- `configuracion/ensemble/congreso_la_rioja.json` (K=3) y `congreso_sevilla.json` (K=16; Valencia descartada por su puente gobernado). Resultado: 10/10 candidatos en las dos (Sevilla con 4 hashes únicos).

### T-35 · Publicación de ensembles con `ensemble_sha256` (hecha, #418)
- El publicador único exige el hash del zip del release; `publish` y `republish` lo calculan, lo exponen y los despliegues lo pasan. La publicación de Salamanca (run 41592019959) fallaba con exit 56. La republicación sin recalcular vale para cualquier territorio con configuración (ensemble_10), no solo Aragón-10; el 50 sigue bloqueado. Solo añade en `ensembles`.

### T-14 · Diagnóstico automático sin el Mac (máxima prioridad tras T-13)
- Objetivo: cuando una 00 falla en M04, M05 o en la puerta de certificación, el propio workflow sube a la rama
  `diagnostico/auto` (carpeta `<territorio>/<run>/`) el M01, el grafo M03 (gz) y el informe M05, para que los
  chats ejecuten el motor en local sin descargar artefactos (403 desde la nube) ni depender del Mac.
- Rol: implementador. Modelo: Opus.
- Ficheros afectados: `_reutilizable-generacion-territorial.yml` (paso `if: failure()` tras M04/M05/certificación),
  herramienta nueva en `herramientas/` para empaquetar y publicar con la credencial de registro (#386), test.
  Workflow compartido: turno del planificador.
- Criterio de aceptación: una 00 que falle en M05 deja en `diagnostico/auto` los tres ficheros en menos de 5 minutos;
  con ellos `python -m ddd_core.m04_seed_engine` y `modulos/05_optimizar_distritos.py` reproducen el fallo en local;
  una 00 correcta no sube nada; tamaño por territorio < 50 MB.
- Prueba local exigida: suite completa + test del empaquetado + una 00 de prueba que falle a propósito (con permiso).
- Dependencias: ninguna. Sustituye a `lanzadores/subir_diagnostico_t02.sh`.

### T-08 · Proteger `main` con CI obligatoria
- Objetivo: impedir fusionar sin «pruebas» en verde y con la rama al día con `main` (lo que ocurrió con #374).
- Rol: operador (lo aplica el propietario: requiere permisos de administrador). Modelo: Haiku.
- Ficheros afectados: ninguno; ajuste del repositorio (Settings → Branches o ruleset sobre `main`):
  check obligatorio `pruebas`, «Require branches to be up to date», sin push directo. Comprobar antes que
  los robots de registro (catálogo, `estado_operativo.json`, activos del visor) que escriben en `main`
  quedan exentos o pasan por PR; si no, la protección los bloquea.
- Criterio de aceptación: una PR con «pruebas» en rojo o pendiente no se puede fusionar; los robots siguen
  registrando sin fallos durante una ejecución 00.
- Prueba local exigida: ninguna; verificación con `gh api repos/jfmurciego/DiputadodeDistrito/branches/main/protection`
  (o rulesets) y una ejecución 00 posterior con registro correcto.
- Dependencias: T-10 para reactivar. Máxima prioridad.
- Estado (2026-11-01): ruleset `proteger-main` (id 26311854) creado con PR obligatoria, check `pruebas` y rama
  al día (`puerta_admision` retirado: solo corre si la PR toca contratos y dejaba las demás en espera eterna).
  **Desactivado**: la app GitHub Actions no se puede añadir a los exentos y los robots de registro
  (`git push origin main` en 00, generación, operación, publicación del sitio y orquestación) quedarían bloqueados.
  Se reactiva al cerrar T-10.


### T-10 · Robots de registro con token propio (desbloquea T-08)
- Objetivo: que los workflows que hacen `git push origin main` lo hagan con un token de GitHub App propia
  (o PAT de grano fino) que pueda figurar como exenta en el ruleset, para reactivar `proteger-main`.
- Rol: implementador (workflows) + propietario (crear la app o el PAT y el secreto). Modelo: Opus.
- Ficheros afectados: `.github/workflows/ejecucion-completa-proyecto.yml`, `orquestacion-durable.yml`,
  `_reutilizable-generacion-territorial.yml`, `_reutilizable-operacion-territorial.yml`,
  `_reutilizable-publicar-sitio.yml` (paso de checkout/push con el token del secreto). Workflows compartidos:
  avisar a las demás sesiones antes.
- Criterio de aceptación: con el ruleset activo y la app exenta, una 00 registra en `main` sin
  «rule violations»; una PR sin `pruebas` en verde no se puede fusionar.
- Prueba local exigida: suite completa (incluye tests de gobernanza de workflows) + `actionlint` si está disponible.
- Dependencias: el propietario crea la GitHub App o PAT y el secreto. No reactivar el ruleset con 00 en curso.

### Resultado de T-01 (2026-11-01, `estado_operativo.json` de las 11:06 + anotaciones y logs de los jobs)
- Completas (32): Albacete, Almería, Ávila, Cáceres, Castellón, Ciudad Real, Córdoba, La Coruña, Cuenca, Gerona,
  Granada, Guadalajara, Huesca, Jaén, León, La Rioja, Lugo, Orense, Asturias, Palencia, Salamanca,
  Santa Cruz de Tenerife, Segovia, Sevilla, Soria, Tarragona, Teruel, Toledo, Zamora, Zaragoza, Ceuta, Melilla.
  En Huesca, La Rioja, Lugo, Santa Cruz de Tenerife y Tarragona el último run falló solo en 05 (visor), sin efecto en M08.
- M06 sin electoral (8): Badajoz, Burgos, Guipúzcoa, Lérida, Navarra, Cantabria, Valladolid, Vizcaya
  (lanzadas con alcance territorial; `main` registra después ejecuciones completas de Badajoz, Burgos, Lérida,
  Navarra y Valladolid: confirmar en el próximo estado operativo).
- PARADA (12), por causa:

| Causa | Provincia | Run | Detalle |
|---|---|---|---|
| Población (M05 `POPULATION_HARD_BLOCK`) | Alicante | 41293667422 | hard=1, desviación máx. 0,36 |
| | Barcelona | 41244711464 | hard=2, 0,30 |
| | Cádiz | 41243953699 | hard=2, 0,18 |
| | Madrid | 41244835816 | hard=1, 0,56 |
| | Málaga | 41293427148 | hard=1, 0,38 |
| | Pontevedra | 41293311168 | hard=1, 0,25 |
| | Baleares | 41250230577 | hard=2, 0,67 (con #370; revisar `component_districts`/exenciones) |
| | Las Palmas | 41250283081 | hard=1, 0,46 (con #370; techo 1,40 insuficiente o reparto no aplicado) |
| Población (M04, estructural) | Álava | 41240137880 | residual de Vitoria (01059) 0,72 bajo suelo; sin sección transferible |
| Conectividad (pre-M04) | Murcia | 41293548832 | «grafo territorial no supera conectividad administrativa», ya con #371 |
| Geometría fuente (01) | Huelva | 41292468775 | `GEOMETRY_INVALID_AUDITED`: secciones INE con huecos interiores sin máscara de cobertura |
| | Valencia | 41293787892 | ídem |

### T-02 · Diagnosticar y relanzar las PARADA
- Objetivo: corregir la causa de cada grupo de PARADA (empezando por M02 con puentes heredados 2024/2025,
  Huelva y Valencia) y dejar un script de relanzamiento para el Mac.
- Rol: implementador (corrección) + operador (relanzamiento por script). Modelo: Opus.
- Ficheros afectados: probablemente `herramientas/generar_provincias_congreso.py`, contratos
  `territorios/congreso_*/config/`, `particiones_insulares_2025.json`,
  `configuracion/politica_generacion_territorial_2025.yaml`; script en rama `lanzadores-mac`.
  Avisar antes de tocar `herramientas/`, `modulos/`, `ddd_core/` o la política.
- Criterio de aceptación: cada provincia PARADA llega al menos a M06 validado en un run nuevo; ninguna
  regresión en las 28 completas.
- Prueba local exigida: suite completa + diagnóstico local de M02/M04/M05 por provincia afectada con el grafo
  subido a `diagnostico/…` (ver `CLAUDE.md`, «Diagnóstico local»).
- Dependencias: T-01. Una PR por causa, no por provincia.

### T-02b · Bloqueos de población M05 (2026-11-01)
Runs 00 de las 16:40 (reparación profunda: profundidad 6, conjunto 3, 500.000 candidatos, 300 s). La reparación no mejoró ningún exceso: el bloqueo es estructural (municipios enteros indivisibles bajo el techo, regla del propietario).

| Provincia | Run | Distrito | Población | Límite | Exceso | Municipios enteros |
|---|---|---|---|---|---|---|
| Madrid | 41327479240 | 52 | 181.853 | techo 133.943 | +47.909 | Pozuelo (28115, 88.504), Boadilla (28022, 64.635) y 28181 (28.714) |
| Málaga | 41327483858 | 10 | 161.454 | techo 134.376 | +27.078 | 29054 (85.136) y 29025 (76.318) |
| Alicante | 41327488604 | 12 | 156.889 | techo 132.268 | +24.620 | trozo de 03065 (119.050) y 03121 (37.839) |
| Barcelona | 41327510776 | 31 | 150.148 | techo 133.339 | +16.809 | 08015 (112.242) y 08194 (37.906); el distrito 40 (08073) va exento del suelo |

**Estado: BLOQUEADAS por estructura (Madrid, Málaga, Alicante, Barcelona y Murcia).** Quedan para un futuro estudio de motor. Palancas descartadas: bajar `municipality_atomicity_limit_ratio` (contradice la regla de no partir un municipio que cabe bajo el techo) y subir el techo (Barcelona 31 está a 1,29 de la media).

Resueltas por decisión del propietario: Cádiz (techo 116 % solo en Cádiz, política 1.7.3, distrito 8 a 1,159 de la media), Pontevedra (exención municipal 36008), Las Palmas (exención municipal 35012). Baleares: techo 127 % solo en Baleares (política 1.7.3; distrito 5 de Mallorca a 1,261 de la media, la reparación profunda no lo mejoró).

### T-09 · Huella de puentes heredados antes de M02
- Objetivo: comprobación previa que detecte puentes municipales heredados de 2024/2025 que ya no casan con el
  inventario municipal y la geometría vigentes, y bloquee con mensaje claro antes de lanzar M02 (evita PARADA).
- Rol: implementador. Modelo: Opus.
- Ficheros afectados: `herramientas/generar_provincias_congreso.py` (o nueva herramienta de comprobación en
  `herramientas/`), paso previo del workflow que lanza M02, tests nuevos en `tests/`. Avisar antes de tocar
  `herramientas/` y workflows.
- Criterio de aceptación: para cada provincia nacional, informe de puentes (válido / municipio inexistente /
  municipios no colindantes ni enlazables / código INE cambiado); las provincias que pararon en M02 por
  puentes (T-01/T-02) salen marcadas; las 28 completas salen limpias.
- Prueba local exigida: suite completa + ejecución de la comprobación sobre todos los contratos
  `territorios/congreso_*` + test con un puente roto sintético.
- Dependencias: T-01 (causas de PARADA). Va detrás de T-02 en prioridad; si T-02 corrige puentes, se apoya en ello.

### T-04 · Completar electoral de las provincias con M06
- Objetivo: llevar las 11 provincias con M06 (y las que salgan de T-02) a M08 con la activación por elección.
- Rol: operador. Modelo: Sonnet.
- Ficheros afectados: ninguno de código; script de lanzamiento en `lanzadores-mac`.
- Criterio de aceptación: 52/52 provincias nacionales con «Cadena completa validada» en el estado operativo.
- Prueba local exigida: ninguna (lanzamiento); comprobación del estado con `generar_estado_operativo.py`.
- Dependencias: T-02, T-03, D-1, permiso explícito del propietario.

### T-05 · Renombrado visible a «nacional»
- Objetivo: en visor, dashboard, informes y textos públicos, «nacional» en lugar de «congreso»; sin
  «circunscripción» en lo visible; topónimos en español. Los identificadores internos (`congreso_*`) no cambian.
- Rol: implementador. Modelo: Sonnet.
- Ficheros afectados: `herramientas/generar_estado_operativo.py`, plantillas del visor, generadores de
  nombres visibles (`display_name`), documentos públicos.
- Criterio de aceptación: `grep -ri "congreso\|circunscripci"` sobre las salidas visibles (visor, dashboard,
  `estado_operativo.json` campos `name`/`display_name`) sin coincidencias; claves internas intactas.
- Prueba local exigida: suite completa + regenerar estado operativo y visor en local y revisar el grep.
- Dependencias: ninguna (mejor tras T-03 si toca los mismos generadores).

### T-06 · Gestor de Campañas con provincias
- Objetivo: el selector del Gestor admite las elecciones nacionales por provincia además de las 19 autonómicas.
- Rol: implementador. Modelo: Sonnet (Opus si exige cambiar el modelo de datos).
- Ficheros afectados: módulo/plantillas del Gestor de Campañas y su catálogo de ámbitos.
- Criterio de aceptación: el selector lista las 52 provincias con nombre en español y etiqueta «nacional»;
  abrir una provincia completa carga sus distritos y resultados.
- Prueba local exigida: suite completa + prueba del selector con una provincia (Huesca).
- Dependencias: T-03 (clave de elección), T-05. Prioridad secundaria.

### T-07 · Andalucía (al final)
- Objetivo: generar y validar distritos de Andalucía y completar su cadena.
- Rol: implementador + operador. Modelo: Opus.
- Ficheros afectados: contrato de Andalucía, política (`population_limits`, exenciones), lanzador del Mac.
- Criterio de aceptación: Andalucía con «Cadena completa validada»; 19/19 autonómicas.
- Prueba local exigida: suite completa + diagnóstico local M04/M05 con el grafo de Andalucía.
- Dependencias: T-04 terminada.

## 4. Tareas hechas
<!-- Formato: T-xx · resumen · PR #nnn / run nnnnnnnnnn · fecha -->
- T-43 · Ensembles de La Rioja y Sevilla publicados como escenario (`ensembles=3`, 157 productos, canónicos intactos) · runs 42384534739 42385012998 · 2026-11-07
- Paso 0 y Paso 1 (bloques 1-3) · framework, guardián de `main`, `CLAUDE.md`/`rules/`/hook y skills de rol · PR #427 #428 #429 #430 · 2026-11-07 (pendientes de fusión)
- T-22 · M04 7.6.6, alivio de residuos sobre el techo; cierra Madrid y Murcia · PR #419 · 2026-11-03
- T-23 · Murcia: exención de suelo de Águilas (30003) · 2026-11-03
- T-35, T-36, T-37 · publicación de ensembles: `ensemble_sha256`, candidatos en WGS84, una feature por distrito · PR #418 #421 #424 · 2026-11-03
- T-14 · Diagnóstico automático: M01, grafo M03 e informe M05 a `diagnostico/auto/<territorio>/<run>/` si falla M04, M05 o la certificación · PR #397 · 2026-11-01
- T-02 · Huelva y Valencia (CRS 25830, #374) y Álava (M04 7.6.0 multisección, #383; 00 41346917857) completas.
  Murcia BLOQUEADA por estructura (objetivo 119.361, suelo 101.457, techo 137.265): Lorca 97.904 + Águilas 36.684 +
  Puerto Lumbreras 17.507 = 152.095 (Águilas y Puerto Lumbreras solo lindan con Lorca; atomicidad 0,80 aborta M04);
  residual de Murcia 116.508 + Alcantarilla 43.040 + Beniel 11.462 = 171.010 (1,43), enclaves sin cabida en núcleos
  cerrados exclusivos. Pasa al estudio de motor (sección 5) · PR #374 #383 · 2026-11-01
- T-08 · Ruleset `proteger-main` activo (PR obligatoria, check `pruebas`, rama al día; exentos administrador y app `ddd-registro`) · ajuste del propietario · 2026-11-01
- T-05 · Nombres visibles «Nacional …» en estado operativo, dashboard y visor; identificadores sin cambios · PR #385 · 2026-11-01
- T-06 · Gestor de Campañas con «Nacional 2023» (52 provincias por INE, matrícula o nombre) · PR #388 · 2026-11-01
- T-09 · Comprobación de puentes heredados antes de M02 (28 puentes en 20 provincias, válidos) · PR #390 · 2026-11-01
- T-10 · Robots de registro con app propia `ddd-registro` (exenta en el ruleset); probado en Baleares 41339398026 · PR #381 + #386 · 2026-11-01
- T-11 · Dashboard sin PARADA falsas y reintentos del estado compartido; arreglo del manifiesto al reanudar desde M05 · PR #387 · 2026-11-01
- T-12 · El encadenado par+04 exige la 02 en success · PR #389 · 2026-11-01
- T-01 · Clasificación de las 52 provincias y causas de PARADA (tabla antes de T-02) · 2026-11-01
- T-03 · Activación por elección: clave `ES-NAC|AUT-[unidad-]AAAAMMDD` (INE canónico, matrícula alias; D-2 según
  recomendación), workflow «Activación por Elección» (plan/activar/electoral/completa, filtro `solo`) y 00 v1.4.6
  con `lanzado_por_eleccion` · PR #376 · 2026-11-01

## 5. Propuestas sin asignar (planificador, 01-11)
### Operación
- Fusión automática: activar «Allow auto-merge» en el repositorio; cada PR se fusiona sola con `pruebas` en verde
  (ruleset activo). Reduce las fusiones manuales del propietario.
- Reactivar `proteger-main` en cuanto no haya 00 en curso (app de registro ya exenta y probada, T-10).
- Estudio de motor para provincias BLOQUEADAS por estructura (Madrid, Málaga, Alicante, Barcelona, Murcia; enclaves en núcleos cerrados): M04/M05 capaces de
  reorganizar distritos alrededor de municipios grandes sin partir los que caben bajo el techo. Opus, tras T-14.

### Extensiones (tras cerrar la elección nacional 2023)
- Histórico de legislaturas: generales 2019-11, 2019-04 y 2016 con la clave por elección (T-03); autonómicas del
  ciclo anterior; inventario municipal y espejo de Interior por año.
- Comparador entre legislaturas en el visor (cambios de distritos y resultados).
- Europeas: solo como agregación de resultados sobre los distritos existentes.
- Municipales en ciudades grandes (Madrid, Barcelona, Valencia, Sevilla): distritos por sección censal; cambia la
  unidad atómica de M04 (Opus, largo).
- Ensembles con GerryChain (`docs/ENSEMBLES_GERRYCHAIN.md`) para medir el sesgo de cada plan.
- Simulación de escaños: uninominal frente a D'Hondt real, por provincia y agregado nacional.
- Comunidades de interés y nombres de distrito para el nacional (auditorías C12/C13).
- Ficha pública por distrito y datos abiertos (GeoJSON/CSV con licencia y huella).
