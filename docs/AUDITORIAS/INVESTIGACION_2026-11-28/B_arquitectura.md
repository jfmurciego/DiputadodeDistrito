# T-509 · Ámbito B · Arquitectura real del proceso e implementación

Fecha: 2026-11-28. Solo lectura. Medidas hechas con la API de GitHub (runs y jobs) y con el árbol de `main` en `9e630d11d`.
Datos para la máquina: `B_arquitectura.json` (10 hallazgos, B-1 a B-10).
Verificado el 28-11 por un revisor independiente contra `origin/main` `548968c47`: B-1 a B-9 reproducidos y corregidos (campo `verificacion`
del JSON; resumen en el §9); B-10 sin revisar. Este texto ya lleva las correcciones.

## 1. Veredicto

1. La tubería **funciona y es fiable en lote**: 95 de los 100 últimos runs manuales de la ejecución completa acabaron en éxito.
2. Pero **el motor ocupa el 2 % del tiempo**. En un run «Generar» de una provincia, 0,9 min son cálculo y 44,6 min son pasos de job. En Andalucía sube al 9 % (6,7 de 75,7 min).
3. El 57 % se va en **montar la imagen Docker 15 veces** por run; otro 12 %, en 31 `checkout`.
4. M01-M03 y las unidades internas **se ejecutan dos veces** en cada run (13 min de mediana). En P00 ya está decidido quitarlo (T-379); la 00 se retira tras el 29-11.
5. De punta a punta, un territorio tarda **unos 90 min de reloj** (territorial 64 + electoral encadenada 25), con 18 y unos 11 min de cola.
6. **El orquestador es GitHub Actions**: 11.193 líneas de YAML, el 48 % shell o Python embebido. Fuera de Actions solo corren M01-M08.
7. **La base de datos es la rama `main`**: 1.605 commits en las 36 h de la última campaña, unos 22 por territorio.
8. Los productos se localizan por **número de run y nombre**, no por contenido; reutilizar es una búsqueda lineal en los últimos 100 runs.
9. Qué recalcular lo decide **un modo elegido a mano** y reglas en prosa, con huellas parciales (M04-M06 con huella y test desde T-51; M01-M03 sin huella de código).
10. **Liga de hoy**: primera en evidencia y trazabilidad; regional en ingeniería de pipelines. No hay runs productivos desde el 16-11.

## 2. La arquitectura real (leída del código)

| Etapa | Código | Consume | Produce | Dónde queda |
|---|---|---|---|---|
| Planificar | 514 líneas dentro de la 00 | catálogo (`configuracion/catalogo_preparacion.yaml`, 206 KB, en `main`) | plan del run | salidas del job |
| 01 Fuentes (P10) | `p10-fuentes.yml`, 1.336 líneas | fuentes oficiales, espejos en R2 | paquete de fuentes | artefacto + commit en `main` |
| Acreditar pre-M04 | P20, primera llamada | paquete de fuentes | M01-M03, unidades, evidencia | artefactos de 14 días + commit |
| 02 Distritos (P20) | P20, segunda llamada; `modulos/01`-`06`, `ddd_core`, `ddd_motor2` | paquete de fuentes | M01…M06, competición, auditoría | `ddd-state-<run>-M0x` (14 días), M06 a R2, commit |
| Activación del par | `preparacion-legislatura-vigente.yml`, lanzada por API | M06, fuente electoral | par preparado | commit en `main` |
| 03-04 Electoral (P10, P30) | `modulos/07` (1.686 líneas) y `08`, en otra 00 lanzada por el bot | M06 + par | M07, M08 | artefacto (30-90 días), R2, commit |
| Estado operativo | `generar_estado_operativo.py` | todo lo anterior en `main` | README, `estado_operativo.json` (437 KB), `status.json` | commit en `main` con hasta 20 reintentos |
| Manifiesto | `registrar_en_main.py` | resultados de los jobs | manifiesto + catálogo de procedencia | commit en `main` |
| 05 Publicar (P40) | `p40-publicacion.yml` | M08 por blob de git | visor | Pages, R2, `publicaciones_visor.json` (510 KB) |

Tamaños: `modulos/` 3.959 líneas (M07 son 1.686); `ddd_core/` 16.785; `ddd_motor2/` 2.257; `herramientas/` 72.617 en 269 ficheros;
`tests/` 91.139 en 523; workflows 11.193 en 15 ficheros; `g10/` 263 (sin uso vivo).

Estado en `orchestracion/`: índice de R2 (`archivo_r2.json`, 1.459 entradas, 926 KB), fuentes en R2 (274 KB), registro del visor (510 KB),
estado operativo (437 KB), catálogo de procedencia (502 KB) y restos de g10 (tres JSON de septiembre).

Se recalcula sin necesidad: la imagen en cada job; M01-M03 y unidades (dos veces); planificación y cuatro puertas en la 00 hija;
README y estado operativo completos en cada run; M04 y M05 de la ruta retirada, que siguen corriendo como candidato (por decisión D-82).

## 3. Medidas

**Últimos 100 runs de la ejecución completa.** Sin filtro, los 100 son humo de `pull_request` (100 % éxito, 1,3 min).
Los 100 últimos manuales (15-11 21:01Z a 16-11 08:23Z, 11,4 h):

| Grupo | Runs | Éxito | Mediana | p90 | Máx. |
|---|---|---|---|---|---|
| Todos | 100 | 95 | 45,9 min | 110 min | 147 min |
| «Generar», lanzados por el propietario | 49 | 47 | 67,5 min | | 147 min |
| «Reutilizar», lanzados por el bot | 51 | 48 | 25,1 min | | 58 min |

Fallos: Málaga (2, «Generar»), Gerona, Asturias y Santa Cruz de Tenerife («Reutilizar» del bot). Total histórico: 1.012 runs manuales.

**Dónde se va el tiempo** (pasos de la API de jobs; 10 runs «Generar» en éxito y 6 «Reutilizar» en éxito; la columna «Reutilizar» es la muestra
del verificador, porque la original daba 42,9 min de reloj y 32,2 de cola y no era representativa de los 51 runs del bot):

| Medianas | «Generar» | «Reutilizar» |
|---|---|---|
| Reloj | 63,6 min | 24,8 min |
| Suma de pasos (los jobs suman 46,1 y 11,3) | 44,6 min | 10,8 min |
| Cola entre jobs | 17,8 min | 11,3 min (1,5-38) |
| Jobs (con Docker) | 31 (15) | 13 (1) |
| Entorno (Docker, pip) | 25,8 min · 57 % | 5,1 min · 47 % |
| Checkout | 5,5 min · 12 % | 2,2 min · 20 % |
| **Motor** (módulos y competición) | **0,9 min · 2,0 %** (1,4-3,8 %) | sin clasificar |
| Primera pasada duplicada | 13,2 min | 0 |
| Espera del encadenado | 4,3 min (máx. 34) | 0 |
| Estado operativo | 0,9 min (máx. 3,9) | 0,8 min (máx. 8,8 en 43763327156) |

Método: suma de `completed_at − started_at` por paso, clasificado por nombre («entorno», «buildx», «runtime», `pip`; `checkout`;
«Ejecutar módulo», «competición», «rehacer M06»). Comprobado en el log del M04 de Orense: capas en caché, 53 s de exportar
la imagen, unos 4 s de módulo en un job de 103 s. Territorio grande de contraste (verificación): Andalucía, run 43728682179,
75,7 min de pasos, 6,7 de motor (8,9 %) y 33,0 de entorno (44 %).

## 4. Estado objetivo: referente mundial

- **Un comando por territorio**, igual en un portátil que en CI. Así trabaja ALARM con sus simulaciones de los 50 estados: tres guiones
  por estado y resultados depositados con DOI (McCartan et al., *Scientific Data*, 2022).
- **Grafo declarativo de etapas**: cada etapa declara entradas, salidas y el código que la define, como las reglas de Snakemake
  (Mölder et al., 2021) o los procesos de Nextflow (Di Tommaso et al., 2017).
- **Artefactos direccionados por contenido**: la salida de una etapa se guarda por su sha256 y se busca por la huella de sus
  entradas, como en Bazel o DVC. Relanzar sin cambios no ejecuta nada.
- **Estado fuera de `main`**: git guarda código y un manifiesto por campaña; los datos, en el almacén de objetos.
- **Medida en cada campaña**: éxito a la primera, minutos por territorio y porcentaje de tiempo de motor.

Con eso, la campaña de 71 pasaría de unos 5.100 min de runner (medidos en el diseño de P00) a una cifra del orden de 1.000 (estimación mía, no medida).

## 5. Hallazgos (impacto tras la verificación)

### B-1 · En provincias el motor ocupa el 2 % de un run (9 % en Andalucía); más de la mitad es montar la imagen 15 veces (impacto 5, esfuerzo M)
- **Hoy**: cada etapa es un job en un runner nuevo: `checkout`, imagen, bajar estado, 2-5 s de módulo, subir estado. La caché de la
  imagen tiene ámbito por commit (`scope=ddd-production-${{ github.sha }}`) y `main` cambia en cada run (88 sha en 100 runs).
- **Por qué importa**: mil ejecuciones son 750 h de runner para 15 h de cálculo. Es también la causa de la cola.
- **Propongo**: (a) un solo job para M01→M06 (`procedimiento.sh` ya acepta tramo) guardando el checkpoint de cada etapa desde dentro;
  (b) imagen construida una vez por huella de `Dockerfile` y `.lock`, usada por digest.
- **Criterio**: en 10 runs «Generar» de provincias, mediana ≤ 12 min de jobs en el tramo P20 (hoy 35,0; fuera de P20 quedan 9-13 min que
  esto no toca) y entorno ≤ 25 %; misma composición sección→distrito (sha256 de su CSV) en 3 territorios. El sha256 del ZIP M06 no vale:
  no se repite entre runs.
- **No previsto**, pero la parte (a) reabre D-143: el propietario eligió la cadena A (varios jobs por territorio) y dejó «un job por
  territorio» como respaldo C. El diseño de P00 (§12) cuenta estos minutos como «trabajo real» y no los desglosa.

### B-2 · El grafo de etapas vive en YAML, no en un ejecutor propio (impacto 5, esfuerzo XL)
- **Hoy**: 15 workflows, 11.193 líneas, 5.346 dentro de `run:`. Puertas, selección de checkpoint, registro y encadenado solo existen en Actions.
- **Por qué importa**: cada cambio de flujo se prueba con runs reales y un tercero no puede repetir una ejecución completa.
- **Propongo**: fichero declarativo de etapas y un ejecutor único; Actions como lanzador fino (matriz + un job por territorio).
- **Criterio**: en un contenedor limpio, un comando produce el M06 de Orense con la misma composición que CI y el M08 con los mismos
  ganadores; workflows ≤ 3.000 líneas, < 10 % en `run:`. También reabre D-143 (un job por territorio).

### B-3 · Productos identificados por run y nombre: reanudar es una búsqueda lineal en 100 runs (impacto 3, antes 4; esfuerzo L)
- **Hoy**: al reanudar, P20 recorre los últimos 100 runs manuales del repositorio (sin paginar) bajando ZIP; en campaña esa ventana son
  11 h. El catálogo cita 148 `run_id` y ninguna clave de R2. 54 retenciones con 5 valores. El índice de R2 tiene 1.459 entradas y
  1.033 sha: las 426 repetidas son la copia al árbol nuevo `interno/estados/…/{ultimo,publicado}/` (T-443, D-198), no copias entre runs;
  P20 todavía no lee ese árbol.
- **Propongo**: que el selector de P20 reanude por clave directa en ese árbol (`…/<territorio>/ultimo/`), validando con la huella de
  entradas; primero en sombra. Un `cas/<sha256>` no aporta hoy (ningún sha se repite entre runs) y choca con D-188.
- **Criterio**: relanzar sin cambios ejecuta 0 etapas de P20 con ≤ 5 min de jobs; acierta con más de 100 runs posteriores y con el
  artefacto caducado; P20 deja de llamar a `actions/runs?…per_page=100` para elegir checkpoint.

### B-4 · Qué recalcular lo decide un modo manual y huellas parciales (impacto 3, antes 4; esfuerzo L)
- **Hoy**: tres modos en el botón; huella por capas para M04-M06 (motor, contrato y política; T-51, con test), ninguna de código para
  M01-M03. La línea 46 de `CLAUDE.md` («reutiliza M04 aunque cambie el contrato») está anticuada: el selector lo rechaza.
- **Propongo**: una función de huella para las 8 etapas (código, contrato, política, entradas, imagen) y quitar el modo del botón.
- **Criterio**: tests de invalidación (un byte en `modulos/02` invalida M02 en adelante y no M01; cambiar el suelo invalida M04 en adelante).

### B-5 · `main` como base de datos: 1.605 commits en 36 h (impacto 4, esfuerzo L)
- **Hoy**: 9.515 commits, 4.454 desde el 1-11, repositorio de 467 MB; fusión de JSON propia con reintentos; el estado operativo llegó a 8,8 min.
- **Propongo**: registros por run en R2 (previsto en T-379), **estado derivado sin versionar** (no previsto) y un commit por campaña.
- **Criterio**: campaña de 71 con ≤ 2 commits de robot en `main` y ningún `PUSH_RECHAZADO`.

### B-6 · M01-M03 y unidades, dos veces por run (impacto 3, antes 4; esfuerzo S)
- **Hoy**: «Acreditar habilitación» y «02 Generar» llaman las dos a P20; 13,2 min de mediana, cerca del 30 % del run.
- **Propongo**: nada nuevo para P00 (decisión B de T-379: una sola llamada). En la 00, que se retira tras el 29-11, solo si esa retirada
  se retrasa: la segunda llamada empezaría en M04 con el estado de la primera.
- **Criterio**: un único job de cada etapa M01-M03 por territorio (API de jobs), M04 no arranca sin la evidencia pre-M04 y la composición
  no cambia en 3 territorios.

### B-7 · Encadenado por bot (impacto 3, previsto en T-379)
- **Hoy**: un job espera con `sleep 30` (mediana 4,3 min, máx. 34) y lanza otra 00 que repite planificación y puertas (25 min de reloj de
  mediana); 51 de 100 runs son del bot.
- **Aporto**: línea base para el criterio de T-379: ningún run del bot, una ejecución por campaña, reloj ≤ 30 min por territorio (hoy unos 90).

### B-8 · El Gestor no lanza desde el 9-11 (impacto 2, antes 3; esfuerzo M)
- **Hoy**: 22 runs en su historia, 13 en éxito; tres herramientas de gestor (1.857 líneas) y tres modos; P00 será la cuarta vía.
- **Propongo**: la retirada del Gestor ya está en la PR 5 de T-379; falta incluir en ella las tres herramientas `gestor_campa*.py` y un test.
  **Criterio**: tras la primera campaña con P00, cero ficheros `gestor`.

### B-9 · La medida de la tubería no está viva (impacto 3, esfuerzo S)
- **Hoy**: `metricas_proceso.json` es del 9-11 (13 territorios) aunque hay un job semanal `metricas` en P90 (T-366) que debería
  regenerarlo; el humo de PR tapa la tasa real; nadie mide el porcentaje de motor.
- **Propongo**: arreglar ese job y añadir a `herramientas/metricas_proceso.py` el porcentaje de motor (los otros dos indicadores ya los
  calcula). **Criterio**: tras la próxima campaña el fichero tiene fecha posterior y los tres valores por territorio; relanzar da lo mismo.

### B-10 · Capas retiradas en el árbol activo (impacto 2, esfuerzo M)
- **Hoy**: `g10/` sin workflow; cuatro motores de semillas encadenados; 68 herramientas citadas solo por tests y 27 por nadie (17.015 líneas).
- **Propongo**: una PR de retirada por capa, empezando por lo que nadie cita. **Criterio**: el guion de referencias da 0 sin cita y la CI sigue en verde.

## 6. Camino en tres pasos, pequeños y reversibles

**Esta semana (sin tocar el motor)**
1. Medida fija (B-9): arreglar el job semanal y añadir el porcentaje de motor, con la muestra de hoy como línea base. Prueba: mismo resultado al relanzar.
2. Doble pasada (B-6): ya decidida en P00 (T-379). En la 00 solo si su retirada se retrasa. Prueba: un job por etapa y misma composición en 3 territorios.
3. Un job para M01→M06 detrás de una opción interna, sin retirar la ruta de 15 jobs (B-1a; reabre D-143). Prueba: misma composición y ≤ 12 min de jobs en el tramo P20.

**Este mes**
4. Imagen por digest (B-1b). Prueba: paso de entorno < 60 s por job.
5. Huella genérica y reanudación por clave directa en R2 **en sombra** (B-3, B-4). Prueba: 0 discrepancias sin explicar en una campaña.
6. Cerrar T-379 con la línea base de B-7 y sacar el estado derivado de `main` (B-5). Prueba: ≤ 2 commits de robot por campaña.

**Este trimestre**
7. Ejecutor único con grafo declarativo (B-2), etapa a etapa. Prueba: un comando en contenedor limpio repite la composición de CI.
8. Retirar la 00, el Gestor, el encadenador y los selectores (B-8, B-10). Prueba: workflows ≤ 3.000 líneas y un solo botón.

## 7. Lo que no pude comprobar

- **Territorios grandes**: la muestra son provincias del Congreso. La verificación midió Andalucía (8,9 % de motor); Madrid y el resto
  de autonómicas siguen sin medir.
- **Runs posteriores al 16-11**: no hay. Los ficheros de P10-P30 cambiaron de nombre el 16/17-11; leí que el paso de la imagen sigue igual
  en `p20-distritos.yml`, pero no hay run que lo mida.
- **«Reutilizar» con contrato cambiado**: resuelto en la verificación. Manda T-51 (`tests/test_huella_checkpoint_motor.py`); la línea 46
  de `CLAUDE.md` está anticuada.
- **Reparto de los 1.605 commits** entre robots y personas: la API no filtró por autor de bot. En el clon local, del 16-11 en adelante,
  hay 173 commits de PR sobre 486.
- **Herramientas sin uso**: búsqueda por nombre; no ve llamadas dinámicas ni usos desde documentos.
- **Ahorro estimado** (de 5.100 a unos 1.000 min por campaña): es una cuenta, no una medida.
- **Fuentes externas**: citadas de memoria, sin reabrir esta noche por presupuesto. Conviene verificar los DOI antes de publicarlos.
- No lancé tests ni motor.

## 8. Objeciones (D-216)

1. **El diseño de P00 optimiza el reparto de una sobrecarga que no debería existir.** Dimensiona 15 cadenas en paralelo para 3.600-4.500 min
   de «trabajo real» que, medido por pasos, es un 2 % de motor en provincias (9 % en Andalucía). Antes de fijar ese diseño convendría quitar la sobrecarga (B-1, B-6).
2. **La noche del 29-11 irá con la 00 actual** (D-145 C): unos 5.000 min de runner para regenerar 71 territorios, cuando B-6 es de talla S.
   (Verificación: tocar la CI de producción la víspera no es realista y P00 ya lo resuelve; B-6 queda en impacto 3.)
3. **Renombrar M01-M08 a P21-P32 (T-313) antes del grafo declarativo** invalida huellas y checkpoints por un cambio de nombres. Con el
   grafo, los nombres visibles serían un dato y no nombres de fichero.
4. **Cabecera de versión y copia en `legacy/` por cada cambio** (418 copias solo de workflows) encarece justo las simplificaciones que
   este informe propone. Sugiero eximir de la copia a los ficheros que se retiran.

## 9. Verificación independiente (28-11)

Reproducido con comandos propios (API de jobs y de runs, `wc`, `grep`, lectura de las líneas citadas) contra `origin/main` `548968c47`.
No hay cambios en los workflows desde el commit que usó el informe.

| Hallazgo | Veredicto | Impacto | Qué cambió |
|---|---|---|---|
| B-1 | CORREGIDO | 5 | Cifras confirmadas; acotado a provincias (Andalucía 9 %); criterio medido en el tramo P20; reabre D-143 |
| B-2 | CORREGIDO | 5 | Cifras confirmadas; criterio por composición, no por sha256 del ZIP; reabre D-143 |
| B-3 | CORREGIDO | 4 → 3 | Las 426 «repetidas» son la copia al árbol nuevo de R2; propuesta sin `cas/`; choca con D-188 |
| B-4 | CORREGIDO | 4 → 3 | Manda T-51, con test; `CLAUDE.md` línea 46 anticuada |
| B-5 | CORREGIDO | 4 | Commits confirmados; tamaños unificados; «1.500 de robot» no está medido |
| B-6 | CORREGIDO | 4 → 3 | Duplicado confirmado; ya decidido en P00 y la 00 se retira |
| B-7 | CORREGIDO | 3 | La 00 hija tarda 25 min, no 43; punta a punta 90, no 105 |
| B-8 | CORREGIDO | 3 → 2 | La retirada ya está en la PR 5 de T-379; quedan las tres herramientas |
| B-9 | CORREGIDO | 3 | Existe un job semanal de métricas (T-366) que no actualiza desde el 9-11 |
| B-10 | sin revisar | 2 | Fuera del alcance (impactos 5, 4 y 3) |

## 10. Descartados en la verificación

Ningún hallazgo se descarta entero. Se retiran estas afirmaciones:

- **«El mismo contenido se guarda varias veces en R2» (B-3)**: las 426 entradas repetidas son el mismo run y artefacto copiado al árbol
  nuevo `interno/estados/` el 23-11 (D-198); el árbol viejo se borra tras el 29-11 (D-188). Entre runs distintos ningún sha se repite.
- **Almacén `cas/<sha256>` (B-3)**: sin salidas reproducibles byte a byte no ahorra nada y contradice D-188 (nombres claros, sin códigos).
- **«La 00 hija tarda 42,9 min con 32,2 de cola» y «105 min de punta a punta» (B-7)**: la mediana de los 51 runs del bot es 25,1 min.
- **«No se sabe si manda `CLAUDE.md` o T-51» (B-4)**: manda T-51; hay test.
- **«Mismo sha256 del M06» como criterio (B-1, B-2, B-3, B-6)**: en `archivo_r2.json`, 67 territorios tienen más de un run y ninguno
  repite el sha del ZIP. Se sustituye por la composición sección→distrito.
- **«≤ 12 min de jobs por run» (B-1)**: fuera del tramo P20 ya hay 9-13 min. El umbral se aplica al tramo P20.
- **«Sin medida» (B-9)**: hay job y herramienta; lo que falta es que escriban y el porcentaje de motor.

