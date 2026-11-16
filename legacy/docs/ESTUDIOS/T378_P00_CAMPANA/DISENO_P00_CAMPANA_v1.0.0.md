# T-378 · Diseño al detalle de P00 Campaña y de la nueva forma de trabajar

VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ANTERIOR: ninguna (fichero nuevo) · ESTADO: propuesta para aprobación del
propietario (D-140, paso 9a)

Solo documento: no cambia código, workflows ni datos, y no lanza nada. Base: `origin/main` 0aa5dd8 y el plan 1.0.55
(PR #848: D-129 a D-141). Límites de GitHub con cita y enlace en `ANEXO_A_LIMITES_GITHUB.md`. Las decisiones que
pido están al final (§11).

## 1. Qué cambia, en una frase

Hoy una campaña son cientos de ejecuciones sueltas que se lanzan unas a otras y escriben en `main` a cada paso. Con
P00, **una campaña es una sola ejecución**: comprueba antes de empezar, trabaja cada territorio a su ritmo, aparta
el que falla sin parar al resto, escribe en `main` una sola vez al final y deja el informe en un issue.

## 2. El botón (lo único visible)

| Campo | Opciones | Por defecto |
|---|---|---|
| Territorios | `todos` (71), `congreso` (52 provincias), `autonómicas` (19 comunidades) o lista de códigos: `nac22, aut11` | — (obligatorio) |
| Elección | `vigente` (la última de cada territorio) o `AAAA-MM` (p. ej. `2026-11` para el ensayo, `2019-11` para el histórico) | `vigente` |
| Modo | `solo comprobar` · `comprobar y lanzar` | `solo comprobar` |
| Publicar | `no` · `sí` | `no` |

No aparecen run ids, sha, rutas, motor, estrategia, «inicio», paralelismo ni «mapa 350» (D-130). Todo eso se
resuelve en el código: reutilizar es automático (D-136), el motor es Deslinde (D-139), el paralelismo es fijo (§7),
los `congreso350_*` se rechazan (D-76) y los ensembles no existen (D-138).

## 3. Una campaña = una ejecución

```
P00 Campaña (una ejecución, un solo número de versión del código)
│
├─ 1. Comprobación previa ──► semáforo por territorio (verde / ámbar / rojo) ──► issue de la campaña
│        └─ «solo comprobar» termina aquí
│
├─ 2. Cadena por territorio (en paralelo, cada uno a su ritmo; los rojos no entran)
│        P10 Fuentes ─► P20 Distritos ─► P30 Resultados electorales
│        (antes de cada paso: ¿hay parada sistémica? si la hay, no empieza el siguiente)
│
├─ 3. Cierre: un único registro en main (catálogo, estado operativo, manifiestos) ──► informe final en el issue
│
└─ 4. P40 Publicación (solo si «publicar = sí», sin parada sistémica, con los territorios que pasaron)

Después, fuera de la ejecución: una sola sesión de IA lee el informe (§6).
```

- P10, P20, P30 y P40 se llaman **por dentro** como workflows reutilizables (`workflow_call`). Ninguna llamada a la
  API para lanzar otras ejecuciones: desaparecen la «Activación» encadenada, la 00 «Reutilizar» del bot y los
  lanzamientos del Gestor y de «Elección».
- **Forma de la cadena (recomendada, A):** una matriz de territorios en la que cada fila llama a un reutilizable
  «cadena de un territorio» que hace P10 → P20 → P30. GitHub admite matriz que llama a reutilizable y hasta 10
  niveles de anidamiento (anexo A, filas 4 y 5); aquí hay 3 o 4. Cada territorio avanza solo: Andalucía no retrasa a
  Soria. El reutilizable de cadena es un fichero sin botón de la familia P00 (como la fusión automática, D-135).
- **B, sin fichero extra:** tres matrices seguidas (todos P10, luego todos P20, luego todos P30). Más simple, pero
  cada paso espera al territorio más lento y hay que filtrar en cada paso los apartados. Peor reloj.
- **C, respaldo (D-130):** un job por territorio con P10-P30 como pasos (acciones compuestas). 71 jobs, cabe de sobra
  en los límites, pero pierde el log separado por paso y obliga a que P10-P30 sean acciones, no workflows. Solo si A
  falla en la prueba (p. ej. un límite no documentado al anidar).
- **Resultados por territorio:** GitHub solo devuelve la salida de la *última* fila de una matriz (anexo A, fila 8),
  así que cada territorio deja su resultado en el estado de campaña (§5) y el cierre lo lee de ahí.

### Semáforo de la comprobación previa

| Color | Significa | Ejemplos (de causas ya conocidas) | Qué hace «comprobar y lanzar» |
|---|---|---|---|
| Verde | Todo listo y compatible | fuentes en R2 con su huella, contrato válido, resultados de esa elección disponibles | lo lanza |
| Ámbar | Se puede, pero regenerará algo | paquete de fuentes caducado (P10 lo rehace), puntos de control incompatibles (P20 empieza de cero) | lo lanza y lo marca |
| Rojo | No se puede | fuente sin espejo que rechaza la nube (Interior, Xunta), provincia `BLOQUEADA_SIN_DATO`, elección sin datos, código inexistente o `congreso350_*` | lo aparta desde el inicio |

Comprobaciones de campaña (si falla una, no se lanza nada): el código de la versión elegida tiene la CI en verde;
no hay otra campaña en curso; R2 responde; y se muestra el gasto de Actions de la semana (D-46). Las comprobaciones
degradan a aviso ante errores de red y bloquean solo con evidencia positiva (lección T-246).

## 4. Políticas: reintentos, apartado y parada sistémica

| Situación | Regla |
|---|---|
| Fallo transitorio (red cortada, error 5xx de GitHub o R2, cuota de descarga «código 75», push rechazado) | Hasta **2 reintentos** dentro del mismo paso, con espera de 1 y 5 minutos. GitHub no reintenta jobs solo: el reintento va en la herramienta. |
| Runner perdido o job cancelado por GitHub | No se reintenta solo (no hay forma dentro de la ejecución). El informe lo marca «transitorio sin reintento» y el Operador puede pulsar «Re-ejecutar jobs fallidos» **en la misma ejecución** (misma versión; GitHub admite 50, anexo A). |
| Fallo no transitorio (huella distinta, puerta en rojo, contrato, motor) | **Sin reintento.** El territorio queda **apartado** con su causa; los demás siguen. |
| Parada sistémica | Si hay **≥3 apartados con la misma causa** o los apartados son **≥20 % de los lanzados** (71 → 15), ningún territorio empieza un paso nuevo; los que están en uno lo terminan. No se publica. El issue lo avisa al momento. |

- «Misma causa» = el mismo código de causa que ya imprimen las herramientas (`ARTIFACT_MISSING`,
  `TERRITORIAL_READY_PAIR_INCOMPATIBLE`, `CANDIDATE_FAILED`…); sin código, cuenta como «causa desconocida».
- Sin vigilante: cada territorio consulta el recuento **antes** de empezar P10, P20, P30 (y el cierre antes de P40).
- Tras una parada, no se relanza: se informa (CLAUDE.md). Un relanzamiento es otra campaña con la lista de apartados.

## 5. Versión fija y estado fuera de `main`

**Versión fija.** GitHub ya ejecuta los reutilizables locales (`./.github/workflows/…`) desde el mismo commit que
el llamador (anexo A, fila 9). Falta que nada lea `main` a mitad de campaña: todo `checkout` usa la versión de la
ejecución, y el estado se lee de la campaña, no de la cabeza de `main`. Un sha por campaña, anotado en el issue.

**Qué escriben hoy los robots en `main` en cada territorio** (de `ejecucion-completa-proyecto.yml`,
`_reutilizable-generacion-territorial.yml`, `_reutilizable-incorporacion-electoral.yml`,
`preparacion-legislatura-vigente.yml`): manifiesto de la 00, estado operativo, catálogo de preparación y producto
territorial, manifiestos M06, par de fuentes, índices de R2 (`archivo_r2.json`, `datos/composicion`,
`datos/resultados`) y el catálogo de procedencia. Con 71 territorios son cientos de pushes: chocan (cupo ≤6 desde la
r4) y cancelan la CI de `main` en cada uno.

| Dónde | A favor | En contra | Uso propuesto |
|---|---|---|---|
| **R2** | Un objeto por territorio: no hay choques; ya tenemos credenciales y huellas sha256; lectura barata | No lo ve una persona; consistencia de lectura tras escritura sin comprobar desde la nube (la web de Cloudflare da 403) | **Estado de trabajo** de la campaña: semáforo, intentos, causas, resultado y productos de cada paso |
| **Rama dedicada** | Versionado y legible con git | Los pushes concurrentes chocan igual que en `main` (el problema es la concurrencia, no la rama); crece sin límite | Descartada |
| **Issue** | Lo ve el propietario y avisa al móvil (D-122) | Límite de la API (1.000/h con el token del workflow, 5.000 con la app; anexo A); editar el cuerpo a la vez pisa cambios | **Informe humano**: al empezar, si hay parada y al terminar; no es base de datos |
| **`main`** | Es lo que leen el visor, el dashboard y los tests | Choques y CI cancelada | **Un solo commit al cierre** con todo lo durable |

**Estado operativo y catálogo.** Durante la campaña no se tocan: el dashboard muestra el estado anterior y el estado
vivo está en el issue. Al cierre se regeneran una vez y van en un único commit (catálogo de procedencia incluido),
con la app de registro como hoy. Si la ejecución muere antes del cierre, lo hecho está en R2 y basta re-ejecutar el
job de cierre en la misma ejecución.

**P10-P40 sueltos** (botón propio) siguen escribiendo en `main` al terminar, como hoy. Dentro de P00 escriben en el
estado de campaña. El registro pasa a una acción compuesta con dos destinos; el resto del paso es idéntico.

## 6. Una sesión de IA, solo al cierre

| Hace | No hace |
|---|---|
| Se dispara una vez cuando P00 termina con apartados o parada (forense de P90, `workflow_run` de «P00 Campaña») | No vigila durante la campaña |
| Lee el issue y las anotaciones de los jobs fallidos; da la causa de cada apartado en ≤5 líneas con el catálogo de causas raíz | No reintenta, no lanza, no publica |
| Agrupa por causa y propone el siguiente paso (otra campaña con la lista de apartados, o una tarea de arreglo) | No edita código ni fusiona |
| Comenta en el issue de la campaña | Con todo en verde no se abre (ahorro) |

Hoy el forense se abre por cada 00 fallida (con 71 fallos serían 71 sesiones). Con P00 es una por campaña.

## 7. Límites de GitHub que mandan (verificados; detalle en el anexo A)

| Límite | Valor | Efecto en P00 |
|---|---|---|
| Jobs de una matriz por ejecución | 256 | 71 territorios caben. El histórico (5 elecciones × 52 = 260) no: **una elección por campaña** (ya lo exige el botón). |
| Jobs a la vez (plan Free) | 20 | Compartidos con la CI. Paralelo fijo: **10 territorios a la vez** (hoy ≤6 por los choques en `main`, que desaparecen). |
| Niveles de anidamiento / reutilizables distintos | 10 / 50 | P00 usa 3-4 niveles y unos 6 reutilizables. |
| Duración de un job / de una ejecución | 6 h / 35 días | El job más largo de la r4 duró 36 min. |
| Re-ejecuciones de una ejecución | 50 | Margen para re-ejecutar jobs fallidos. |
| Cola con `queue: max` por grupo | 100 | Los grupos únicos actuales (`ddd-prepared-source-pair`, `ddd-catalog-promotion`) pasan a ser por territorio. |

No verificado (no está en la documentación): un tope de jobs por ejecución distinto del de la matriz, y si los jobs
de los reutilizables llamados desde una matriz cuentan para los 256. Se comprueba en la validación (§9). El plan de
la cuenta (Free, 20 jobs) lo confirma el propietario.

## 8. Qué se absorbe y qué se retira

| Hoy | Qué hace | Dónde queda | Se retira |
|---|---|---|---|
| `gestor-campanas.yml` («P00 Campaña — Gestor») | Formulario de 13 campos; planifica (`legislatura_vigente.py`) y lanza una 00 por territorio por la API; histórico en 3 lotes por el tope de 256; modo «matriz» que llama a la 00 | Botón de P00 (4 campos); el plan → comprobación previa; la matriz → cadena por territorio; el histórico → campaña con `elección = AAAA-MM` | Fichero, lanzamientos por API, ensembles, mapa 350, «inicio», `max_paralelo`, «solo plan» (→ «solo comprobar») |
| `preparacion-legislatura-vigente.yml` («P00 Campaña — Legislatura») | Prepara el par fuentes territoriales + electorales y lo registra en `main` en una cola única; la 00 la lanza por la API si falta el par | P10 (P11 + P12) dentro de la cadena; el par va al estado de campaña y al commit de cierre | Fichero, cola única y lanzamiento desde la 00 |
| `activacion-por-eleccion.yml` («P00 Campaña — Elección») | Convierte una clave de elección en territorios (`clave_eleccion.py`) y lanza por la API una fase por territorio | La expansión elección → territorios, en la comprobación previa (la herramienta se reutiliza) | Fichero y lanzamientos |
| `ejecucion-completa-proyecto.yml` (la 00) | Todo el bloque por territorio; registra en `main` en cada paso; encadena legislatura y otra 00 «Reutilizar» | Sus jobs se reparten en P10/P20/P30/P40 (pasos 6-8) y en la cadena; manifiesto y estado → cierre | Fichero (en la PR de P00, D-129), `encadenar_par_y_04` y la 00 del bot |
| `_reutilizable-puerta-validacion.yml` | Puerta 01-04 | **Acción compuesta** «puerta de validación» (sin «Interno»), misma lógica y lectura R2 → Actions → release | Fichero |
| `forense-00.yml` (tras T-366, dentro de P90) | Forense por cada 00 fallida | Forense **por campaña** (§6); el disparador sigue siendo el nombre «P00 Campaña» | La versión por territorio |

También cambian: `legislatura_vigente.py` (`TITLE_00`) y `metricas_proceso.py` (`RUN_NAME`, que ya acepta
«P00 Campaña · …»); las skills `lanzar-00`, `lanzar-campana` y `operador` (una sola: lanzar P00) y las listas de
workflows de `test_design_a_catalogo`, `test_design_a_matriz_sintetica` y `test_codauto_preparation_contract`.

## 9. Plan de validación y respaldo

1. **Prueba de humo en la PR**: P00 se ejecuta una vez por el evento de la PR (solo sintaxis y comprobación previa
   sintética). Así queda disponible para lanzarla por la API desde la rama: GitHub solo muestra el botón con el
   fichero en `main`, pero permite lanzarlo desde otra rama si ya se ejecutó una vez (anexo A, fila 10).
2. **P00 de aut11** (Extremadura) desde la rama: «solo comprobar» y luego «comprobar y lanzar», publicar = no.
   Criterio: una sola ejecución, ningún lanzamiento por la API, producto M06 bit a bit igual al vigente, un único
   commit en `main` y el issue completo.
3. **Re-ensayo corto** con los tres territorios del ensayo (nac22, nac42, nac52), `elección = 2026-11`, publicar = no.
   Además: un fallo transitorio forzado (se reintenta) y uno no transitorio (se aparta y los otros dos siguen).
4. Ambas con frase del propietario al Operador (D-52) y antes del **26-11**.
5. **Respaldo (D-140):** si el **24-11** P00 no está validada, la noche del 29-11 va con la 00 actual (que ya llama a
   los P10-P40 nuevos) y P00 se fusiona después del 29-11.

Riesgo de calendario: T-379 va detrás de T-377 (P20) y P10, P20 y P30 no se fusionan hasta terminar el ensayo en
seco. Si eso no ocurre antes del ~21-11, el respaldo es lo probable.

## 10. Riesgos, descartes, PR y coste

**Riesgos**

| Riesgo | Mitigación |
|---|---|
| Un límite no documentado al anidar matriz → reutilizable → reutilizable | Se ve en la prueba de humo y en aut11; respaldo C (un job por territorio) |
| P10-P30 leen hoy de `main` (catálogo, par) a mitad de cadena | Entrada oculta «estado de campaña» en su `workflow_call`; test de flujo que falle si un paso lee `main` dentro de P00 |
| El cierre falla y `main` no recibe nada | Lo hecho queda en R2; re-ejecutar el job de cierre (misma ejecución) |
| Una campaña larga ocupa los 20 jobs y frena la CI de las PR | 10 territorios a la vez; la CI de PR se mantiene en cola |
| La IA de cierre no ve el log grande | Usa anotaciones y el log filtrado (como el forense de hoy) |

**Descartadas:** la rama dedicada para el estado (§5); vigilante que cancela la ejecución (CLAUDE.md: sin vigilantes);
reintentos automáticos de job por re-ejecución lanzada desde fuera (sería lanzar por la API); mantener el Gestor como
«lanzador» de P00 (contradice D-130); una ejecución por elección del histórico en lotes (el tope de 256 obliga a
partir: mejor una elección por campaña).

**PR de T-379 (estimación: 4, en este orden)**

| # | PR | Contenido |
|---|---|---|
| 1 | Estado de campaña | Herramienta de comprobación previa, semáforo, recuento de apartados/parada e informe; lectura/escritura en R2; tests (sin workflows) |
| 2 | Puerta como acción compuesta | Sustituye `_reutilizable-puerta-validacion.yml`; test de equivalencia |
| 3 | P00 Campaña | `p00-campana.yml` + cadena por territorio + cierre en un commit + issue; borra Gestor, Legislatura, Elección y la 00; tests y skills |
| 4 | IA de cierre | Forense por campaña en P90 |

**Coste de Actions por campaña de 71 territorios.** Medido en los ficheros de jobs de la API (suma del reloj de cada
job, como T-155) entre el 15-11 00:00 y el 16-11 12:00 UTC (r3/r4): 161 ejecuciones de la 00 (149 en éxito,
4.926 min) y 81 de «Legislatura» (219 min): **≈5.150 min, unos 72 min por territorio**, con fallos y con dos 00 por
territorio (la del Operador y la «Reutilizar» del bot). La mayor ejecución sumó 77 min. Con P00 se espera algo menos
(una cadena por territorio, sin la 00 duplicada ni la legislatura aparte, sin CI cancelada en `main`): **del orden de
4.000-5.000 min por campaña**, un tercio del tope semanal de 15.000 (T-155). Con 10 territorios a la vez, **8-9 h de
reloj**. La sesión de IA del cierre: una por campaña, Sonnet; su coste no consta aún en el repositorio.

## 11. Decisiones que pido al propietario

1. **Forma de la cadena:** A (matriz + reutilizable «cadena de un territorio», un fichero sin botón en la familia
   P00) — recomendada — o B (tres matrices seguidas, sin fichero extra).
2. **Estado fuera de `main`:** R2 para el trabajo, issue para el informe y un único commit en `main` al cierre (rama
   dedicada descartada).
3. **Grupos de territorios:** `todos`, `congreso`, `autonómicas` y lista de códigos. ¿Alguno más (p. ej. «una
   comunidad con sus provincias»)?
4. **Elección:** `vigente` por defecto y `AAAA-MM` para ensayo e histórico.
5. **Ámbar:** ¿se lanza y se marca (recomendado) o se aparta como el rojo?
6. **Parada sistémica en campañas pequeñas:** ¿mínimo de 3 apartados también para la regla del 20 %? (Si no, en una
   campaña de 3 territorios un solo fallo pararía al resto.)
7. **Publicar con apartados:** publicar los que pasaron (recomendado) o nada si hay algún apartado.
8. **Paralelo fijo de 10 territorios** y confirmación de que la cuenta es Free (20 jobs a la vez).
9. **IA de cierre** solo con apartados o parada (recomendado) o siempre.
10. **Validación desde la rama:** que la P00 de aut11 y el re-ensayo, lanzadas desde la rama de la PR, puedan escribir
    su commit de cierre en `main` (si no, validan todo menos ese commit).
