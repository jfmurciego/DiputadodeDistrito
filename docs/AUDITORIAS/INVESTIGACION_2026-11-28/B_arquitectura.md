# T-509 · Ámbito B · Arquitectura real del proceso e implementación

Fecha: 2026-11-28. Solo lectura. Medidas hechas con la API de GitHub (runs y jobs) y con el árbol de `main` en `9e630d11d`.
Datos para la máquina: `B_arquitectura.json` (10 hallazgos, B-1 a B-10).

## 1. Veredicto

1. La tubería **funciona y es fiable en lote**: 95 de los 100 últimos runs manuales de la ejecución completa acabaron en éxito.
2. Pero **el motor ocupa el 2 % del tiempo**. En un run «Generar» de una provincia, 0,9 min son cálculo y 44,6 min son jobs.
3. El 57 % se va en **montar la imagen Docker 15 veces** por run; otro 12 %, en 31 `checkout`.
4. M01-M03 y las unidades internas **se ejecutan dos veces** en cada run (13 min de mediana).
5. De punta a punta, un territorio tarda **unos 105 min de reloj** (territorial 64 + electoral encadenada 43), con 18 y 32 min de cola.
6. **El orquestador es GitHub Actions**: 11.193 líneas de YAML, el 48 % shell o Python embebido. Fuera de Actions solo corren M01-M08.
7. **La base de datos es la rama `main`**: 1.605 commits en las 36 h de la última campaña, unos 22 por territorio.
8. Los productos se localizan por **número de run y nombre**, no por contenido; reutilizar es una búsqueda lineal en los últimos 100 runs.
9. Qué recalcular lo decide **un modo elegido a mano** y reglas en prosa, con huellas parciales.
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
| «Reutilizar», lanzados por el bot | 51 | 48 | 24,8 min | | 58 min |

Fallos: Málaga (2, «Generar»), Gerona, Asturias y Santa Cruz de Tenerife («Reutilizar» del bot). Total histórico: 1.012 runs manuales.

**Dónde se va el tiempo** (pasos de la API de jobs; 10 runs «Generar» y 6 «Reutilizar» elegidos al azar entre los de éxito):

| Medianas | «Generar» | «Reutilizar» |
|---|---|---|
| Reloj | 63,6 min | 42,9 min |
| Suma de jobs | 44,6 min | 11,1 min |
| Cola entre jobs | 17,8 min | 32,2 min |
| Jobs (con Docker) | 31 (15) | 13 (1) |
| Entorno (Docker, pip) | 25,8 min · 57 % | 4,9 min · 43 % |
| Checkout | 5,5 min · 12 % | 2,2 min · 19 % |
| **Motor** (módulos y competición) | **0,9 min · 2,0 %** (1,4-3,8 %) | sin clasificar |
| Primera pasada duplicada | 13,2 min | 0 |
| Espera del encadenado | 4,3 min (máx. 34) | 0 |
| Estado operativo | 0,9 min (máx. 3,9) | 1,5 min (máx. 8,8) |

Método: suma de `completed_at − started_at` por paso, clasificado por nombre («entorno», «buildx», «runtime», `pip`; `checkout`;
«Ejecutar módulo», «competición», «rehacer M06»). Comprobado en el log del M04 de Orense: capas en caché, 53 s de exportar
la imagen, unos 4 s de módulo en un job de 103 s.

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

## 5. Hallazgos, de mayor a menor impacto

### B-1 · El motor ocupa el 2 % de un run; el 57 % es montar la imagen 15 veces (impacto 5, esfuerzo M)
- **Hoy**: cada etapa es un job en un runner nuevo: `checkout`, imagen, bajar estado, 2-5 s de módulo, subir estado. La caché de la
  imagen tiene ámbito por commit (`scope=ddd-production-${{ github.sha }}`) y `main` cambia en cada run (88 sha en 100 runs).
- **Por qué importa**: mil ejecuciones son 750 h de runner para 15 h de cálculo. Es también la causa de la cola.
- **Propongo**: (a) un solo job para M01→M06 (`procedimiento.sh` ya acepta tramo) guardando el checkpoint de cada etapa desde dentro;
  (b) imagen construida una vez por huella de `Dockerfile` y `.lock`, usada por digest.
- **Criterio**: 10 runs «Generar» de provincias con mediana ≤ 12 min de jobs y entorno ≤ 25 %; M06 con el mismo sha256 en 3 territorios.
- **No previsto**: el diseño de P00 (§12) cuenta estos minutos como «trabajo real».

### B-2 · El grafo de etapas vive en YAML, no en un ejecutor propio (impacto 5, esfuerzo XL)
- **Hoy**: 15 workflows, 11.193 líneas, 5.346 dentro de `run:`. Puertas, selección de checkpoint, registro y encadenado solo existen en Actions.
- **Por qué importa**: cada cambio de flujo se prueba con runs reales y un tercero no puede repetir una ejecución completa.
- **Propongo**: fichero declarativo de etapas y un ejecutor único; Actions como lanzador fino (matriz + un job por territorio).
- **Criterio**: en un contenedor limpio, un comando produce M06 y M08 de Orense con el sha256 de CI; workflows ≤ 3.000 líneas, < 10 % en `run:`.

### B-3 · Productos identificados por run y nombre, no por contenido (impacto 4, esfuerzo L)
- **Hoy**: al reanudar, P20 recorre los últimos 100 runs manuales del repositorio (sin paginar) bajando ZIP; en campaña esa ventana son
  11 h. El catálogo cita 148 `run_id` y ninguna clave de R2. R2 tiene 1.459 entradas y 1.033 sha distintos. 54 retenciones con 5 valores.
- **Propongo**: almacén por contenido en R2 (`cas/<sha256>`) e índice huella de entradas → sha de salida; primero en sombra.
- **Criterio**: relanzar sin cambios ejecuta 0 etapas en < 5 min; acierta con más de 100 runs posteriores y con el artefacto caducado.

### B-4 · Qué recalcular lo decide un modo manual y huellas parciales (impacto 4, esfuerzo L)
- **Hoy**: tres modos en el botón; huellas a mano para M04-M06, ninguna de código para M01-M03; `CLAUDE.md` y el selector (T-51) no dicen
  lo mismo sobre reutilizar con el contrato cambiado.
- **Propongo**: una función de huella para las 8 etapas (código, contrato, política, entradas, imagen) y quitar el modo del botón.
- **Criterio**: tests de invalidación (un byte en `modulos/02` invalida M02 en adelante y no M01; cambiar el suelo invalida M04 en adelante).

### B-5 · `main` como base de datos: 1.605 commits en 36 h (impacto 4, esfuerzo L)
- **Hoy**: 9.515 commits, 4.454 desde el 1-11, repositorio de 467 MB; fusión de JSON propia con reintentos; el estado operativo llegó a 8,8 min.
- **Propongo**: registros por run en R2 (previsto en T-379), **estado derivado sin versionar** (no previsto) y un commit por campaña.
- **Criterio**: campaña de 71 con ≤ 2 commits de robot en `main` y ningún `PUSH_RECHAZADO`.

### B-6 · M01-M03 y unidades, dos veces por run (impacto 4, esfuerzo S)
- **Hoy**: «Acreditar habilitación» y «02 Generar» llaman las dos a P20; 13,2 min de mediana, cerca del 30 % del run.
- **Propongo**: que la segunda llamada empiece en M04 con el estado de la primera. T-379 lo resuelve solo en la ruta de campaña.
- **Criterio**: un único job de cada etapa M01-M03 por run y mismo sha256 del M06.

### B-7 · Encadenado por bot (impacto 3, previsto en T-379)
- **Hoy**: un job espera con `sleep 30` (mediana 4,3 min, máx. 34) y lanza otra 00 que repite planificación y puertas; 51 de 100 runs son del bot.
- **Aporto**: línea base para el criterio de T-379: ningún run del bot, una ejecución por campaña, reloj ≤ 30 min por territorio.

### B-8 · El Gestor no lanza desde el 9-11 (impacto 3, esfuerzo M)
- **Hoy**: 22 runs en su historia, 13 en éxito; tres herramientas de gestor (1.857 líneas) y tres modos; P00 será la cuarta vía.
- **Propongo**: fecha de retirada en la PR que estrene P00, con test. **Criterio**: tras la primera campaña con P00, cero ficheros `gestor`.

### B-9 · Sin medida viva de la tubería (impacto 3, esfuerzo S)
- **Hoy**: `metricas_proceso.json` es del 9-11 (13 territorios); el humo de PR tapa la tasa real; nadie mide el porcentaje de motor.
- **Propongo**: tres indicadores al cierre de cada campaña. **Criterio**: fichero generado solo, reproducible con la API.

### B-10 · Capas retiradas en el árbol activo (impacto 2, esfuerzo M)
- **Hoy**: `g10/` sin workflow; cuatro motores de semillas encadenados; 68 herramientas citadas solo por tests y 27 por nadie (17.015 líneas).
- **Propongo**: una PR de retirada por capa, empezando por lo que nadie cita. **Criterio**: el guion de referencias da 0 sin cita y la CI sigue en verde.

## 6. Camino en tres pasos, pequeños y reversibles

**Esta semana (sin tocar el motor)**
1. Medida fija (B-9): los tres indicadores con la muestra de hoy como línea base. Prueba: mismo resultado al relanzar.
2. Quitar la doble pasada (B-6). Prueba: un job por etapa y sha256 igual en 3 territorios. Se revierte con un `revert`.
3. Un job para M01→M06 detrás de una opción interna, sin retirar la ruta de 15 jobs (B-1a). Prueba: sha256 igual y ≤ 12 min de jobs.

**Este mes**
4. Imagen por digest (B-1b). Prueba: paso de entorno < 60 s por job.
5. Huella genérica y almacén por contenido **en sombra** (B-3, B-4). Prueba: 0 discrepancias sin explicar en una campaña. Se borra el prefijo y no queda rastro.
6. Cerrar T-379 con la línea base de B-7 y sacar el estado derivado de `main` (B-5). Prueba: ≤ 2 commits de robot por campaña.

**Este trimestre**
7. Ejecutor único con grafo declarativo (B-2), etapa a etapa. Prueba: un comando en contenedor limpio repite el sha256 de CI.
8. Retirar la 00, el Gestor, el encadenador y los selectores (B-8, B-10). Prueba: workflows ≤ 3.000 líneas y un solo botón.

## 7. Lo que no pude comprobar

- **Territorios grandes**: la muestra son provincias del Congreso. En Madrid o Andalucía el motor pesará más que el 2 %; se comprueba
  con el mismo método sobre runs autonómicos.
- **Runs posteriores al 16-11**: no hay. Los ficheros de P10-P30 cambiaron de nombre el 16/17-11; leí que el paso de la imagen sigue igual
  en `p20-distritos.yml`, pero no hay run que lo mida.
- **«Reutilizar» con contrato cambiado**: no ejecuté el selector; no sé si manda `CLAUDE.md` o T-51. Se comprueba con un test del selector.
- **Reparto de los 1.605 commits** entre robots y personas: la API no filtró por autor de bot. En el clon local, del 16-11 en adelante,
  hay 173 commits de PR sobre 486.
- **Herramientas sin uso**: búsqueda por nombre; no ve llamadas dinámicas ni usos desde documentos.
- **Ahorro estimado** (de 5.100 a unos 1.000 min por campaña): es una cuenta, no una medida.
- **Fuentes externas**: citadas de memoria, sin reabrir esta noche por presupuesto. Conviene verificar los DOI antes de publicarlos.
- No lancé tests ni motor.

## 8. Objeciones (D-216)

1. **El diseño de P00 optimiza el reparto de una sobrecarga que no debería existir.** Dimensiona 15 cadenas en paralelo para 3.600-4.500 min
   de «trabajo real» que, medido por pasos, es un 2 % de motor. Antes de fijar ese diseño convendría quitar la sobrecarga (B-1, B-6).
2. **La noche del 29-11 irá con la 00 actual** (D-145 C): unos 5.000 min de runner para regenerar 71 territorios, cuando B-6 es de talla S.
3. **Renombrar M01-M08 a P21-P32 (T-313) antes del grafo declarativo** invalida huellas y checkpoints por un cambio de nombres. Con el
   grafo, los nombres visibles serían un dato y no nombres de fichero.
4. **Cabecera de versión y copia en `legacy/` por cada cambio** (418 copias solo de workflows) encarece justo las simplificaciones que
   este informe propone. Sugiero eximir de la copia a los ficheros que se retiran.
