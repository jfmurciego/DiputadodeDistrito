# T-378 · Diseño al detalle de P00 Campaña y de la nueva forma de trabajar

VERSIÓN: 1.1.3 · FECHA: 2026-11-16 · ANTERIOR: `legacy/docs/ESTUDIOS/T378_P00_CAMPANA/DISENO_P00_CAMPANA_v1.1.2.md` ·
ESTADO: propuesta para el revisor independiente y el propietario (T-387, D-145)
CAMBIOS 1.1.0: decisiones A, B y C de D-145 (la validación desde la rama no escribe en `main`; 15 territorios a la vez
con un solo job por cadena; la noche del 29-11 con la 00 actual) y todos los arreglos del revisor del diseño 1.0:
qué es un apartado y cómo falla el job `resultado`, re-ejecuciones, recuento sin duplicados, marca «sin_resultado»,
permisos por job, cierre atómico, grupos globales fuera de la ruta de campaña, commit de cierre como robot, IA de cierre
con permisos mínimos y logs como entrada no confiable, plan de PR con la 2b, traducción del ensayo, listas de códigos
mixtas, citas del anexo renumeradas, reloj y coste reproducibles.
CAMBIOS 1.1.1: revisor independiente sobre 1.1.0 (PASS_WITH_EXCEPTIONS): (M1) el registro de P10-P30 sueltos sale a un
reutilizable propio, porque un reutilizable no puede pedir más permisos que su llamador; (M2) la decisión A solo es firme
si los secretos de la app de registro pasan a un entorno limitado a `main`; (m1) apartado = job en éxito con causa en R2
y jobs en serie con `!cancelled()`; (m2) cierre con `!cancelled()`, campaña cancelada entera e idempotencia en la rama
de destino; (m3) anexo: `queue: max` marcado como no verificado para esta cuenta.
CAMBIOS 1.1.2: revisión de la 1.1.1 (M2 condicionado): inventario verificado de los usos de la app de registro con su job
y entorno, partición de los 3 jobs que ya tienen otro entorno, `registro` sin revisores, cierre en dos jobs excluyentes
por rama, efecto en los robots que corren con otra ref, secretos de entorno en reutilizables marcados no verificados,
recuento de `queue: max` con criterio, campaña cancelada sin forense.
CAMBIOS 1.1.3: decisiones del propietario D-147 sobre §15 (segunda campaña rechazada con aviso; el cierre no se amplía a
`RUTAS_ROBOT` y dispara la CI de `main`; cierre de validación en rama + PR en borrador; entorno `registro`).
MOTIVO: D-145 (corrige D-143 tras el revisor del diseño 1.0), revisiones de la 1.1.0 y la 1.1.1, y D-147.

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
| Decisiones finales (D-147) | 4 abiertas | segunda campaña rechazada; cierre con CI de `main`; validación en rama + PR en borrador; entorno `registro` | §3, §6, §10, §15 |

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
├─ 3. Cierre (if: !cancelled()): lee R2 ─► informe en el issue ─► un commit en main ─► objeto «cierre» en R2
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
- **Una campaña a la vez (D-147: se rechaza la segunda).** P00 **no** lleva grupo de concurrencia a nivel de workflow
  (con él, GitHub encola la segunda en vez de rechazarla, fila 19). El primer job, la comprobación previa, consulta por
  la API las ejecuciones de P00 en curso (`in_progress`, `queued`, `waiting`) del mismo workflow: si hay otra, la
  ejecución termina en rojo con el aviso «hay otra campaña en curso (run <id>)», sin lanzar nada ni escribir en R2, y
  abre o comenta el issue de la campaña en curso. Si dos arrancan a la vez y se ven mutuamente, sigue la de `run_id`
  menor y se rechaza la otra. Las ejecuciones de la prueba de humo (`pull_request`) no cuentan ni bloquean. Prueba:
  test de la herramienta de comprobación con una lista sintética de ejecuciones (ninguna → sigue; otra en curso →
  rechazo; dos simultáneas → sigue la menor) y test del YAML que comprueba que P00 no declara `concurrency` de workflow.

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

**Qué es un apartado (arreglo B1, fijado en 1.1.1).** Cada paso de la cadena **termina siempre en éxito** cuando ha
podido decidir: escribe en R2 `pasos/<territorio>/<paso>/<intento>.json` con estado «ok» (y huellas) o con estado
«apartado» y su **causa** (fallo no transitorio o transitorio con los reintentos agotados), y pasa la salida
`sano=true|false`. Así un territorio apartado **no** pone la matriz en rojo ni toca a los demás, y la fuente de verdad
es R2, no el color del job. Un job en **rojo** es un fallo que la herramienta no pudo atrapar: se cuenta como
apartado con causa `FALLO_NO_CONTROLADO`. Un job en éxito **sin** objeto en R2 se cuenta como apartado con causa
`SALIDA_R2_AUSENTE`. Nunca cuenta como verde nada que no tenga «ok» en R2.

**Serie dentro de la cadena.** Cada job posterior lleva
`if: ${{ !cancelled() && needs.<previo>.result == 'success' && needs.<previo>.outputs.sano == 'true' }}`: si el paso
anterior apartó el territorio (o falló), el resto se **salta** sin cancelar la matriz; si la campaña se cancela, no
arranca nada nuevo. Prueba: test del YAML de la cadena que exige esa condición en todo job con predecesor.

**«sin_resultado».** Cancelación, tiempo agotado y runner perdido no dejan que el job escriba su salida. Por eso, al
**empezar** cada paso, el territorio escribe en R2 una marca `sin_resultado` (paso, intento, hora) que el mismo job
sustituye por «ok» o por la causa al terminar. El cierre (§6) cuenta toda marca `sin_resultado`
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

**Job `resultado` (arreglo B1).** Último job de P00, `if: ${{ !cancelled() }}`. Lee el recuento final y **falla** (salida ≠0) si
hay ≥1 apartado o parada, o si el cierre no terminó. Así la ejecución entera queda en `failure` y se dispara la IA de
cierre de P90, que hoy solo se abre con `workflow_run.name == 'P00 Campaña' && conclusion == 'failure'`
(`p90-automatico.yml`, l. 662). Sin ese job, una campaña con apartados podría terminar en verde (fail-fast falso y
jobs en éxito con apartados en R2) y la IA no se abriría. Con todo verde, `resultado` pasa y no se abre nada. Prueba:
test de la herramienta de `resultado` (0 apartados → 0; 1 apartado → ≠0; cierre pendiente → ≠0) y test del YAML que
comprueba que `resultado` existe con `!cancelled()` y depende del cierre y de P40.

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
| Cadena de un territorio (P10, P20, P30 dentro) | `contents: read`; P10-P30 declaran también `contents: read` a nivel de workflow | solo R2 (secretos R2) |
| Registro de P10-P30 sueltos | `contents: write`, en un **reutilizable de registro propio** (p. ej. `_p-registro.yml`, sin botón) que solo llama el botón suelto de cada P10-P30 | `main`, como hoy |
| Cierre | `contents: write`, `issues: write` y la app de registro (`DDD_REGISTRO_APP_ID`/`KEY`) | el commit en `main` y el informe |
| P40 Publicación | lo de hoy | lo de hoy |
| IA de cierre (en P90) | `contents: read`, `actions: read`, `issues: write` | comentario en el issue |

**Por qué un reutilizable aparte (M1, 1.1.1).** GitHub no deja que un workflow llamado suba los permisos de su
llamador: «The `GITHUB_TOKEN` permissions passed from the caller workflow can be only downgraded (not elevated) by the
called workflow» (anexo A, fila 22). Si P10-P30 siguieran declarando `contents: write` y P00 los llamara con `read`, la
ejecución no arrancaría (error de arranque), aunque el job que escribe tuviera un `if` falso. Por eso P10-P30 pasan a
`contents: read` en todo el fichero, y lo que hoy escriben en `main` se mueve a un reutilizable de registro con
`contents: write` que **solo** llama la ruta suelta (el botón de cada P10-P30, que tiene `workflow_dispatch` y sus
propios permisos). P00 nunca llama a ese reutilizable.

La entrada «campaña» (oculta, solo `workflow_call`) es la que activa la ruta de campaña. Pruebas: (1) test que falla si
P10-P30 o la cadena declaran `contents: write` o contienen `git push` o una herramienta de registro en `main` fuera del
reutilizable de registro; (2) test que fija `contents: read` en la llamada de P00 a la cadena y que P00 no llama al
reutilizable de registro; (3) test de equivalencia: con «campaña» vacía, P10-P30 sueltos hacen lo mismo que hoy
(mismos jobs y salidas, el registro dentro del reutilizable); (4) la **prueba de humo** de la PR 3 comprueba que P00
arranca con `contents: read` (sin error de arranque).

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

El cierre (`if: ${{ !cancelled() }}`, después de la matriz) hace, en este orden:

1. **Lee R2** y calcula el recuento final (§4). Calcula la **huella del estado**: sha256 de la lista ordenada de
   claves y huellas de los productos de la campaña.
2. **Informe en el issue** (crea o actualiza el comentario final). Va **antes** del commit: si el commit falla, el
   informe ya dice «cierre pendiente». Si la API del issue falla, el cierre sigue con el commit pero termina en rojo
   (salida ≠0) sin tocar la campaña (los territorios ya terminaron).
3. **Commit en `main`** con la app de registro. Mensaje con el id de campaña y la huella del estado. **Idempotente**:
   si ya hay **en la rama de destino** (`main`, o `p00-cierre/<run_id>` en una validación, §10) un commit con ese id y
   esa huella, no hace nada (re-ejecutar el cierre no duplica). En ensayo
   la lista de ficheros es vacía y no hay commit (§2).
4. **Push rechazado** (otro robot escribió antes): rebase y reintento, **tope 2**. Si falla, no fuerza nada: informe
   «cierre pendiente» en el issue, cierre en rojo, y el Operador re-ejecuta solo el cierre.
5. **Objeto `cierre` en R2** (id de campaña, sha del commit, huella), escrito **solo después** de que el push se
   confirme. Una re-ejecución que lo encuentra con la misma huella termina en verde sin hacer nada.

**Campaña cancelada entera.** Si alguien cancela la ejecución, el cierre (`!cancelled()`) no arranca: es una
campaña **abortada**. No hay commit; lo hecho queda en R2 y el issue se queda con el último estado. El Operador puede
re-ejecutar los jobs cancelados en la misma ejecución (el recuento de §4 evita duplicar y no repite pasos «ok» porque
cada paso empieza leyendo su objeto en R2) o dejarla abortada; la siguiente campaña lo vuelve a comprobar todo. Se usa
`!cancelled()` y no `always()` para no depender de si GitHub arranca o no jobs `always()` tras una cancelación; la
prueba de humo cancela una vez a propósito y comprueba que no se escribe nada. Una ejecución cancelada termina en
`cancelled`, no en `failure`: **no se abre la IA de cierre** (P90 solo se dispara con `failure`, §7). Es lo buscado: la
cancelación la decide una persona, que ya sabe por qué.

**El commit de cierre y la CI de `main` (D-147).** El cierre escribe también `configuracion/catalogo_preparacion.yaml`,
que no está en `RUTAS_ROBOT`, y la lista **no se amplía**: P90 no lo trata como robot y lanza la batería completa en
`main`. Es un push por campaña, así que el coste es una batería por campaña. Efecto conocido: como push «no robot»,
usa los grupos `ddd-main-*` con `cancel-in-progress: true`, de modo que un push de código posterior la cancela, o el
cierre cancela la de un push de código anterior aún en curso; vale la regla de «`main` en verde» de siempre (una
batería cancelada no cuenta hasta que otra completa termine en verde). Prueba: test que calcula la lista de ficheros
que el cierre puede escribir y comprueba que todas están en `RUTAS_ROBOT` salvo `configuracion/catalogo_preparacion.yaml`
(si aparece otra ruta, el test falla y se decide aparte).

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
| Cola de un grupo de concurrencia | 1 en espera (100 con `queue: max`) | 19 / 6 | Por eso P00 no usa grupo de workflow: la segunda campaña se rechaza en la comprobación previa (§3, D-147). |

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
  en una **rama de cierre** `p00-cierre/<run_id>` creada desde `main` y abre una **PR en borrador** con `no-automerge` hacia `main` para ver
  la diferencia (D-147). Nada se fusiona: la PR se cierra sin fusionar tras revisar la validación. El objeto `cierre` en R2 guarda esa rama.
- **Quién lo garantiza (M2, 1.1.1).** Esa regla vive en el código de la propia rama: una rama modificada y lanzada por
  la API podría saltársela y escribir en `main` con la app de registro, porque hoy sus secretos
  (`DDD_REGISTRO_APP_ID`/`KEY`) son del repositorio y cualquier rama los lee. Para que sea firme:
  1. los secretos de la app pasan a un **entorno** `registro` con ramas de despliegue limitadas a `main` (anexo A,
     fila 23: «Secrets stored in an environment are only available to workflow jobs that reference the environment», y
     la regla de ramas se compara con el `GITHUB_REF` de la ejecución); se borran los del repositorio;
  2. todo job que usa la app declara `environment: registro` (inventario abajo). El entorno `registro` **no lleva
     revisores obligatorios ni temporizador**: solo la regla de ramas; si no, cada registro de robot esperaría
     aprobación;
  3. el **cierre de P00 son dos jobs excluyentes**: `cierre_main` con `if: github.ref == 'refs/heads/main'`,
     `environment: registro` y la app; y `cierre_rama` con `if: github.ref != 'refs/heads/main'`, sin entorno, con
     `GITHUB_TOKEN` (`contents: write`) hacia `p00-cierre/<run_id>`. Hace falta separarlos porque un job con
     `environment: registro` lanzado desde otra rama **no se salta**: GitHub rechaza el despliegue y el job falla. El
     token del workflow no se puede limitar a una rama; lo que impide que escriba en `main` es el ruleset
     `proteger-main` (exige `veredicto` y ese token no está entre las excepciones); se comprueba en la validación con
     un push de prueba que debe ser rechazado (`GH013`).
  Sin el punto 1, la decisión A queda como **norma del código revisado**, no como garantía (§15).

**Inventario de usos de la app** (verificado en `main` 8221ab9; criterio: líneas con `secrets.DDD_REGISTRO_APP_ID`,
cada una con su `KEY` al lado = un uso; otros 8 ficheros solo la citan en comentarios). **25 usos en 11 ficheros**:

| Fichero (lo hereda) | Jobs con la app (línea del secreto) | Entorno hoy |
|---|---|---|
| `_reutilizable-generacion-territorial.yml` (→ P20, T-377) | `pre_m04_evidence` (900), `pre_m04_diagnostic` (1034), `registrar` (1436) | — |
| `_reutilizable-incorporacion-electoral.yml` (→ P30) | `registrar` (376) | — |
| `_reutilizable-publicar-sitio.yml` (→ P40, T-372) | `publicar` (149) | **`github-pages`** (l. 126) |
| `desplegar-visor-publico.yml` (→ P40, T-372) | `preparar_publicacion` (89) | **`produccion`** para personas (l. 72) |
| `ejecucion-completa-proyecto.yml` (la 00; se retira tras el 29-11) | `detectar_recuperacion_electoral` (948), `actualizar_estado` (1340), `manifestar` (1572) | — |
| `p70-archivo.yml` (P70, ya en `main`) | `archivar_r2` (116), `resolver_producto` (238), `acreditar` (409), `registrar` (628), `acreditar_registro` (701), `extraer_m06` (795), `podar` (913) | `podar`: **`produccion`** si no es simulación (l. 898, puerta humana del borrado irreversible) |
| `p90-automatico.yml` (P90) | `catalogo` (398), `resultados` (462), `numeracion` (528), `metricas` (770) | — |
| `auto-merge.yml` | `fusionar` (53) | — |
| `preparacion-fuentes.yml` (→ P10) | `registrar` (496), `generation_pending` (562) | — |
| `preparacion-legislatura-vigente.yml` (se retira) | `registrar_par` (320) | — |
| `preparacion-resultados-electorales.yml` (→ P10) | `registrar` (613) | — |

- **Los 3 jobs que ya tienen entorno** se parten: el trabajo con su entorno (`github-pages` o `produccion`) y el
  registro en `main` en un job **posterior** con `environment: registro` (sin `produccion`), que solo recibe salidas
  del anterior. En `podar` la puerta humana sigue delante del borrado y el registro va después. Lo hace la PR 2a sobre
  P70; en P40 lo hereda T-372 (si T-372 se fusiona antes, la PR 2a lo aplica sobre `p40-publicacion.yml`).
- **Efecto buscado en los robots:** con el entorno, ningún job con la app puede registrar si la ejecución no es de
  `main`: P10-P30, P70 y P80 lanzados desde una rama, o cualquier `pull_request`, dejan de poder escribir en `main`.
  Los de P90 (`catalogo`, `resultados`, `numeracion` en push a `main`; `metricas` por calendario/`workflow_run`) y
  `auto-merge` (`workflow_run`, que corre con la rama por defecto, anexo fila 15) siguen funcionando. La PR 2a lo
  comprueba job por job contra este inventario.
- **No verificado:** que un job de un **reutilizable llamado** que declara `environment: registro` reciba los secretos
  del entorno (la documentación no lo dice expresamente). La PR 2a lo prueba con una ejecución real de humo antes de
  borrar los secretos del repositorio.
- La rama de cierre no dispara la CI de `main` (P90 corre en push a `main` y en PR).
- Prueba: (1) test de que ningún workflow usa `secrets.DDD_REGISTRO_APP_*` en un job sin `environment: registro`;
  (2) en la validación de aut11, el log del cierre muestra el destino `p00-cierre/<run_id>` y `main` no recibe commit;
  (3) test de que `cierre_main` y `cierre_rama` tienen condiciones de rama opuestas y solo `cierre_main` usa la app.
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
| **2a** | Entorno `registro` (D-147) | Entorno sin revisores y limitado a `main`; `environment: registro` en los 25 usos del inventario (§10); parte `podar`, `preparar_publicacion` y `publicar`; humo real con un reutilizable; después el propietario traslada los secretos y borra los del repositorio | test de secretos con entorno; humo |
| **2b** | Entrada «campaña» en P10-P30 | Entrada oculta `campana`; P10-P30 con `contents: read`; registro suelto a un reutilizable propio; ruta de campaña solo R2, sin grupos globales, jobs en serie con `!cancelled()`. **Sin cambiar su comportamiento suelto** | tests de §3 (serie) y §5 (sin push, permisos, equivalencia, grupos) |
| 3 | P00 Campaña | `p00-campana.yml` + cadena + cierre + `resultado` + issue; skills; **no borra la 00** ni el Gestor | tests de §3 (concurrencia), §6 y §10; prueba de humo |
| 4 | IA de cierre | Forense por campaña en P90 (§7) | test de §7 |
| 5 | Retirada (tras el 29-11) | Borra la 00, Gestor, Legislatura y Elección; listas de los tests de catálogo | tests de catálogo |

PR 1 ya en curso (T-379); 2a, 2, 2b, 3 y 4 detrás de T-377 y de la fusión de P10-P30; 2a antes de la 3 (la 3 depende del entorno `registro` para `cierre_main`); 3 se fusiona después del 29-11.

## 14. Arreglos del revisor: sección y prueba

| Arreglo | Sección | Prueba prevista |
|---|---|---|
| Apartado = job en éxito con salida en R2 | §4 | recuento con job verde sin salida → apartado |
| Job `resultado` en rojo con ≥1 apartado o parada (dispara la IA) | §4 | herramienta 0/1/pendiente + YAML `!cancelled()` |
| Re-ejecución solo del cierre y de transitorios | §4 | `run_attempt=2` admitido/rechazado |
| Recuento idempotente por (campaña, territorio, paso, run_attempt) | §4 | doble escritura y reintento que sana |
| Marca `sin_resultado` (cancelación, tiempo agotado, runner perdido) | §4 | estado sintético → apartado |
| Cadena con `contents: read`; registro suelto en reutilizable propio (M1); solo el cierre escribe | §5 | sin `contents: write` ni push en P10-P30; humo: P00 arranca con `read` |
| Decisión A garantizada por entorno, no por el código de la rama (M2) | §10 | secretos con entorno; push de prueba rechazado |
| Serie con `!cancelled()`; cierre y `resultado` con `!cancelled()`; campaña cancelada (m1, m2) | §4, §6 | YAML; humo con una cancelación |
| IA de cierre: permisos mínimos, secreto, entrada no confiable | §7 | YAML y cláusula |
| Segunda campaña rechazada con aviso (D-147) | §3 | comprobación con ejecuciones sintéticas; sin `concurrency` de workflow |
| Cierre atómico (huella, idempotencia, R2 después del push, tope 2, issue antes) | §6 | tres tests del cierre |
| Grupos globales fuera de la ruta de campaña | §5 | grupos con territorio |
| Commit de cierre y CI de `main` (D-147) | §6 | rutas ⊆ `RUTAS_ROBOT` + `catalogo_preparacion.yaml` |
| PR 2b, la 00 no se borra en la PR 3, 29-11 con la 00 | §11, §13 | — (plan) |
| Traducción `2026-11` ↔ «ensayo 2026-11-29»; el ensayo no commitea | §2 | tabla y cierre vacío |
| Listas mixtas con elección inexistente | §2 | rojo por territorio |
| Citas del anexo renumeradas y verificadas | anexo A 1.1 | — (ruta de fuente por fila) |
| 36 min frente a 120 min | §8 | — |
| Coste y reloj reproducibles | §12 | — (filtro y criterio) |

## 15. Decisiones del propietario

Tomadas el 16-11 (**D-147**) sobre las cuatro que quedaban:

1. **Segunda campaña:** se **rechaza con aviso** mientras otra esté en curso; no se encola (§3).
2. **`RUTAS_ROBOT`:** `configuracion/catalogo_preparacion.yaml` **no** entra en la lista; el commit de cierre dispara la
   CI de `main` (§6).
3. **Cierre de una validación:** rama `p00-cierre/<run_id>` **+ PR en borrador** con `no-automerge` (§10).
4. **Garantía de la decisión A:** entorno `registro` limitado a `main` con los secretos de la app (opción a, PR 2a),
   tocando los 25 usos y separando en job propio el registro de los jobs que ya tienen entorno (§10).

No quedan decisiones abiertas en este diseño.
