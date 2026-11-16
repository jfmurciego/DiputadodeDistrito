# T-378 · Diseño al detalle de P00 Campaña y de la nueva forma de trabajar

VERSIÓN: 1.1.0 · FECHA: 2026-11-16 · ANTERIOR: `legacy/docs/ESTUDIOS/T378_P00_CAMPANA/DISENO_P00_CAMPANA_v1.0.0.md` ·
ESTADO: propuesta para el revisor independiente y el propietario (T-387, D-145)
CAMBIOS 1.1.0: decisiones A, B y C de D-145 (la validación desde la rama no escribe en `main`; 15 territorios a la vez
con un solo job por cadena; la noche del 29-11 con la 00 actual) y todos los arreglos del revisor del diseño 1.0:
qué es un apartado y cómo falla el job `resultado`, re-ejecuciones, recuento sin duplicados, marca «sin_resultado»,
permisos por job, cierre atómico, grupos globales fuera de la ruta de campaña, commit de cierre como robot, IA de cierre
con permisos mínimos y logs como entrada no confiable, plan de PR con la 2b, traducción del ensayo, listas de códigos
mixtas, citas del anexo renumeradas, reloj y coste reproducibles.
MOTIVO: D-145 (corrige D-143 tras el revisor del diseño 1.0).

Solo documento: no cambia código, workflows ni datos, y no lanza nada. Base: `origin/main` 8221ab9. Límites de GitHub
con cita, fuente y fila en `ANEXO_A_LIMITES_GITHUB.md` 1.1.0 (las referencias «fila n» son de ese anexo). Cada arreglo
lleva su prueba prevista; el resumen está en §14. Las decisiones que aún necesito están en §15.

## 0. Qué cambia respecto al diseño 1.0

| Tema | 1.0 | 1.1 | Sección |
|---|---|---|---|
| Validación desde la rama | podía escribir su commit de cierre en `main` | **no escribe en `main`**: el cierre va a una rama de cierre (A) | §11 |
| Territorios a la vez | 10 (luego 15 en D-143) | **15**, con un solo job por cadena a la vez (B) | §3, §12 |
| Noche del 29-11 | respaldo si P00 no está validada el 24-11 | **caso base**: la 00 actual; P00 se fusiona después del 29-11 (C) | §11, §13 |
| La 00 | se borraba en la PR 3 | **no se borra en la PR 3**; se retira en una PR aparte tras el 29-11 | §13 |
| Apartado | «el territorio queda apartado» | definición exacta, recuento sin duplicados y job `resultado` en rojo | §4 |
| Permisos y cierre | un commit al cierre | permisos por job, orden de operaciones del cierre y reintentos acotados | §5, §6 |

## 1. Qué cambia, en una frase

Hoy una campaña son cientos de ejecuciones sueltas que se lanzan unas a otras y escriben en `main` a cada paso. Con
P00, **una campaña es una sola ejecución**: comprueba antes de empezar, trabaja cada territorio a su ritmo, aparta
el que falla sin parar al resto, escribe en `main` una sola vez al final y deja el informe en un issue.

**Nombres.** Este diseño usa los nombres de destino de D-129. Mientras duren los pasos 6-8, los ficheros actuales son:

| Nombre de destino | Fichero hoy (nombre visible hoy) |
|---|---|
| P10 Fuentes (P11 territoriales, P12 electorales) | `preparacion-fuentes.yml` («P10 Fuentes — P11 Territoriales») y `preparacion-resultados-electorales.yml` («P10 Fuentes — P12 Electorales») |
| P20 Distritos | `produccion-distritos.yml` («P20 Base territorial — P30 Distritos») + `_reutilizable-generacion-territorial.yml` |
| P30 Resultados electorales | `incorporacion-resultados-electorales.yml` («P40 Resultados electorales») + `_reutilizable-incorporacion-electoral.yml` |
| P40 Publicación | `desplegar-visor-publico.yml` («P50 Publicación») |

## 2. El botón (lo único visible)

| Campo | Opciones | Por defecto |
|---|---|---|
| Territorios | `todos` (71), `congreso` (52 provincias), `autonómicas` (19 comunidades) o lista de códigos: `nac22, aut11` | — (obligatorio) |
| Elección | `vigente` (la última de cada territorio) o `2026-11` (el ensayo). Otros `AAAA-MM` (histórico) se aceptan en el botón pero salen en rojo hasta que exista la tarea del histórico (D-137: P30 no tiene aún campo «elección») | `vigente` |
| Modo | `solo comprobar` · `comprobar y lanzar` | `solo comprobar` |
| Publicar | `no` · `sí` | `no` |

No aparecen run ids, sha, rutas, motor, estrategia, «inicio», paralelismo ni «mapa 350» (D-130).

**Traducción del ensayo.** `2026-11` en P00 se pasa a P12 como `eleccion: "ensayo 2026-11-29"`, la única opción de
ensayo que P12 acepta hoy (`preparacion-resultados-electorales.yml`, entrada `eleccion`, 1.0.17). El ensayo **no
persiste ni registra** (P12 fuerza `persist_state=false` y marca el paquete `production_eligible=false`). En P00 eso
significa: en una campaña de ensayo el cierre **no hace commit** en `main`, escribe solo R2 y el issue, y no se
publica aunque se marque «sí» (la comprobación previa lo avisa). Prueba: test de la tabla de traducción (`vigente` →
`vigente`; `2026-11` → `ensayo 2026-11-29`; `2019-11` → rojo «elección no soportada») y test de que el cierre de una
campaña de ensayo produce una lista de ficheros a commitear vacía.

**Listas de códigos mixtas.** Una lista puede mezclar Congreso y autonómicas (`nac22, aut11, aut13`). Con `vigente`
cada territorio toma su propia elección vigente: no hay conflicto. Con un `AAAA-MM` concreto, a un territorio que no
tuvo elección ese mes le sale **rojo por territorio** («sin elección en AAAA-MM») y no entra; los demás siguen. No es
un error global: la campaña solo se niega entera si **ningún** territorio queda en verde o ámbar. Un código
inexistente o `congreso350_*` también es rojo por territorio. Prueba: test de la comprobación previa con
`nac22, aut11, xyz99` y `2026-11` (nac22 verde, aut11 rojo «sin elección», xyz99 rojo «código inexistente»; campaña
lanzable con 1).

## 3. Una campaña = una ejecución

```
P00 Campaña (una ejecución; un solo commit del código para todo)
│
├─ 1. Comprobación previa ──► semáforo por territorio ──► issue de la campaña (se crea aquí)
│        └─ «solo comprobar» termina aquí
│
├─ 2. Cadena por territorio: matriz de hasta 15 a la vez; cada fila llama a «cadena de un territorio»
│        P10 ─► P20 ─► P30, todos los jobs EN SERIE (un solo job ocupado por territorio)
│        (antes de cada paso: ¿hay parada sistémica? si la hay, no empieza el siguiente)
│
├─ 3. Cierre (if: always()): lee R2 ─► informe en el issue ─► un commit en main ─► objeto «cierre» en R2
│
├─ 4. P40 Publicación (solo si «publicar = sí», sin parada, con los que pasaron; nunca en ensayo)
│
└─ 5. Resultado: en rojo si hay ≥1 apartado o parada (así se abre la IA de cierre, §7)
```

- P10, P20, P30 y P40 se llaman **por dentro** como workflows reutilizables (`workflow_call`): ninguna llamada a la
  API para lanzar otras ejecuciones (GitHub admite matriz que llama a reutilizable, fila 11, y hasta 10 niveles de
  anidamiento, fila 9; aquí hay 3 o 4).
- **Forma A (aprobada):** matriz de territorios → reutilizable «cadena de un territorio» (fichero sin botón de la familia
  P00) → P10, P20, P30. Respaldo C (un job por territorio con acciones compuestas) solo si A falla en la prueba de humo.
- **Matriz:** `strategy: {fail-fast: false, max-parallel: 15}`. `fail-fast` viene a `true` por defecto y cancelaría
  todas las filas al primer fallo (fila 18); con `false` un territorio que falla no toca a los demás. `max-parallel`
  limita filas de la matriz, no jobs: por eso hace falta la serie de abajo.
- **Un job por cadena (decisión B).** Hoy `pre_m04_evidence` y `m04` dependen los dos solo de `internal_units`
  (`_reutilizable-generacion-territorial.yml`, l. 877 y 1178) y no coinciden únicamente porque una exige
  `preflight_only` y la otra lo excluye. En la ruta de campaña, `m04` pasa a depender también de `pre_m04_evidence`
  (en éxito o saltado) y, en general, **cada job de la cadena depende del anterior**. Medido en la r3/r4: en las 84 00
  del Operador nunca hubo más de **1 job a la vez** (§12), así que la serie no alarga la cadena; la convierte en
  garantía. Con 15 cadenas: **máximo 15 jobs de la campaña y 5 libres para la CI** (cuenta Free: 20, fila 4). Se
  acepta que la CI de las PR vaya más lenta durante una campaña. Prueba: test que lee el árbol de jobs de la cadena
  (con P10-P30 desplegados) y falla si dos jobs pueden ejecutarse a la vez en la ruta de campaña (cada job tiene como
  mucho un sucesor y un predecesor activos).
- **Resultados por territorio:** GitHub solo devuelve la salida de la última fila de una matriz de reutilizables
  (fila 12); cada territorio deja su resultado en R2 (§5) y el cierre lo lee de ahí.
- **Una campaña a la vez.** A nivel de P00: `concurrency: {group: ddd-p00-campana, cancel-in-progress: false}` (sin
  `queue: max`). Efecto (fila 19): una segunda campaña **espera** a que termine la primera; si llega una tercera
  mientras la segunda espera, GitHub cancela la segunda y deja la tercera. Elijo **encolar una** frente a rechazar:
  un doble clic no lanza dos campañas ni pierde la orden, y la que espera hace su comprobación previa al empezar (CI en
  verde de su versión y caducidad de la ficha de autorización, D-52), así que si la autorización ha caducado se queda en
  «solo comprobar». No se usa `queue: max` (hasta 100 en cola, fila 6): varias campañas encoladas en silencio serían
  campañas no autorizadas a destiempo. La prueba de humo de la PR usa otro grupo (`ddd-p00-pr-<n>`) para no bloquear
  campañas. Prueba: test del YAML que fija el grupo, `cancel-in-progress: false` y la ausencia de `queue` en P00.

### Semáforo de la comprobación previa

| Color | Significa | Ejemplos | Qué hace «comprobar y lanzar» |
|---|---|---|---|
| Verde | Todo listo y compatible | fuentes en R2 con su huella, contrato válido, resultados de esa elección disponibles | lo lanza |
| Ámbar | Se puede, pero regenerará algo | paquete de fuentes caducado (P10 lo rehace), puntos de control incompatibles (P20 empieza de cero) | lo lanza y lo marca |
| Rojo | No se puede | fuente sin espejo que rechaza la nube, `BLOQUEADA_SIN_DATO`, sin elección en ese mes, código inexistente, `congreso350_*` | lo aparta desde el inicio |

Comprobaciones de campaña (si falla una, no se lanza nada): la versión elegida tiene la CI en verde; R2 responde; hay al
menos un territorio verde o ámbar; y se muestra el gasto de Actions de la semana (D-46). Ante errores de red degradan a
aviso y bloquean solo con evidencia positiva (lección T-246). Un rojo de la comprobación previa **no** cuenta como
apartado (no se lanzó) y sale en el informe aparte.

## 4. Políticas: reintentos, apartado y parada sistémica

**Qué es un apartado (arreglo B1).** Un territorio está **sano** en un paso solo si el job terminó en éxito **y** su
salida está escrita en R2 (objeto `pasos/<territorio>/<paso>/<intento>.json` con estado «ok» y huellas). Todo lo demás
es **apartado**: fallo no transitorio, transitorio que agotó sus reintentos, o «sin_resultado». Un job verde sin su
salida en R2 también es apartado (causa `SALIDA_R2_AUSENTE`): nunca cuenta como verde.

**«sin_resultado».** Cancelación, tiempo agotado y runner perdido no dejan que el job escriba su salida. Por eso, al
**empezar** cada paso, el territorio escribe en R2 una marca `sin_resultado` (paso, intento, hora) que el mismo job
sustituye por «ok» o por la causa al terminar. El cierre corre con `if: always()` y cuenta toda marca `sin_resultado`
que siga ahí como apartado con causa `SIN_RESULTADO` (cancelado, tiempo agotado o runner perdido, según la conclusión
del job que da la API). Prueba: test de la herramienta de recuento con un estado sintético en el que un paso quedó en
`sin_resultado` (debe salir apartado, nunca verde).

| Situación | Regla |
|---|---|
| Fallo transitorio (red cortada, 5xx de GitHub o R2, cuota de descarga «código 75», push rechazado) | Hasta **2 reintentos** dentro del mismo paso, con espera de 1 y 5 min. GitHub no reintenta jobs solo: el reintento va en la herramienta. |
| Runner perdido, cancelación o tiempo agotado | Queda `sin_resultado` → apartado. El Operador puede pulsar «Re-ejecutar jobs fallidos» **en la misma ejecución** (misma versión; hasta 50 re-ejecuciones, fila 5), solo para esto y para el cierre. |
| Fallo no transitorio (huella distinta, puerta en rojo, contrato, motor) | **Sin reintento ni re-ejecución.** Apartado con su causa; los demás siguen. |
| Parada sistémica | **≥3 apartados con la misma causa** o apartados **≥20 % de los lanzados con un mínimo de 3** (71 → 15): ningún territorio empieza un paso nuevo; los que están en uno lo terminan. No se publica. El issue lo avisa al momento. |

**Re-ejecuciones (arreglo B1).** Solo se re-ejecutan el cierre y los transitorios (`sin_resultado` o código transitorio).
La herramienta de recuento rechaza, en una re-ejecución, repetir un paso cuyo último intento fue un fallo no
transitorio: el job sale en rojo con «no re-ejecutable». Prueba: test con un apartado `TERRITORIAL_READY_PAIR_INCOMPATIBLE`
y `run_attempt=2` (rechazo) y con `SIN_RESULTADO` y `run_attempt=2` (admitido).

**Recuento sin duplicados.** Cada resultado se guarda con la clave **(campaña, territorio, paso, run_attempt)** y el
recuento usa, para cada (territorio, paso), solo el intento más alto. Escribir dos veces la misma clave da el mismo
objeto (idempotente). Así una re-ejecución que sale bien quita el apartado anterior y ninguna cuenta dos veces. La
campaña se identifica por `run_id`. Prueba: test del recuento con el mismo apartado escrito dos veces (cuenta 1) y con
un intento 1 apartado + intento 2 «ok» (cuenta 0).

- «Misma causa» = el mismo código de causa que imprimen las herramientas (`ARTIFACT_MISSING`,
  `TERRITORIAL_READY_PAIR_INCOMPATIBLE`, `CANDIDATE_FAILED`, `SIN_RESULTADO`…); sin código, «causa desconocida».
- Sin vigilante: cada territorio consulta el recuento **antes** de empezar P10, P20 y P30, y el cierre antes de P40.

**Job `resultado` (arreglo B1).** Último job de P00, `if: always()`. Lee el recuento final y **falla** (salida ≠0) si
hay ≥1 apartado o parada, o si el cierre no terminó. Así la ejecución entera queda en `failure` y se dispara la IA de
cierre de P90, que hoy solo se abre con `workflow_run.name == 'P00 Campaña' && conclusion == 'failure'`
(`p90-automatico.yml`, l. 662). Sin ese job, una campaña con apartados podría terminar en verde (fail-fast falso y
jobs en éxito con apartados en R2) y la IA no se abriría. Con todo verde, `resultado` pasa y no se abre nada. Prueba:
test de la herramienta de `resultado` (0 apartados → 0; 1 apartado → ≠0; cierre pendiente → ≠0) y test del YAML que
comprueba que `resultado` existe con `if: always()` y depende del cierre y de P40.

## 5. Versión fija, estado fuera de `main` y permisos

**Versión fija.** Los reutilizables locales se ejecutan desde el mismo commit que el llamador (fila 13). Todo `checkout`
usa la versión de la ejecución y el estado se lee de R2, no de la cabeza de `main`. Un sha por campaña, en el issue.

**Dónde se guarda cada cosa** (sin cambios respecto a 1.0): **R2** el estado de trabajo (semáforo, intentos, causas,
resultados y productos de cada paso, un objeto por clave de §4: no hay choques); **issue** el informe humano (al
empezar, si hay parada y al terminar; no es base de datos); **`main`** un solo commit al cierre con todo lo durable.
Rama dedicada para el estado: descartada (los pushes concurrentes chocan igual).

**Permisos (arreglo del revisor).** Hoy P10, P20 y P30 declaran `contents: write` para todo el workflow
(`preparacion-fuentes.yml` l. 182-183, `produccion-distritos.yml` l. 202-203, `incorporacion-resultados-electorales.yml`
l. 170-171) y escriben en `main` dentro de sus jobs. Diseño:

| Pieza | Permisos | Qué escribe |
|---|---|---|
| Comprobación previa | `contents: read`, `actions: read`, `issues: write` | crea el issue |
| Cadena de un territorio (P10, P20, P30 dentro) | `contents: read` (la llamada desde P00 pasa ese techo, y un reutilizable no puede subirlo) | solo R2 (secretos R2) |
| Job de registro de cada P10-P30 suelto | `contents: write` en un **job aparte** con `if: inputs.campana == ''` | `main`, como hoy |
| Cierre | `contents: write`, `issues: write` y la app de registro (`DDD_REGISTRO_APP_ID`/`KEY`) | el commit en `main` y el informe |
| P40 Publicación | lo de hoy | lo de hoy |
| IA de cierre (en P90) | `contents: read`, `actions: read`, `issues: write` | comentario en el issue |

La entrada «campaña» (oculta, solo `workflow_call`) es la que activa la ruta de campaña. Pruebas: (1) test que falla si
en la ruta de campaña de P10-P30 (jobs sin `if: inputs.campana == ''`) aparece `git push`, una herramienta de registro
en `main` o `contents: write`; (2) test que fija `contents: read` en la llamada de P00 a la cadena; (3) test de
equivalencia: con «campaña» vacía, P10-P30 sueltos se comportan como hoy (mismos jobs, mismas salidas).

**Grupos globales fuera de la ruta de campaña.** Comprobado en `main` 8221ab9 (T-360/#839 ya quitó
`ddd-catalog-promotion` y `ddd-shared-operational-state` de la 00 y del reutilizable electoral):

| Grupo único | Dónde sigue hoy | En la ruta de campaña |
|---|---|---|
| `ddd-catalog-promotion` | `preparacion-fuentes.yml` l. 475 y `preparacion-resultados-electorales.yml` l. 603 | se omite (el job de registro no corre; el estado va a R2) |
| `ddd-prepared-source-pair` | `preparacion-legislatura-vigente.yml` l. 306 | desaparece con ese fichero (el par va a R2 y al cierre) |
| `ddd-shared-operational-state` | `desplegar-visor-publico.yml` l. 75 | se mantiene: P40 se llama **una vez** por campaña, después del cierre, y el grupo la ordena frente a una publicación suelta |

Los grupos por territorio (`ddd-territorial-prod-<territorio>-<edición>`, `ddd-electoral-prod-<territorio>`) se quedan:
dentro de una campaña cada territorio va una sola vez. Prueba: test que falla si un job de la ruta de campaña usa un
grupo de concurrencia sin el territorio en su nombre (salvo P40).

## 6. El cierre, paso a paso (atomicidad)

El cierre (`if: always()`, después de la matriz) hace, en este orden:

1. **Lee R2** y calcula el recuento final (§4). Calcula la **huella del estado**: sha256 de la lista ordenada de
   claves y huellas de los productos de la campaña.
2. **Informe en el issue** (crea o actualiza el comentario final). Va **antes** del commit: si el commit falla, el
   informe ya dice «cierre pendiente». Si la API del issue falla, el cierre sigue con el commit pero termina en rojo
   (salida ≠0) sin tocar la campaña (los territorios ya terminaron).
3. **Commit en `main`** con la app de registro. Mensaje con el id de campaña y la huella del estado. **Idempotente**:
   si ya hay en `main` un commit con ese id y esa huella, no hace nada (re-ejecutar el cierre no duplica). En ensayo
   la lista de ficheros es vacía y no hay commit (§2).
4. **Push rechazado** (otro robot escribió antes): rebase y reintento, **tope 2**. Si falla, no fuerza nada: informe
   «cierre pendiente» en el issue, cierre en rojo, y el Operador re-ejecuta solo el cierre.
5. **Objeto `cierre` en R2** (id de campaña, sha del commit, huella), escrito **solo después** de que el push se
   confirme. Una re-ejecución que lo encuentra con la misma huella termina en verde sin hacer nada.

**El commit de cierre cuenta como robot.** P90 trata un push como robot (`needs.cambios.outputs.robot`, l. 53-95) si
el autor es `[bot]` y **todas** las rutas están en `RUTAS_ROBOT`; un robot no cancela la CI de `main` (los grupos
`ddd-main-*` solo se usan con `robot != 'true'`). El cierre escribe solo rutas de esa lista. Prueba: test que calcula
la lista de ficheros que el cierre puede escribir y comprueba que todas casan con `RUTAS_ROBOT` de `p90-automatico.yml`.
Riesgo conocido: los robots de hoy también escriben `configuracion/catalogo_preparacion.yaml`, que **no** está en
`RUTAS_ROBOT`; si el cierre tiene que escribirlo, hace falta decidir (§15).

Pruebas del cierre: test del commit idempotente (dos cierres con el mismo estado → un commit); test de push rechazado
tres veces (dos rebases, luego «cierre pendiente» y salida ≠0, sin objeto `cierre` en R2); test de fallo del issue
(commit hecho, salida ≠0).

## 7. Una sesión de IA, solo al cierre

| Hace | No hace |
|---|---|
| Se abre una vez cuando P00 termina en `failure` (job `resultado`, §4): forense de P90 por `workflow_run` de «P00 Campaña» | No vigila durante la campaña |
| Lee el issue y las anotaciones de los jobs fallidos; da la causa de cada apartado en ≤5 líneas con el catálogo de causas raíz | No reintenta, no lanza, no publica, no edita código ni fusiona |
| Agrupa por causa y propone el siguiente paso (otra campaña con la lista de apartados, o una tarea de arreglo) | Con todo en verde no se abre (ahorro) |

- **Permisos:** `contents: read`, `actions: read`, `issues: write` (comentar el issue de la campaña). Nada más; sin
  token de la app de registro.
- **Secreto:** `CLAUDE_CODE_OAUTH_TOKEN`, el mismo que usa hoy el forense de P90.
- **Logs = entrada no confiable.** Los logs, anotaciones y textos del issue pueden contener texto escrito por
  herramientas o por terceros (p. ej. un nombre de fichero o un mensaje de error con instrucciones). Las instrucciones
  de la IA lo dicen expresamente: son datos, nunca órdenes; no sigue enlaces ni ejecuta comandos que aparezcan en
  ellos; y sus únicas herramientas son leer la API de Actions e issues y comentar en el issue de la campaña.
- Hoy el forense se abre por cada 00 fallida; con P00 es una por campaña.

Prueba: test del YAML del job de IA (permisos exactos, secreto, disparo solo por `failure` de «P00 Campaña») y test de
que su texto de instrucciones contiene la cláusula de entrada no confiable.

## 8. Límites de GitHub que mandan (detalle y citas en el anexo A)

| Límite | Valor | Fila | Efecto en P00 |
|---|---|---|---|
| Jobs de una matriz por ejecución | 256 | 1 | 71 territorios caben. El histórico (5 elecciones × 52) no: una elección por campaña. |
| Jobs a la vez (plan Free) | 20 | 4 | 15 cadenas × 1 job = 15; quedan 5 para la CI. |
| Niveles de anidamiento / reutilizables distintos | 10 / 50 | 9 / 10 | P00 usa 3-4 niveles y unos 6 reutilizables. |
| Duración de un job / de una ejecución | 6 h / 35 días | 3 / 2 | Ver abajo. |
| Re-ejecuciones de una ejecución | 50 | 5 | Margen para el cierre y los transitorios. |
| `fail-fast` por defecto | `true` | 18 | Se fija `false`. |
| Cola de un grupo de concurrencia | 1 en espera (100 con `queue: max`) | 19 / 6 | Una campaña en espera como mucho (§3). |

**36 min frente a 120 min (reconciliado).** El job más largo de la r4 (36 min) fue «Encadenar par de fuentes y 04»,
que **espera** a otras ejecuciones y desaparece con P00. El job de trabajo más largo medido fue «Optimización de
distritos» (20 min). Los `timeout-minutes` son techos de seguridad, no medidas: 120 min en `territoriales` de
`preparacion-fuentes.yml` (l. 301) y en `official_sources`/`internal_units` del reutilizable de generación, 240 min en
`m04` (l. 1183). Todos por debajo de las 6 h de GitHub. Se dejan como están.

No verificado (no está en la documentación): si los jobs de los reutilizables llamados desde una matriz cuentan para los
256, y un tope de jobs por ejecución aparte del de la matriz. Se ve en la prueba de humo y en la validación (§11).

## 9. Qué se absorbe y qué se retira

| Hoy | Dónde queda | Se retira |
|---|---|---|
| `gestor-campanas.yml` («P00 Campaña — Gestor») | Botón de P00; el plan → comprobación previa; la matriz → cadena | Tras el 29-11, en la PR de retirada (§13) |
| `preparacion-legislatura-vigente.yml` («P00 Campaña — Legislatura») | P10 (P11 + P12) dentro de la cadena; el par a R2 y al cierre | Ídem |
| `activacion-por-eleccion.yml` («P00 Campaña — Elección») | La expansión elección → territorios en la comprobación previa (`clave_eleccion.py`) | Ídem |
| `ejecucion-completa-proyecto.yml` (la 00) | Sus jobs, en P10/P20/P30/P40 y la cadena; manifiesto y estado → cierre | **No en la PR 3**: tras el 29-11, en la PR de retirada |
| `_reutilizable-puerta-validacion.yml` | Acción compuesta «puerta de validación» | En la PR 2 |
| Forense por cada 00 (dentro de P90) | Forense por campaña (§7) | En la PR 4 |

Mientras convivan P00 y la 00, las dos se llaman «P00 Campaña»: el disparo de P90 (por nombre) sirve para ambas. P00
nueva lleva en el run-name «· campaña ·» para distinguirla en el tablero y en las métricas.

## 10. Validación desde la rama (decisión A)

GitHub solo muestra el botón con el fichero en `main`, pero deja lanzarlo desde otra rama por la API si ya se ejecutó
una vez (fila 14). Por eso la PR 3 lleva una prueba de humo por el evento de la PR.

- **El cierre de una validación no escribe en `main`.** Si la ejecución no viene de `main`, el cierre hace su commit
  en una **rama de cierre** `p00-cierre/<run_id>` creada desde `main` y, si el propietario lo quiere, abre una PR en
  borrador con `no-automerge` para ver la diferencia. Nada se fusiona. El objeto `cierre` en R2 guarda esa rama.
- La rama de cierre no dispara la CI de `main` (P90 corre en push a `main` y en PR).
- Prueba: test del cierre que, con `github.ref` distinto de `refs/heads/main`, elige la rama `p00-cierre/<run_id>` y
  nunca `main`.

Pasos (con frase del propietario al Operador, D-52, cada uno):

1. Prueba de humo en la PR: sintaxis y comprobación previa sintética.
2. **aut11** (Extremadura) desde la rama: «solo comprobar» y «comprobar y lanzar», publicar = no. Criterio: una sola
   ejecución, ningún lanzamiento por la API, M06 bit a bit igual al vigente, commit en la rama de cierre y el issue
   completo; nunca más de 15 jobs a la vez.
3. **Re-ensayo corto** con nac22, nac42 y nac52, `elección = 2026-11`, publicar = no: sin commit (es ensayo); un fallo
   transitorio forzado (se reintenta) y uno no transitorio (se aparta, los otros dos siguen y `resultado` sale en rojo).

## 11. Calendario (decisión C)

- **La noche del 29-11 va con la 00 actual como caso base** (ya llama a los P10-P40 nuevos). No es un respaldo: es el
  plan.
- P00 se valida (§10) cuando estén P10, P20 y P30 fusionados (tras el ensayo en seco) y **se fusiona después del 29-11**.
- La 00 no se borra hasta después del 29-11 y de que P00 haya hecho al menos una campaña real.

## 12. Coste y reloj (reproducibles)

**Filtro exacto.** `GET repos/jfmurciego/diputadodedistrito/actions/workflows/ejecucion-completa-proyecto.yml/runs`
con `created` en seis ventanas de 6 h entre `2026-11-15T00:00:00Z` y `2026-11-16T12:00:00Z` (la API corta a 1.000
por consulta), y lo mismo para `preparacion-legislatura-vigente.yml`. Por cada ejecución,
`GET actions/runs/<id>/jobs?filter=all` (paginado). **Minutos = suma, por job no saltado, de `completed_at −
started_at`** (el `/timing` da 0 en un repositorio público).

**Recuento.** Hoy la API da **203** ejecuciones de la 00 con ese filtro: **161** `workflow_dispatch` y **42**
`pull_request` (la prueba de humo de las PR, 40 min en total, excluidas). Las 161 del 1.0 son las `workflow_dispatch`:

| Grupo (15-11 00:00 → 16-11 12:00 UTC) | Ejecuciones | En éxito | Minutos |
|---|---|---|---|
| 00 del Operador | 84 (71 territorios; 8 con más de una) | 76 | 4.005 |
| 00 «Reutilizar» del bot (`github-actions[bot]`) | 77 | 73 | 921 |
| Total 00 `workflow_dispatch` | 161 | 149 | 4.926 |
| «Legislatura» (bot) | 81 | 77 | 219 |
| **Total** | | | **5.145** |

De los 4.005 min del Operador, **649** son del job «Encadenar par de fuentes y 04», que solo espera a otras
ejecuciones y desaparece con P00. Por territorio (00 del Operador): mediana 50 min, percentil 90 77 min, máximo 130.

**Estimación con P00.** Trabajo real ≈ 4.005 − 649 + 219 (Legislatura, pasa a P10) = **≈3.575 min**, más la parte
electoral que hoy hace la 00 del bot (≤921 min): **≈3.600-4.500 min por campaña de 71** (menos de un tercio del tope
semanal de 15.000, T-155).

**Reloj con 15 a la vez.** Medido: en las 84 00 del Operador nunca hubo más de 1 job a la vez y la relación minutos /
reloj fue 0,82 (el resto, arranque y cola de runner). Por eso poner `m04` en serie **no cambia el reloj**.

| Caso | Cuenta | Reloj |
|---|---|---|
| Sin cola, bien repartido | 3.600-4.500 min / 15 | **4,0-5,0 h** |
| Con el arranque medido (÷0,82) | | 4,9-6,1 h |
| Peor caso (la cadena más larga, 130 min, al final) | + 2,2 h | hasta ≈7 h |

Las cifras se reproducen con el filtro, las ventanas y la suma por job descritos arriba (recalculadas el 16-11 con
la API; dan las mismas 161 / 4.926 min del 1.0). La sesión de IA del cierre: una por campaña, Sonnet; su coste
no consta aún en el repositorio.

## 13. Plan de PR de T-379

| # | PR | Contenido | Prueba que la cierra |
|---|---|---|---|
| 1 | Estado de campaña | Herramientas de comprobación previa, semáforo, recuento (clave §4, `sin_resultado`, parada), `resultado`, cierre (huella, idempotencia) e informe; lectura/escritura en R2; sin workflows | tests de §2, §4 y §6 |
| 2 | Puerta como acción compuesta | Sustituye `_reutilizable-puerta-validacion.yml` | test de equivalencia |
| **2b** | Entrada «campaña» en P10-P30 | Entrada oculta `campana` en su `workflow_call`; ruta de campaña con `contents: read`, solo R2, sin grupos globales, jobs en serie; job de registro aparte con `if: inputs.campana == ''`. **Sin cambiar su comportamiento suelto** | tests de §3 (serie) y §5 (sin push, permisos, equivalencia, grupos) |
| 3 | P00 Campaña | `p00-campana.yml` + cadena + cierre + `resultado` + issue; skills; **no borra la 00** ni el Gestor | tests de §3 (concurrencia), §6 y §10; prueba de humo |
| 4 | IA de cierre | Forense por campaña en P90 (§7) | test de §7 |
| 5 | Retirada (tras el 29-11) | Borra la 00, Gestor, Legislatura y Elección; listas de los tests de catálogo | tests de catálogo |

PR 1 puede empezar ya; 2, 2b y 3 tras T-377 y tras fusionarse P10-P30; 3 se fusiona después del 29-11.

## 14. Arreglos del revisor: sección y prueba

| Arreglo | Sección | Prueba prevista |
|---|---|---|
| Apartado = job en éxito con salida en R2 | §4 | recuento con job verde sin salida → apartado |
| Job `resultado` en rojo con ≥1 apartado o parada (dispara la IA) | §4 | herramienta 0/1/pendiente + YAML `if: always()` |
| Re-ejecución solo del cierre y de transitorios | §4 | `run_attempt=2` admitido/rechazado |
| Recuento idempotente por (campaña, territorio, paso, run_attempt) | §4 | doble escritura y reintento que sana |
| Marca `sin_resultado` (cancelación, tiempo agotado, runner perdido) | §4 | estado sintético → apartado |
| Cadena con `contents: read`; push en job aparte; solo el cierre escribe | §5 | sin `git push` en la ruta de campaña; permisos; equivalencia |
| IA de cierre: permisos mínimos, secreto, entrada no confiable | §7 | YAML y cláusula |
| Concurrencia de P00 (encolar una) | §3 | YAML |
| Cierre atómico (huella, idempotencia, R2 después del push, tope 2, issue antes) | §6 | tres tests del cierre |
| Grupos globales fuera de la ruta de campaña | §5 | grupos con territorio |
| Commit de cierre como robot | §6 | rutas ⊆ `RUTAS_ROBOT` |
| PR 2b, la 00 no se borra en la PR 3, 29-11 con la 00 | §11, §13 | — (plan) |
| Traducción `2026-11` ↔ «ensayo 2026-11-29»; el ensayo no commitea | §2 | tabla y cierre vacío |
| Listas mixtas con elección inexistente | §2 | rojo por territorio |
| Citas del anexo renumeradas y verificadas | anexo A 1.1 | — (ruta de fuente por fila) |
| 36 min frente a 120 min | §8 | — |
| Coste y reloj reproducibles | §12 | — (filtro y criterio) |

## 15. Decisiones que aún necesito del propietario

1. **Concurrencia de P00:** encolar una campaña (recomendado, §3) o rechazar la segunda mientras haya una en curso.
2. **Commit de cierre y `RUTAS_ROBOT`:** si el cierre debe escribir `configuracion/catalogo_preparacion.yaml` (hoy fuera
   de la lista), (a) añadir esa ruta exacta a `RUTAS_ROBOT` (la cubre la batería nocturna) — recomendado — o (b) aceptar
   que ese cierre lance la suite completa en `main`.
3. **Rama de cierre de la validación:** solo la rama (recomendado) o rama + PR en borrador con `no-automerge`.
