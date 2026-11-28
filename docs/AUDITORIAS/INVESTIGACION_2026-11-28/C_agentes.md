# T-509 · Ámbito C — Agentes, skills, chats y proceso

Fecha: 2026-11-28 · Verificado por un revisor independiente (05:10Z; §8 y §9) · Datos: `C_agentes.json` · Guion del libro de costes: `/tmp/t509_C_agentes/libro.py` (no versionado)

## 1. Veredicto

1. Liga de hoy: **segunda división alta**. Las piezas son buenas; el sistema que forman es caro y se contradice.
2. Lo bueno: 13 skills cortas (22–60 líneas), 2 subagentes de solo lectura con salida JSON, 2 hooks con tests,
   7 reglas que solo se cargan al tocar sus ficheros y un conjunto de oro de 43 casos.
3. Lo que falla: el estado vive en prosa (plan de 190 KB, tablero a mano, costes en cuatro sitios) y en chats
   residentes que se releen a sí mismos en cada llamada.
4. El chat del Planificador lleva 216 USD (05:03Z; 186 a las 04:37Z) y al menos el 80 % es leer y reescribir su
   propio historial.
5. Coordinar cuesta en torno a un tercio del gasto conocido (34–37 % según la lectura), y el libro solo anota el 21 %.
6. Nada en el aparato nombra la ventana de 5 horas, el esfuerzo ni el modelo Fable: la flota de anoche (dato del
   encargo, sin comprobar) no incumplió ninguna regla, porque no había regla.
7. Lanzar y publicar dependen de pasos en prosa y de una frase que ninguna máquina comprueba.
8. El tablero lleva fecha del 28-11 y su cuadro principal no cambia desde el 16-11 o antes.
9. Las evaluaciones se ejecutaron una vez, el 07-11, y no cubren ningún rol.
10. Todo tiene arreglo en una semana, en sombra y reversible: guiones y ficheros pequeños, no más reglas.

## 2. Estado objetivo (referente mundial) y sistema que propongo

Referencias: Anthropic pide «the smallest possible set of high-signal tokens» y notas persistentes fuera del contexto
([ingeniería de contexto, 29-09-2025](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents));
avisa de que un sistema multiagente gasta unas 15 veces más tokens que un chat y que hay que escribir reglas de escala
([sistema multiagente, 13-06-2025](https://www.anthropic.com/engineering/multi-agent-research-system)); y para skills pide
guiones en lo frágil («Run exactly this script»), nada con caducidad en el cuerpo y al menos tres evaluaciones por skill
([buenas prácticas de skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).

**Roles que quedan**

| Rol | Vida | Modelo y esfuerzo (a decidir) | Lee al empezar |
|---|---|---|---|
| Propietario | — | — | Tablero generado y pendientes |
| Director de ola (une Planificador y Coordinador) | Un chat nuevo por ola; se archiva al cerrarla | Opus o Sonnet, medio | Tablero y cola generados (≤ 20.000 tokens) |
| Operador | Un chat por campaña, en su entorno con rol | Sonnet, medio | Ficha de la campaña y salida de `lanzar.py` |
| Implementador | Una tarea, una PR | Opus, alto (Sonnet en documentación) | Su ficha de tarea y las reglas de sus ficheros |
| Revisor y forense (subagentes) | Una llamada | El más barato que pase el oro | Diff o run |

**Estado que pasa al repositorio:** `docs/plan/tareas/T-xxx.md` (estado, criterio, dependencias, talla),
`docs/plan/decisiones.jsonl`, `docs/autorizaciones/` con cabecera legible por máquina, `docs/costes/libro.jsonl`,
lecciones dentro de la PR de cada tarea.

**Lo que se genera con guion:** `docs/ESTADO.md` (PR, runs, publicados, cola), el índice `docs/PLAN.md`, el resumen
semanal del libro y el plan de ventana.

**Presupuesto de la ventana de 5 horas** (equivalencia ≈ 115 USD según el encargo; sin comprobar): 30 % reserva del propietario, 15 % coordinación,
55 % trabajo. Con la media del libro (6,47 USD por tarea) caben unas 10 tareas medias por ventana en la parte de trabajo.
Antes de abrir chats, el guion lee `rate_limit_info` y el libro y devuelve cuántas sesiones caben; las flotas van por olas.
Fable y esfuerzo máximo, solo con frase del propietario.

**Evaluaciones:** oro por agente y por modelo, reejecutado al cambiar agentes o reglas; tres escenarios de autoridad por
rol; indicadores del libro (coste por PR, CI verde al primer empuje, ciclos de reparación, coordinación sobre total).

## 3. Medidas del aparato

| Pieza | Medida (28-11) |
|---|---|
| Skills | 13 ficheros, 443 líneas, 36 KB; sin guiones ni ficheros de apoyo |
| Agentes · hooks · reglas | 2 (103 líneas) · 2 (306 líneas) · 7 (430 líneas, 90 KB) |
| `CLAUDE.md` | 99 líneas, 10,7 KB |
| `docs/PLAN.md` | 1.191 líneas, 190 KB (≈ 50.000 tokens), 216 decisiones, 407 tareas, 79 copias en legacy (7,4 MB) |
| `docs/ESTADO.md` | 112 líneas, 22 KB en main; 70 líneas (62 %) con autoría ≤ 16-11 |
| Traspasos | 15 en 15 días, en dos carpetas; 8 del Coordinador |
| `docs/registro/` | 544 entradas; 656 copias del registro en legacy (101 MB) |
| `main` desde el 16-11 | 487 commits: 58 % robots (281, por autor); 206 PR, 50 de gobierno (24 % de las PR, 10 % de los commits) |
| Evaluaciones | 43 casos para 2 subagentes; 1 ejecución por agente (07-11); 1 veredicto real archivado |

**Puntuación (0–10; disparador, tamaño, caducidad, contradicciones, prosa que debería ser guion)**

| Pieza | Nota | Motivo principal |
|---|---|---|
| diagnosticar-run | 8 | Disparador y salida claros; aún remite al Mac del propietario |
| forense · revisor (agentes) | 8 · 8 | Solo lectura real, JSON, memoria; sin evaluar desde el 07-11 |
| guardia_git.py | 8 | Hace una cosa y está probado |
| cierre-sesion · implementador · ingeniero-motor · lanzar-campana | 7 | Claros; avisos a destinatarios distintos y modelo anticuado |
| disenar-agente · publicar-visor · revisar-pr | 6 | Estados en inglés; línea «al planificador»; lista duplicada con el agente |
| rol_herramientas.py · settings.json | 6 | Ata a los subagentes; la rama del Operador no está cableada |
| coordinador · operador · lanzar-00 | 5 | Tablero y libro a mano; 14 notas fechadas; lanzar-00 se contradice |
| planificador | 4 | Tres versiones de quién edita el plan; nueve líneas de anécdotas fechadas |
| presupuesto | 3 | Sin ventana, sin modelo vigente, sin fichero ni guion para el libro |
| Reglas: huellas 8 · gobernanza 7 · registro 7 · motor2 6 · diagnostico-local 6 · contratos 5 · workflows 4 | — | Bien acotadas por rutas; las dos últimas pesan 20 y 47 KB |

**Libro de costes reconstruido (14 a 28-11, USD)**

| Concepto | Chats | Suma | Nota |
|---|---|---|---|
| Implementadores | 93 | 602,00 | Mediana 2,95; media 6,47; p90 15,95; máximo 40,7; 21 chats ≥ 10 USD suman el 68 % |
| Coordinador (20 a 26-11) | 3 | 183,39 | 33,3 + 75,77 + 74,32 |
| Auditoría del 24-11 | 1 | 76,74 | |
| **Total anotado** | 97 | **862,13** | |
| Planificador (sin anotar) | 1 | 216,33 | `get_session` a las 05:03Z (186,34 a las 04:37Z); incluye la investigación T-509 |
| Operador (sin anotar) | ? | ? | No consta en ningún sitio |

Coordinación conocida: 399,72 de 1.078,46 USD = **37 %** (35 % con la lectura de las 04:37Z; 34 % con los 162 USD previos
a la investigación). Del 20 al 26-11: 96 PR fusionadas y 640,71 USD anotados.

## 4. Hallazgos (por id; el impacto es el que queda tras la verificación)

### C-1 · La ventana de 5 horas no existe para el aparato (impacto 5, esfuerzo S) — CORREGIDO
- **Hoy:** 0 menciones de «5 horas», esfuerzo o Fable en `.claude/`, `CLAUDE.md`, fichas, framework y plan. La skill
  presupuesto dice «Sonnet por defecto; Opus solo para el motor» (l. 16). El Planificador corre en Fable 5.2 a esfuerzo
  máximo; el bloque Relevo de tres skills manda crear la sucesora con «mismo modelo».
- **Sin comprobar:** que 26 sesiones Fable más 7 de trabajo agotaran la ventana (≈ 115 USD) en unos 6 minutos y que una
  gastara 11,4 USD en 6,5 minutos. Es dato del encargo; no está en ningún fichero.
- **Dato útil:** `get_session` devuelve `rate_limit_info` (`five_hour`, estado y hora de reinicio), pero no el saldo.
- **Propongo:** presupuesto 2.0 con guion: tabla de modelo y esfuerzo por rol, reparto 30/15/55 sobre un presupuesto por
  ventana que fija el propietario, olas calculadas, `model` y `effort` siempre explícitos al crear sesiones.
- **Criterio:** `presupuesto_ventana.py --plan` rechaza 26 sesiones Fable a máximo (salida ≠ 0) y acepta una ola dentro
  del reparto (dos fixtures); 0 apariciones de «mismo modelo» en las skills; en el libro de 7 días ningún cierre anota
  la ventana en estado distinto de «allowed» (se lee al cerrar cada chat, sin vigilante).
- **Riesgo:** un modelo más barato en coordinación puede errar más; se mide antes de fijarlo (C-8).

### C-2 · El Planificador gasta al menos el 80 % en releerse y ya no puede relevarse solo (impacto 5, esfuerzo M) — CORREGIDO
- **Hoy** (`get_session`, 05:03Z): 216,33 USD; 351,5 M de tokens leídos de caché, 12,9 M escritos, 0,93 M de salida
  (379 releídos por cada uno producido). A precio de lista la salida es como mucho 37,12 USD (17 %). A las 04:37Z el
  autor leyó 186,34 USD y 0,52 M de salida (cota del 86 %); la diferencia coincide con la investigación T-509, que corre dentro de este chat.
- Contexto 605.791 tokens. El relevo D-160 salta al 70 % de 784.000 (548.800): ya superado. Linaje 7 de 8, donde la
  skill prohíbe crear sucesora. El relevo «sin intervención del propietario» se acaba ahí.
- **Por qué:** cada llamada paga todo lo anterior; el coste crece con el cuadrado de la longitud del chat.
- **Propongo:** chats de coordinación efímeros (uno por ola, leyendo solo lo generado). Entretanto, relevo por tamaño
  absoluto (150.000 tokens), no por porcentaje del umbral de un modelo de 1M.
- **Criterio:** una sesión vuelca `get_session` de los chats de rol a un JSON y `libro_costes.py --vivos <json>` devuelve
  0 solo si ninguno pasa de 200.000 tokens ni de linaje 6; coordinación < 15 % del libro semanal.
- **Necesita:** decisión del propietario (cambia D-160). Reversible: las skills actuales siguen en git.

### C-3 · El libro de costes es prosa en cuatro sitios, sin sesión ni roles (impacto 4, esfuerzo S) — CORREGIDO
- **Hoy:** 97 partidas copiadas a mano en `ESTADO.md`, `TRASPASO_*`, `docs/traspasos/` y `docs/registro/` (12 ficheros),
  con tres notaciones. Planificador y Operador: 0 partidas. T-430, T-443 y T-325 aparecen dos veces con cifras
  distintas y sin id de sesión no se pueden conciliar.
- **Propongo:** `docs/costes/libro.jsonl` escrito desde `get_session` al cerrar cada chat y `libro_costes.py --resumen`.
- **Criterio:** el resumen reproduce 862,13 USD ± 1 % con las 97 partidas importadas (marcadas como históricas, sin id
  de sesión) e incluye los chats de rol; el test exige sesión y rol solo en las filas nuevas.
- **Ya previsto en parte:** T-494 (provisional) pide «un libro único», sin guion.

### C-4 · El tablero lleva fecha nueva y contenido viejo (impacto 3, antes 4; esfuerzo M) — CORREGIDO
- **Hoy:** cabecera «2026-11-28 (madrugada)» en main; las 41 líneas del cuadro por temas y de «Tareas del motor (10-11)»
  no cambian desde el 16-11 o antes (límite del clon); 70 de 112 líneas (62 %) son ≤ 16-11. Dice «Visor v2 desplegado»;
  hay 12 ficheros de test de la v4 y el plan da la V5 por hecha (T-500). Diez secciones de relevo apiladas.
- **Propongo:** `generar_tablero.py` (no confundir con `generar_estado_operativo.py`, que ya existe): registro del visor,
  fichas de tarea y un único bloque manual; las PR y los runs vivos se imprimen a demanda y no se versionan.
- **Criterio:** `generar_tablero.py --check` en CI solo contra ficheros versionados; 0 apariciones de «Relevo» y de
  «Visor v2»; fichero < 6 KB.
- **Por qué baja:** no se cita ningún error causado por el tablero y el dashboard operativo ya sale de un guion.

### C-5 · El plan es una base de datos en prosa (impacto 4, esfuerzo L) — CORREGIDO
- **Hoy:** 190 KB. T-500 a T-505 están bajo el título «Cola T-291 a T-367 (14 a 16-11)». El 51 % de las líneas es
  estado del 01 al 07-11. Abre con «Reglas para todos los chats» que contradicen seis reglas vigentes: quién fusiona,
  el Mac, a quién se avisa, quién numera el registro, qué suite se pasa y a quién se pide un lanzamiento.
- **Recuento de estados:** entre 70 y 95 tareas abiertas según el patrón; la misma columna escribe «EN_CURSO» (8) y
  «EN CURSO» (17).
- **Propongo:** una ficha por tarea abierta, `decisiones.jsonl` y un índice generado de menos de 150 líneas.
- **Criterio:** `wc -c docs/PLAN.md` < 20.000; `plan.py tarea T-505` imprime solo esa tarea; test de criterio por ficha.
- **Ya previsto en parte:** T-494 (provisional) pide una ficha por decisión.

### C-6 · Lanzar y publicar: prosa y una frase que nadie comprueba (impacto 3, antes 4; esfuerzo M) — CORREGIDO
- **Hoy:** 151 líneas en cuatro skills describen las comprobaciones previas. Ningún workflow ni herramienta lee
  `docs/autorizaciones/`. Desde D-127 la frase D-52 es el único control. `lanzar-00` dice en la l. 34 que el run arranca
  al hacer el dispatch y en la l. 38 que queda en espera hasta el «Approve».
- **Propongo:** `herramientas/lanzar.py`, en simulación por defecto: valida ficha, topes, caducidad y run en curso,
  compone el dispatch y lo anota.
- **Criterio:** tests: ficha caducada → 2; fuera de ficha → 2; run en curso → 3; las cuatro skills ≤ 70 líneas.
- **Ya previsto en parte:** T-493 (provisional) propone revisor solo en el paso de publicar.
- **Por qué baja:** D-127 es una decisión expresa del propietario, no hay incidente citado desde entonces, las
  publicaciones se pueden revertir y el repositorio público no factura minutos.

### C-7 · Nueve contradicciones entre skills, `CLAUDE.md` y plan (impacto 3, esfuerzo S) — CONFIRMADO
- Quién edita el plan (planificador l. 10 y l. 42; coordinador l. 21). A quién va la línea de resultado
  (publicar-visor l. 22 frente a operador l. 29). A quién avisa el implementador (l. 9 frente a l. 23).
  `cierre-sesion` siempre abre PR, y el Coordinador la invoca «sin PR». Quién fusiona (revisar-pr l. 3 frente a
  operador l. 37). «Sonnet por defecto» y «coste no en dólares» frente a Fable y a un libro en USD. Estados en inglés
  en `disenar-agente`. «No adoptar prompts residentes» frente a tres chats residentes. El Mac.
- El bloque Relevo está copiado en 5 skills y un test fija la copia.
- **Criterio:** `tests/test_skills_coherencia.py` con las frases vetadas; Relevo en un solo fichero enlazado.

### C-8 · Evaluaciones de una sola vez y sin roles (impacto 3, esfuerzo M) — CONFIRMADO
- **Hoy:** una ejecución por agente (07-11: revisor 17/18, forense 12/12); 26 commits en reglas y `CLAUDE.md` desde el
  16-11 sin repetirla (27 con el del 28-11); 0 de 13 skills evaluadas; 3 casos de autoridad; 1 veredicto real archivado
  frente a 206 PR.
- **Propongo:** tres escenarios de autoridad por rol, casos retenidos posteriores al 07-11, reejecución por modelo.
- **Criterio:** ≥ 15 escenarios en `evals/skills/`; un resultado por agente y modelo posterior al último cambio.

### C-9 · El hook de roles solo ata a los subagentes (impacto 3, esfuerzo S) — CORREGIDO
- **Hoy:** la rama del Operador depende de `DDD_ROL` en un entorno que no existe (3 entornos, ninguno de operador; el
  «Default» no tiene variables). «Sin rol: deja pasar». Planificador, Coordinador e implementador no tienen límite.
- **Propongo:** invertir el defecto (sin rol no se despachan workflows con efecto ni se edita plan o autorizaciones) y
  crear un entorno por rol que lo necesite (Operador y quien edite el plan). `create_session` hereda el entorno del
  creador: al abrir implementadores hay que pasar `environment_id`, o heredarían el rol.
- **Criterio:** tests del hook: dispatch sin rol → 2; con `DDD_ROL=operador` → 0; editar `PLAN.md` sin
  `DDD_ROL=planificador` → 2 y con él → 0.

### C-10 · Robots y copias: 58 % de los commits y 101 MB (impacto 3, esfuerzo M) — CORREGIDO
- **Hoy:** de 487 commits, 281 son de robots: 186 del que numera el registro y 95 de otros. Los 206 restantes son PR,
  50 de ellas de gobierno. 656 copias del registro en legacy.
- **Propongo:** sin copia en legacy para ficheros de solo adición; registro numerado al publicar versión.
- **Criterio:** en una semana no crecen las copias y hay 0 commits «registro: numerar»; PR de gobierno < 10 %. Los otros
  95 commits de robots no los toca esta propuesta. Toca la regla de gobernanza.

### C-11 · Límites en líneas, no en tamaño (impacto 2, esfuerzo S) — CONFIRMADO
- **Hoy:** `CLAUDE.md` cumple 100 líneas con 10,8 KB; `workflows.md` pesa 47 KB con líneas de hasta 2.723 caracteres.
- **Criterio:** test de bytes (`CLAUDE.md` ≤ 8 KB; cada regla ≤ 12 KB; ninguna línea > 400 caracteres).

## 5. Camino

**Tres pasos**

| Paso | Qué | Prueba |
|---|---|---|
| Esta semana | C-1, C-3, C-7, C-9 y tablero en sombra (C-4) | Ninguna ventana agotada; libro con chats de rol; test de coherencia en verde |
| Este mes | C-2 (coordinación efímera), C-5, C-6, C-8 | Coordinación < 15 % del libro; plan < 20 KB; `lanzar.py` con sus cuatro tests |
| Este trimestre | C-10, C-11, oro por modelo y elección del más barato que pasa | 0 commits de numeración del registro; coste por PR un 30 % menor que 5 USD |

**Semana de migración (cada día es una PR pequeña que se deshace con `git revert`)**

| Día | Acción | Cómo se deshace |
|---|---|---|
| 1 | Presupuesto 2.0 y tabla de modelo y esfuerzo; corregir las nueve contradicciones | Revertir la PR de skills |
| 2 | `libro_costes.py` y `libro.jsonl` con las 97 partidas; el Coordinador sigue anotando a mano | Borrar la carpeta |
| 3 | `generar_estado.py` escribe `ESTADO_generado.md` junto al manual; se comparan dos días | Borrar el fichero generado |
| 4 | `lanzar.py` solo en simulación; el Operador lo ejecuta antes de cada lanzamiento real | No usarlo |
| 5 | Fichas de las tareas abiertas en doble escritura; `PLAN.md` intacto | Borrar `docs/plan/` |
| 6 | Una ola piloto con director efímero, sin Planificador ni Coordinador residentes | Reabrir los chats de rol con sus skills |
| 7 | Decidir con el libro: coste de coordinación de la ola piloto frente al tercio actual | Si no baja del 15 %, se vuelve atrás |

## 6. Lo que no pude comprobar

- El coste del Operador: no está en el libro. Se obtiene con `get_session` de sus chats.
- Qué caducidad de caché usa cada sesión y cuánto de los 12 M de tokens escritos son despertares en frío. Haría falta
  el desglose por turno.
- La fecha real del cuadro del tablero: el clon empieza el 16-11. Se ve con `git log --follow` en un clon completo.
- Si los 26 commits en reglas cambiaron el acierto del revisor: hay que reejecutar el oro (consume ventana).
- El porcentaje de PR con CI verde al primer empuje: la skill presupuesto cita un 20 % del 02-11 y no hay guion.
- Si los ajustes de proyecto admiten fijar modelo y esfuerzo por defecto: comprobar en la documentación de ajustes.
- La flota de anoche (26 + 7 sesiones, ≈ 115 USD, 6 minutos): solo consta en el encargo.
- Que el entorno `produccion` no tiene revisor: consta por D-127; la API de entornos da 403 desde la nube.
- Precios: los de la skill `claude-api` (tabla del 03-11-2026); la equivalencia de la suscripción puede diferir.

## 7. Objeciones (D-216)

1. **El propio T-509 repitió el fallo que investiga:** el protocolo mandaba «Usa subagentes» a cada sesión, sin tope de
   concurrencia ni de esfuerzo. La regla de ventana tiene que valer también para los encargos del Planificador.
2. **D-160:** un relevo ligado al umbral de compactación de un modelo de 1M llega cuando el chat ya es caro, y el
   linaje 8 lo corta. Propongo cambiarlo por tamaño absoluto o por ola.
3. **«El coste … no en dólares»** (skill planificador, l. 28): las tallas sirven para aprobar tareas, pero la ventana
   solo se presupuesta en dólares o en tokens. Hacen falta las dos cosas.
4. **Cada fallo acaba en una regla en prosa:** este informe propone seis guiones y ninguna regla nueva. La prohibición
   de coautores no se cumplió (4 commits de 72 desde el 24-11 según el autor; el verificador cuenta 11 con
   alguna línea «Co-authored-by», sin distinguir de quién) hasta que T-505 la puso en el robot de fusión.
5. **«Mantener todos los frentes»** es compatible con todo lo anterior, pero el número de chats simultáneos lo fija la
   ventana, no el número de frentes.

## 8. Verificación independiente (28-11, 05:10Z, sobre origin/main 548968c47)

Revisados 11 · confirmados 3 · corregidos 8 · refutados 0 · no comprobables 0. El detalle y el comando de cada uno
están en el campo `verificacion` de `C_agentes.json`.

| Id | Veredicto | Qué cambia |
|---|---|---|
| C-1 | CORREGIDO | La flota de anoche es dato del encargo, sin comprobar; criterio reescrito (la API no da saldo; sin registro diario) |
| C-2 | CORREGIDO | 216 USD y cota ≥ 80 % (antes 186 y ≥ 86 %); 15 traspasos, no 13; coordinación «un tercio», no «≥ 35 %» |
| C-3 | CORREGIDO | Cuatro sitios, no cinco; el test exime a las 97 partidas históricas, que no tienen sesión |
| C-4 | CORREGIDO | La cabecera ya dice 28-11; 70 de 112 líneas; `--check` solo con ficheros versionados; impacto 4 → 3 |
| C-5 | CORREGIDO | 190 KB; abiertas 70–95 (faltaba «EN CURSO» con espacio); solape con T-494 |
| C-6 | CORREGIDO | Líneas 34 y 38; 26 referencias fechadas; solape con T-493; impacto 4 → 3 |
| C-7 | CONFIRMADO | — |
| C-8 | CONFIRMADO | — |
| C-9 | CORREGIDO | Evidencia confirmada; la propuesta necesita entorno por rol y `environment_id` explícito |
| C-10 | CORREGIDO | Robots 58 % (281), no 51 %; gobierno 50 commits (10 %), no 84; criterio de robots reescrito |
| C-11 | CONFIRMADO | — |

## 9. Descartados en la verificación

Ningún hallazgo se descarta entero. Se retiran estas afirmaciones sueltas:

- «84 commits más (17 %) son documentos de gobierno» (C-10): no se reproduce; son 50, las mismas 50 PR.
- «62 commits de otros robots» y «51 % de robots» (C-10): son 95 y 58 %.
- «Costes en cinco sitios» (C-3): son cuatro; `origin/main` no es un sitio.
- «13 traspasos, 1 en `docs/traspasos/`» (C-2): son 15, con 3 en esa carpeta.
- «72 de 106 líneas (68 %)» y «fecha del 26-11» (C-4): son 70 de 112 (62 %) y la cabecera ya dice 28-11.
- «Efecto irreversible» y «cuesta minutos de Actions» (C-6): se ha revertido antes y el repositorio público no factura.
- «Robots < 10 % de los commits» como criterio (C-10): la propuesta no lo alcanza.
