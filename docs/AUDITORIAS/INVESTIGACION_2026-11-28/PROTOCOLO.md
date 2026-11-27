<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Protocolo de la investigación profunda del 28-11 (flota de sesiones)
FECHA: 2026-11-28
ESTADO: DOCUMENTO DE TRABAJO de la investigación T-509. No es el plan; no autoriza lanzar ni publicar nada
CAMBIOS: 1.0.0 — protocolo común y reparto de ámbitos
MOTIVO: orden del propietario (28-11, 00:20, chat del Planificador): la investigación más profunda hecha hasta hoy, en todos los ámbitos, para pasar el proyecto a la siguiente fase y convertirlo en referente mundial
ANTERIOR: ninguna (fichero nuevo)
-->

# Investigación profunda del 28-11 — protocolo común (T-509)

## 1. El encargo (palabras del propietario)
«La investigación más profunda que jamás has hecho: todos los gaps de mejora del proyecto en todos sus ámbitos
(arquitectura, implementación, skills, chats principales, repositorio, almacenamiento, publicación, algoritmo y sus
mejoras inmensas). Pasar el proyecto, en todas sus facetas, a la siguiente fase. Un referente mundial, un ejemplo a
seguir e imitar.» Hay capacidad de sobra y debe gastarse esta noche: **profundidad máxima, no ahorres**.

Tú llevas **un ámbito** (anexo A). Planificador: `session_01KQDtFtbjHrVwhhgHnNE6nU` (solo `send_message` del MCP
`claude-code-remote`).

## 2. Qué ya existe (léelo antes; no lo repitas)
- `docs/AUDITORIAS/AUDITORIA_INTEGRAL_2026-11-24.md` y `docs/AUDITORIAS/PLAN_MEJORA_2026-11-25.md` (bloques A–K).
- Análisis de dirección (26-11), resumen: gobierna más que construye (≈216 decisiones, ≈500 tareas, 79 versiones del
  plan); la jerarquía de chats frena; cada fallo acaba en una regla en prosa; demasiados frentes; CI cara; el
  propietario es el cuello de botella; D-18 silencia la crítica. Decidido (D-216): se aprueban **criterios de
  aceptación**, no detalles, y cada tarea admite una línea de objeción. El propietario **mantiene todos los frentes**.
- `docs/PLAN.md` (decisiones D-xx y tareas T-xx), `docs/ESTADO.md`, `CLAUDE.md`, `.claude/rules/`, `docs/ESTUDIOS/`.

Un hallazgo vale si es **nuevo**, o **refuta o corrige** con evidencia algo de lo anterior, o lo **profundiza con datos
que no había** (medidos, no estimados). Repetir una auditoría sin añadir evidencia no vale.

## 3. Reglas (sin excepciones)
- **Solo lectura sobre producción**: no lances workflows de GitHub, no publiques, no abras PR, no toques `docs/PLAN.md`
  ni ficheros fuera de los tuyos. Nada de `gh workflow run` ni `dispatches`.
- Escribes solo: `docs/AUDITORIAS/INVESTIGACION_2026-11-28/<NN>_<slug>.md`, `…/<NN>_<slug>.json` y, si eres laboratorio
  o necesitas guiones o datos, `docs/ESTUDIOS/T509_<SLUG>/` (sin binarios ni ficheros de más de 1 MB).
- **Commits sin firmas** (D-211): sin `Co-Authored-By`, sin `Claude-Session`, sin nombres de IA ni de modelo.
- **Empuja a tu rama de salida cada 30 min** (`git push -u origin HEAD:<tu rama>`), el primero en los primeros
  20 min con el esqueleto: si la sesión se corta, lo empujado se salva.
- Español claro y corto; topónimos en español. Datos oficiales nunca de memoria: de un fichero con fuente.
- Entorno: 4 CPU; faltan dependencias de Python (instala con el `.lock` que toque; lee `.claude/rules/diagnostico-local.md`
  y `.claude/rules/motor2.md`); la web del proyecto no es accesible desde la nube; `gh api` REST sí (GraphQL no);
  WebSearch y WebFetch sí. Chromium y Playwright están instalados (`require('playwright')`).

## 4. Nivel de exigencia
- **Mide**: cuenta, cronometra, ejecuta, perfila, consulta la API (runs, PR, jobs). «Parece» no es un hallazgo.
- **Usa subagentes** (herramienta Agent) para leer en paralelo y **un verificador que intente refutar** tus 10 hallazgos
  principales antes de darlos por buenos (¿lo arregló una PR posterior?, ¿ya es una T-xx del plan?, ¿hay una D-xx del
  propietario que lo decide en contra?).
- **Compara con los mejores del mundo** en tu ámbito, con fuente (URL, año). Di en qué liga juega hoy el proyecto y
  qué haría falta para la primera.
- **No pares pronto**: trabaja por rondas, cada una con un ángulo distinto (por fichero, por historia de git, por
  datos, por fallo, por usuario, por referente externo), hasta que dos rondas seguidas no den nada nuevo o llegue la hora.
  Comprueba la hora con `date -u`.
- Tu **línea de objeción** (D-216) es bienvenida: si el propio encargo o una decisión vigente te parece un error, dilo
  con evidencia en una sección «Objeciones».

## 5. Qué entregas
### 5.1 `<NN>_<slug>.md` (para el propietario; máx. ~400 líneas)
1. **Veredicto en 10 líneas**: en qué liga juega hoy este ámbito y por qué.
2. **Estado objetivo «referente mundial»**: cómo se vería, con ejemplos reales de quien ya lo hace.
3. **Hallazgos**, de mayor a menor impacto. Cada uno: qué pasa hoy (con evidencia), por qué importa, qué propongo,
   **criterio de aceptación verificable**, coste, riesgo.
4. **Camino en tres pasos** (esta semana / este mes / este trimestre), cada paso con su prueba.
5. **Lo que no pude comprobar** y cómo se comprobaría. **Objeciones**.

### 5.2 `<NN>_<slug>.json` (para la máquina)
```json
{"ambito": "NN_slug", "sesion": "<tu session id>", "veredicto": "…", "liga_hoy": "…", "liga_objetivo": "…",
 "hallazgos": [{
   "id": "NN-1", "titulo": "≤100 caracteres", "que_pasa_hoy": "…",
   "evidencia": [{"tipo": "VERIFICADO|LEIDO|EXTERNO|HIPOTESIS", "ref": "ruta:línea | comando | URL", "detalle": "cifra o cita"}],
   "por_que_importa": "…", "propuesta": "…",
   "criterio_aceptacion": "prueba o comando con su resultado esperado",
   "impacto": 1, "esfuerzo": "S|M|L|XL", "riesgo": "…",
   "toca": ["motor|ci|publicacion|web|datos|docs|proceso|skills|repo|ciencia|producto|seguridad|legal"],
   "necesita": "nada|fusion|lanzamiento|decision_propietario",
   "ya_previsto": "T-xxx o null", "decisiones_relacionadas": ["D-xx"],
   "nivel_mundial": "qué hacen los mejores, con fuente", "confianza": "alta|media|baja"}]}
```
`impacto`: 5 = cambia la liga del proyecto; 1 = pulido. `esfuerzo`: S ≤ 1 sesión; M 2–3; L una semana; XL más.
VERIFICADO = lo reproduje con un comando; LEIDO = lo leí en código o documento; EXTERNO = fuente de fuera.

## 6. Horario (UTC; son las 00:00Z ≈ 01:00 en España)
| Fase | Hasta | Qué |
|---|---|---|
| 1. Investigación | 02:15Z | Hallazgos completos y empujados (esqueleto antes de 00:40Z) |
| 2. Verificación cruzada | 03:00Z | El Planificador te dirá qué rama ajena verificar (quien construye no certifica) |
| 3. Siguiente fase | 04:15Z | El Planificador te dirá qué mejora verificable preparar en una rama (sin PR) |
| Cierre | 04:20Z | Último empuje y mensaje de cierre |

Al acabar cada fase, **mensaje al Planificador** (≤12 líneas): rama, nº de hallazgos, los 5 principales con su impacto,
y lo que necesitas. Si te quedas sin trabajo antes de la hora, **profundiza** (otra ronda), no esperes.

## Anexo A — Ámbitos
Cada ámbito tiene foco y punteros de partida (no límites: sigue el rastro donde lleve).

| NN | slug | Foco | Punteros |
|---|---|---|---|
| 01 | motor-codigo | Revisión a fondo del motor Deslinde: correctitud, determinismo y huellas, formulación CP-SAT del exacto, exhaustivo, generadores y cadenas, competición y clave D8, reglas (R-NUCLEO, D-66), rendimiento, errores latentes, qué impide escalar | `paquetes/deslinde/`, `ddd_motor2/`, `ddd_core/m05_*`, `.claude/rules/motor2.md`, `docs/ESTUDIOS/T296_OPTIMO_D8`, `T254_MEDICION_DESLINDE`, `T136_CERTIFICADOR_EXACTO.md`, `T465_BANCO_PILOTO`, informes T-502/T-503/T-507 (PR #1029, #1035, #1037) |
| 02 | algoritmo-mundo | Estado del arte mundial 2019–2026 en redistritación algorítmica y qué traer a Deslinde: ReCom y variantes, SMC (`redist`), short bursts, optimización exacta (contigüidad por cortes o flujos, mínimo de unidades partidas, generación de columnas / branch-and-price), diagramas de potencia, métodos multinivel; herramientas y proyectos (GerryChain, ALARM 50-State, Dave's Redistricting, Districtr, PlanScore); comisiones de límites (Reino Unido, Canadá, Australia, Nueva Zelanda). Cada técnica → mejora concreta, con coste y beneficio | Web (artículos, repos) + `paquetes/deslinde/src/deslinde/` para aterrizar |
| 03 | lab-exacto-escala | LABORATORIO. Llevar la optimalidad demostrada a territorios grandes: formulaciones alternativas del exacto, rotura de simetrías, arranque en caliente, cotas inferiores, descomposición; medir tiempo y hueco frente al exacto actual en Sevilla, Valencia, Málaga, Alicante, Vizcaya y los que quepan | `paquetes/deslinde/src/deslinde/exacto.py`, `reglas/`, `docs/ESTUDIOS/T465_BANCO_PILOTO`, `requirements-exacto.lock`, `herramientas/bateria_motor.py` |
| 04 | lab-mejora-local | LABORATORIO. Mejora local exacta (LNS): partir del ganador actual de cada territorio y reoptimizar con CP-SAT grupos de 2–3 distritos vecinos; medir en cuántos territorios mejora la clave D8 y cuánto cuesta | Igual que 03 + `ddd_motor2/competir.py`, `datos/composicion/` |
| 05 | lab-neutralidad | LABORATORIO. Mapas alternativos como vara de medir: generar para varios territorios miles de mapas válidos con las reglas del contrato (ReCom), comprobar la mezcla, y situar el mapa publicado en la distribución (escaños por bloque con mayoría simple, partidas, desviación). Diseñar el «certificado de neutralidad» publicable | `ddd_ensemble/`, `docs/ENSEMBLES_GERRYCHAIN.md`, `docs/ESTUDIOS/T465_BANCO_PILOTO/gerrychain_puro.py`, PLAN_MEJORA bloque D, por qué se retiraron el 16-11 |
| 06a | lab-banco-nac-a | LABORATORIO. Banco de comparación completo con el motor 1.2: Deslinde frente a GerryChain (10⁴ pasos) y frente al exacto donde quepa. Nacionales nac01–nac26 (primero los pequeños). Tabla por territorio | `docs/ESTUDIOS/T465_BANCO_PILOTO/` (diseño, guiones), `.claude/rules/motor2.md` (adquisición de entradas) |
| 06b | lab-banco-nac-b | Igual que 06a para nac27–nac52 (Madrid no se adquiere en la nube: márcalo) | Igual |
| 06c | lab-banco-aut | Igual que 06a para aut01–aut19 | Igual |
| 07 | ciencia-metodo | Rigor científico: igualdad de población y tolerancias frente a los estándares (Comisión de Venecia y países con distritos), compacidad (¿se mide?), contigüidad, límites administrativos, comunidades de interés; justificación y sensibilidad de la clave D8 («regla a medida», bloque E); reproducibilidad por terceros; preinscripción OSF, artículo JOSS, Zenodo; qué exigiría una revisión por pares; amenazas a la validez | `docs/PREINSCRIPCION_OSF.md`, `docs/ARTICULO_JOSS/`, `docs/AUDITORIA_C*.md`, `docs/POLITICA_*.md`, `documentacion_publica/`, `visor/v4/…metodo` |
| 08 | analisis-electoral | El análisis electoral: M07/M08, doble vuelta (P75), bloques, supuestos (voto estratégico, candidaturas, transferencias), histórico 2011–2023, indicadores (T-478), incertidumbre; comparación con lo que publican politólogos y medios; errores posibles en datos (CERA, voto exterior, secciones sin geometría); qué falta para que sea análisis citable | `modulos/07_*`, `modulos/08_*`, `configuracion/`, `herramientas/*doble_vuelta*`, `datos/resultados/`, AUDITORIA_INTEGRAL §7 |
| 09 | datos-fuentes | Datos y fuentes: catálogo de procedencia, sha256, espejos, P10, licencias, caducidad; calidad (equivalencias de secciones entre años, municipios sobredimensionados); datos abiertos publicados (FAIR, esquema, documentación, API) | `fuentes/`, `orchestracion/catalogo_procedencia.json`, `orchestracion/fuentes_r2.json`, `datos_abiertos/`, `.github/workflows/p10-fuentes.yml`, `docs/GUIA_FUENTES_R2.md` |
| 10 | almacenamiento | Almacenamiento: los cinco buckets de R2, estructura diseñada y no aplicada (D-188/D-190), inventario, promoción, poda; artefactos de Actions que caducan y M06 perdidos; git como almacén (blobs M08, `.git` de 446 MB); integridad, copias, restauración probada, coste, retención | `docs/ESTUDIOS/T145_PODA_R2`, `docs/ESTUDIOS/T430_WEB_EDITABLE/`, `.github/workflows/p70-archivo.yml`, `p40-publicacion.yml`, `herramientas/*r2*` |
| 11 | publicacion-web | Publicación: P40 (Pages + R2), migración a Cloudflare (hoy el job corre en `github-pages` y no ve las variables de `publicacion`), atomicidad, vuelta atrás, caché y versionado, pruebas por rama (P90), medición, dominio y www, SEO técnico, cabeceras de seguridad, analítica sin cookies; plan de corte | `.github/workflows/p40-publicacion.yml`, `p90-automatico.yml`, `docs/ESTUDIOS/T430_WEB_EDITABLE/REDISENO_R2.md`, `herramientas/publicar*`, `T294_ANALITICA_SIN_COOKIES` |
| 12 | visor | El visor: calidad del código, rendimiento medido (peso, peticiones; sírvelo en local y mídelo con Playwright), accesibilidad WCAG 2.2, móvil, experiencia (encontrar tu distrito, compartir, comparar sistemas), estados de error, pruebas; versiones muertas (v2, v3); comparación con los mejores visores electorales del mundo | `visor/v4/`, `visor/v2/`, `dashboard/`, `tests/test_visor_*`, `docs/ESTUDIOS/T295_ACCESIBILIDAD`, `T156_VISOR_USO`, `T499*` |
| 13 | ci-cd | CI/CD: los 15 workflows (tamaño, duplicación), minutos reales (API de runs de las dos últimas semanas), niveles y selección por impacto, colas de fusión, tests inestables, cachés, tiempo por job; fusión automática, guardián y revisor; tasa de fallo por workflow | `.github/workflows/`, `.claude/rules/workflows.md`, `docs/ESTUDIOS/T162_CI_PRUEBAS`, `T155_COSTE` |
| 14 | seguridad | Seguridad y cadena de suministro: permisos de `GITHUB_TOKEN`, acciones fijadas por SHA, inyección por expresiones en `run:`, secretos y entornos, robots y Apps, ruleset, hooks y `settings.json`; dependencias (`pip-audit`), Dockerfile; modelo de amenazas de un repositorio público con agentes y fusión automática (inyección de instrucciones por PR, issues o comentarios) | `.github/workflows/`, `.claude/`, `requirements*.lock`, `Dockerfile` |
| 15 | tests | Tests: 515 ficheros y 2.213 fixtures: cobertura real (mídela en un subconjunto), tiempos, redundancia, tests que no prueban nada, pruebas por propiedades, mutación (muestra), separación por niveles; lista de reglas en prosa de `CLAUDE.md` y `.claude/rules/` que deberían ser un test o una guarda | `tests/`, `tests/tiempos*`, `CLAUDE.md`, `.claude/rules/` |
| 16 | repositorio | Repositorio: 14.482 ficheros; `legacy` (153 MB), `docs` (389 MB), `territorios/evidencia`, binarios, `.git`; estructura y nombres; código muerto (`ddd_core` frente a `ddd_motor2`, `paquetes/deslinde`, `g10`); ficheros sueltos en la raíz; coste y beneficio de VERSIÓN + `legacy`; reestructuración por fases sin romper huellas (D-82) | Todo el árbol; `docs/DEUDA_HISTORICA_LEGACY.md`, `.claude/rules/gobernanza.md` |
| 17 | arquitectura | Arquitectura del proceso: M01–M08, P00–P90, contratos, checkpoints, linaje y recibos, catálogo, resolver de la 00, Gestor, activación por elección; acoplamientos, puntos únicos de fallo, idempotencia, complejidad accidental; arquitectura objetivo (grafo declarativo, artefactos direccionados por contenido, datos fuera de git) y migración | `docs/ARQUITECTURA/`, `docs/ARQUITECTURA_*.md`, `modulos/`, `ddd_core/`, `g10/`, `orchestracion/`, `.github/workflows/ejecucion-completa-proyecto.yml`, `gestor-campanas.yml` |
| 18 | operacion | Operación medida: historial de runs (éxito por workflow, causas del forense, reintentos, duración), «a la primera» (T-491), observabilidad; tiempo de ciclo de una idea hasta publicada; esperas (plazo de las últimas 200 PR: abrir → verde → fusión) con la API | API de Actions y de PR, `.claude/agent-memory/forense/MEMORY.md`, `orchestracion/metricas_proceso.json`, `docs/EJECUCIONES` |
| 19 | agentes-proceso | Sistema de agentes y gobierno: roles y chats (Planificador, Coordinador, Operador, implementadores), relevos, coste por chat, `PLAN.md`, `ESTADO.md` (desfasado), registro; calidad de cada skill, agente, hook y regla (disparadores, tamaño, contradicciones, lo que falta); `evals/oro`; comparación con las guías públicas de Anthropic sobre agentes, contexto y skills (con fuente); sistema objetivo y migración | `.claude/`, `CLAUDE.md`, `docs/PLAN.md`, `docs/ESTADO.md`, `docs/TRASPASO_*`, `evals/`, `docs/ARQUITECTURA/FRAMEWORK_AGENTES_Y_ESTRUCTURA.md` |
| 20 | producto-estrategia | Producto y estrategia para ser referente mundial: audiencias, propuesta de valor, lo que hacen los referentes (Atlas of Redistricting, ALARM, Dave's Redistricting, Electoral Calculus, revisiones de límites), huecos (comparador de sistemas, busca tu distrito, piezas para medios, API, inglés), credibilidad (revisión externa, límites declarados, licencia D-194 frente a apertura), sostenibilidad; hoja de ruta a 30, 90 y 180 días con hitos verificables | AUDITORIA_INTEGRAL §10–§12, `README.md`, `documentacion_publica/`, `visor/v4/`, `docs/ESTUDIOS/T158_OTROS_AMBITOS` |
| 21 | legal-etica | Legal y ética: licencias de código y datos, atribuciones (fotos CC BY, teselas), encuadre frente a la LOREG y el art. 68 CE, aviso legal, privacidad y analítica, propiedad intelectual, neutralidad política percibida (nombres de bloques), condiciones de uso de las fuentes (INE, Interior, CNIG, Wikimedia) | `LICENSE`, `visor/v4/NOTICE.md`, `propiedad_intelectual/`, `docs/registro_pi/`, `configuracion/`, páginas legales del visor |
| 22 | calidad-mapas | Auditoría numérica de lo publicado: por territorio y distrito, desviación de población, demarcaciones y municipios partidos, compacidad si hay geometría, contigüidad y enclaves, coherencia de totales (votos y escaños), nombres duplicados; atípicos y errores; clasificación de los territorios más débiles; tests de coherencia que faltan | `datos/`, `datos_abiertos/`, `orchestracion/publicaciones_visor.json`, `territorios/*/resultados`, CLAUDE.md («Visor y dashboard») |
| 23 | economia | Economía: gasto por chat (libro de costes en las lecciones del Coordinador y en `docs/ESTADO.md`), minutos de CI, R2; coste por territorio regenerado, por PR y por decisión; dónde se va el gasto; palancas con ahorro estimado; presupuesto y métricas | PR de lecciones (#1028, #1030 y anteriores), `orchestracion/metricas_proceso.json`, `.claude/skills/presupuesto`, `docs/ESTUDIOS/T155_COSTE` |
| 24 | auditoria-auditorias | Verificación adversarial de las auditorías anteriores: cada afirmación y propuesta de la AUDITORIA_INTEGRAL, del PLAN_MEJORA y del análisis de dirección: ¿cierta hoy?, ¿hecha?, ¿en el plan?, ¿decidida por el propietario? Tabla de estado, errores de las auditorías y lista de puntos ciegos que ninguna miró | Los tres documentos + `docs/PLAN.md` + `git log` |
