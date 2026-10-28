# A2 v1.9 — resultado de selección diversa

**Dictamen:** `NO_GO` para revisión funcional. La prueba dirigida vuelve a perder un prefijo antes del movimiento 9. Según el criterio de parada, no se ejecutó benchmark funcional completo ni se ensayó otra variante.

## Identidad fijada

- Rama/base: `codex/distritos-autonomicos` / `42163cd8cebd120db9ab9fd1329c32ccdd87cf36`.
- Predecesor v1.8 preservado en `legacy/core/m05_population_repair_v1.8.0_2026-10-10.py`, SHA-256 `19cbcffd70268f7eebfb75cb625bbea29bd66fade4d5a78ea819a0da91e1f2c8`.
- Código local v1.9: SHA-256 `064a32bce09aeafa4ecfd4e0d88e358f9e0cdf820e2dd805caee15180e58a602`.
- Checkpoint: SHA-256 `6a5181ddeca846dae3afde8e560ac51077d30ca82a09c85277d57406fe289d9c`; testigo: `6e832b1c6f35891d104f04ffdeedcb1fd7c7481a3598015b42aaf43f61d6091a`.
- Datos/contrato coinciden: asignación inicial recuperada exactamente al invertir el testigo, K=135, suelo 40.722,388148, techo 89.080,224074, objetivo 50.902,985185, tolerancia absoluta 6.108,358222. Las 82 transferencias son unitarias y pasan el validador v1.9; el replay llega a la asignación final validada. El manifiesto del testigo identifica otro hash M05 (`1c87809a…cc874b8`), por lo que el testigo confirma una ruta válida en estos mismos datos, no una salida producida por v1.9.
- La reproducción dirigida conservó beam 128 y los mismos topes declarados: 400.000 intentos, 400.000 estados, 180 s, 640 MiB, profundidad 96, radio 8 y 2 por distrito antes del tope global. Se detuvo al primer prefijo no seleccionado; no es un benchmark funcional.

## Primer bloqueo de v1.9

El prefijo 5 (`28:28003:M`, 91→125) vuelve a ser el primer punto perdido. Su padre (prefijo 4) estaba en la frontera y se expandió. La transferencia pasó las comprobaciones de provincia, contigüidad donante/receptor, atomicidad, disciplina municipal y transición hard; generó un estado candidato único. La deduplicación no lo eliminó. Sin embargo, el selector no lo incluyó entre los 128 estados.

v1.9 sustituyó la reserva de continuaciones con pareja repetida por una reserva del mejor hijo por estado padre, manteniendo la mitad superior por ranking global. El candidato del testigo quedó fuera de la mitad global y no fue el hijo conservado para su padre (o el padre ya estaba representado por la mitad global). La traza no registra cuál de esas dos ocupaciones ocurrió; sí prueba que el estado fue generado y rechazado por la selección del beam. No se llegó al noveno prefijo bajo esta variante, así que no puede acreditarse su supervivencia ni expansión.

En la ola del quinto movimiento: 129.777 intentos acumulados, 16.067 estados únicos nuevos (16.068 contando el inicial), 434 expansiones, 4.673 deduplicaciones acumuladas y 4.685 candidatos únicos en esa ola. El estado del testigo estaba en esos candidatos, pero `target_in_selected=false`. La reproducción tardó 35,45 s hasta esa selección; es coste de diagnóstico instrumentado, no coste del benchmark.

La traza completa y el script están en `traza_prefijos_v19_perdida_paso5.json` y `reproducir_prefijos_v19_hasta_perdida.py`. El script valida el testigo y ejecuta la búsqueda solo hasta el primer prefijo perdido.

## Pruebas y límites

- `python3 -m unittest tests.test_m05_population_repair -q`: 32 pruebas, PASS. Incluye caso genérico donde el siguiente handoff cambia de pareja donante/receptor.
- Regresión íntegra `python3 -m unittest tests.test_repro_reparador_rioja_cantabria -v`: 8 PASS, 1 ERROR y 1 FAIL. Ambos fallos se detienen en `REPAIR_CODE_DIFFERS_FROM_RUN`: el harness exige el hash histórico del motor. No se desactivó ni alteró esa guarda; La Rioja no queda acreditada como PASS.
- No se ejecutó benchmark funcional v1.9 porque el replay dirigido falló antes de alcanzar el noveno prefijo. Por ello no hay resultado hard final v1.9 y no se infiere una reparación.

## Recomendación

`NO_GO`. La selección por diversidad de padre tampoco conserva el prefijo necesario; no se debe avanzar a benchmark ni a integración con esta variante. La evidencia disponible pide una solución de conservación de trayectorias menos restrictiva que una sola plaza por padre, pero esta entrega se detiene aquí sin encadenar otra variante.
