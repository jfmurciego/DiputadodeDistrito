# Reparador aislado: La Rioja y control histórico de Cantabria

Versión: 1.0.0. Nombre: diagnóstico exacto y regresión local M05.
Fecha: 2026-10-08. Alcance: desarrollo autonómico local. Estado: CI_PENDIENTE.
Cambios: nuevo arnés, fixture real y evidencia; ningún código productivo modificado.
Motivo: determinar si el reparador existente puede cerrar La Rioja.
Origen: encargo Work; documento nuevo sin predecesor.
Base: `72e4eac09f5b1599f5ab277ebd9986de41527ed6`, rama `codex/distritos-autonomicos`.

## Evidencia y reconstrucción

El almacenamiento local contenía los paquetes de fuentes, pero no los checkpoints de distritos.
Se consultaron metadatos remotos; se guardaron únicamente La Rioja M05 (2.110.240 bytes)
y Cantabria M06 (3.053.384 bytes), mediante las autorizaciones de red del entorno.
Sus SHA-256 coinciden con GitHub y, para Cantabria, con el producto territorial durable.
Los ZIP originales quedan en `/private/tmp/ddd-rioja-M05.zip` y
`/private/tmp/ddd-cantabria-M06.zip`; no se presupone conservación permanente de `/tmp`.
La disponibilidad e identidades completas están en el JSON de disponibilidad adjunto.
Caducidad remota: La Rioja 20 de octubre; Cantabria 19 de octubre de 2026.

El checkpoint de La Rioja contiene la salida M04 original, grafo M03, salida e informe M05.
El arnés lee esas entradas sin ejecutar M04 ni el motor base M05. Reconstruye el agrupado
`ddd_unit_id`, poblaciones de nodos, provincia, grupos municipales y protección de fronteras
cerradas del wrapper, con validación de cobertura, K, totales y poblaciones del informe.
Como `population_repair=DISABLED/NOT_NEEDED`, la salida conservada es exactamente el estado
que alcanzó la puerta del reparador: no hubo reparación ni escritura posterior de asignaciones.
El pulido swap también está desactivado. No se confunde este estado con la entrada del motor
base M05: las asignaciones M04 también se conservan separadamente en la fixture.

El core actual tiene SHA-256 `1c87809aefaa015307288f1d1491815ba3bbeafd70ddef8800fad9916cc874b8`,
idéntico al fingerprint de ambos runs. El arnés falla si cambia ese código o el hash del ZIP.
La regresión usa una extracción real de argumentos, no una ejecución sintética.
No se instala GIS: la lectura JSON no reconstruye geometrías ni recalcula adyacencias.

## Comparación

| Estado | Hard | Fuera de tolerancia | Mínimo | Máximo | Desviación máxima |
|---|---:|---:|---:|---:|---:|
| La Rioja, entrada M04 conservada | 0 | 1 | 8.750 | 13.846 | 41,775836069 % |
| La Rioja, puerta del reparador | 0 | 1 | 8.750 | 13.846 | 41,775836069 % |
| La Rioja, reparador aislado por defecto | 0 | 1 | 8.750 | 13.846 | 41,775836069 % |
| La Rioja, ensayo focal directo | 0 | 1 | 8.750 | 13.846 | 41,775836069 % |
| Cantabria, producto histórico M06 | 0 | 11 | 13.459 | 28.965 | 72,2973145226 % |

La Rioja: 343 secciones, 193 unidades, K=33, población=322.282, provincia=26;
target=9.766,121212121212, tolerancia absoluta=1.171,9345454545453;
floor=7.812,89696969697, cap=17.090,71212121212. Sin exenciones de suelo.
Se mantienen los 19 distritos urbanos cerrados, atomicidad, integridad municipal,
provincia y contigüidad del grafo protegido. La suma de desviaciones relativas es
2,201599841133; se conservan 181 aristas de corte y no hay movimientos aceptados.
Los límites y poblaciones completas están en el JSON de evidencia y la fixture.

Cantabria se lee sin recalcular. El producto durable es `PASS_WITH_EXCEPTIONS`, run
37318299003, commit fuente `3938c97a8b46590a54016173416acf34c165d5a1`.
La reparación histórica pasó de hard=1/outside=6 a hard=0/outside=11, con 7 pasos,
9 unidades transferidas y 1,583047 s registrados. Target=16.811,057142857142;
floor=13.448,845714285715, cap=29.419,35, tolerancia=2.017,326857142857.
El informe conserva campos poblacionales previos a la reparación: se usan las
poblaciones finales autoritativas `population_repair.population_after`, contrastadas
con las asignaciones. No se interpreta la antigua fila de 6.778 habitantes como resultado final.
Las restricciones estructurales finales se verifican leyendo el checkpoint; no es recertificación.

## Causa concreta y prueba acotada

El distrito 22 agrupa Alfaro (9.821) y Rincón de Soto (4.025): 13.846 habitantes.
La banda fina es [8.594,186666666666, 10.938,055757575758]. Rincón de Soto es indivisible
y solo tiene dos vecinos: Alfaro y Aldeanueva de Ebro (2.744).
Con Alfaro supera el techo fino. Solo con Aldeanueva suma 6.769 y queda por debajo
del mínimo. Para crecer desde ese conjunto debe añadir Alfaro, Autol (4.811) o el
residual indivisible de Calahorra (7.210); las sumas son 16.590, 11.580 y 13.979.
Todas superan el techo fino. La enumeración exhaustiva visita solo dos conjuntos
bajo el techo y no encuentra ninguno en banda. Con poblaciones no negativas, añadir
más unidades no puede recuperar un conjunto que ya excede el techo.

Por tanto, **no existe un distrito conectado en banda que contenga esta unidad bajo
el grafo y atomicidad recibidos por el reparador**; no existe una partición global
`outside=0` en ese espacio. No se extrapola a otra unidad mínima o a otro grafo.
La transferencia legal Rincón→28 traslada el outlier y empeora la desviación máxima
de 41,78 % a 43,14 %. El motor puede explorar estados intermedios, pero no puede
superar esta obstrucción sin cambiar el problema. No se ha encontrado defecto causal de código.

La puerta productiva no activa el reparador cuando hard=0; eso explica `DISABLED`,
pero activarlo aisladamente tampoco resuelve este caso. No se modifica esa política.
El ensayo por defecto termina `TIME_BUDGET_EXHAUSTED`, sin fase focal; el ensayo
con `max_depth=0` entra directamente en focal y agota la cola en dos estados.
Ambos retornan `NO_FEASIBLE_REPAIR_FOUND` y conservan el baseline.

## Coste, pruebas y reproducción

Último ensayo por defecto: 5,038950 s de pared, 4,668742 s CPU usuario,
0,075100 s CPU sistema; RSS máximo del proceso 110.489.600 bytes (Mac).
Límites: 5 s, 20.000 candidatos admisibles, profundidad primaria 3, conjuntos de 2.
El límite temporal es cooperativo, con un pequeño sobrepaso observable; no es un kill externo.
El ensayo focal directo tarda 0,004562 s y examina 2 candidatos / 8 transiciones.
RSS es máximo acumulado del proceso, no memoria incremental de la búsqueda.
Los contadores completos del último ensayo están en el JSON; pueden variar por tiempo y equipo.
Se ejecutaron dos ensayos por defecto durante la preparación del arnés (unos 10 s en total),
además de ensayos focales de milisegundos. No se prolongó la optimización.

```sh
python3 herramientas/repro_reparador_rioja_cantabria.py --rioja-checkpoint /private/tmp/ddd-rioja-M05.zip --cantabria-checkpoint /private/tmp/ddd-cantabria-M06.zip --output /private/tmp/comparacion.json
python3 -m unittest tests.test_repro_reparador_rioja_cantabria tests.test_m05_population_repair -q
git diff --check
```

Pruebas dirigidas: 34 PASS. Incluyen la partición real, obstrucción exhaustiva,
rechazo de hash incorrecto, salida reparada que no prueba el input, core cambiado,
presupuesto excesivo y diferencia entre cola agotada, corte y conjunto factible.
No hay corrección productiva; por eso no existe prueba de defecto que falle antes
y pase después de un parche. La regresión conserva el diagnóstico exacto.
La fixture permite repetir el ensayo focal y la prueba de obstrucción sin descargar ZIP.

Política de versiones: solo archivos nuevos con metadatos; no se sustituye ningún
predecesor funcional, no cambia versión ni contrato del motor. El incremento queda
CI_PENDIENTE, sin promoción ni nueva certificación territorial. La corrección electoral
72e4eac0 se conserva sin modificaciones; no existe dependencia causal demostrada.

## Decisión de siguiente paso

Cerrar este paquete de diagnóstico. Aumentar presupuesto o reintentar el reparador
con estas mismas entradas no puede eliminar todos los outliers. Si Work quiere
estudiar otro espacio de soluciones, debe dirigir un encargo separado sobre la
formación de unidades/topología con evidencia oficial y contratos aplicables; no
hay autorización aquí para partir municipios, cambiar tolerancia, regenerar M04
ni lanzar una nueva ejecución territorial.

Push, PR, merge, workflows, ejecuciones territoriales, publicaciones: NO.
Revisión separada y commit local: se registran en el cierre de la entrega.
