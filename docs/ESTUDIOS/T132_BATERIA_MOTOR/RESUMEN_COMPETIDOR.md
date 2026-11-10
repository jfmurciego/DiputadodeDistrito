# Motor nuevo (primera versión, D-48): competición «canónico + GerryChain» en los 71 territorios

Fecha: 2026-11-10. Competidor: `ddd_motor2.competidor` (rama t163-competidor-m05 @ddcc3ff), que en cada territorio
ejecuta el motor actual (canónico) y 5 cadenas GerryChain con semillas públicas (derivadas de las huellas de la base
territorial) y se queda con el mejor plan válido según el núcleo de reglas. Mismas entradas (base territorial reconstruida
desde fuente), mismo contrato y la misma validación de producción que la batería. Detalle: `COMPETIDOR.csv`.

## Criterio de aceptación

| Criterio | Resultado |
|---|---|
| 71/71 válidos (validación de producción) | **Sí: 71/71** |
| Ninguno peor que el canónico (fuera de tolerancia, después desvío máximo) | **Sí: mejora 21, empata 50, empeora 0** |
| Tiempos | 221 min en total, frente a 40 min del canónico (×5,6); mediana 92 s; máximo 992 s (Cataluña) |
| Reproducibilidad bit a bit | **Sí**: Congreso Huesca, Álava y Soria dan la misma composición en tres ejecuciones (sha256) |

Ganador: el canónico en 45 territorios y una cadena GerryChain en 26.

## Territorios que mejoran

| Territorio | Fuera de tolerancia (canónico) | Desvío máx. (canónico) | Ganador |
|---|---|---|---|
| andalucia | 16 (20) | 0.7455 (0.7455) | gerrychain-s1545196287 |
| cantabria | 8 (9) | 0.7230 (0.7230) | gerrychain-s598047657 |
| castilla_la_mancha | 4 (5) | 0.4074 (0.4074) | gerrychain-s755139571 |
| castilla_y_leon | 1 (2) | 0.1611 (0.1364) | gerrychain-s1439468606 |
| cataluna | 28 (53) | 0.6212 (0.6212) | gerrychain-s668019616 |
| comunidad_foral_de_navarra | 12 (24) | 0.6478 (0.6478) | gerrychain-s1614479722 |
| comunidad_valenciana | 30 (42) | 0.7468 (0.7468) | gerrychain-s882243471 |
| congreso_barcelona | 0 (1) | 0.1446 (0.2231) | gerrychain-s1594088439 |
| congreso_cantabria | 0 (0) | 0.0048 (0.0095) | gerrychain-s316109232 |
| congreso_castellon | 0 (0) | 0.0081 (0.0122) | gerrychain-s631585320 |
| congreso_ciudad_real | 0 (0) | 0.0083 (0.0486) | gerrychain-s2018848443 |
| congreso_granada | 0 (0) | 0.0255 (0.0447) | gerrychain-s72478774 |
| congreso_guipuzcoa | 0 (0) | 0.0742 (0.1054) | gerrychain-s2124606281 |
| congreso_huesca | 0 (0) | 0.0002 (0.0006) | gerrychain-s1417755764 |
| congreso_la_coruna | 0 (0) | 0.0313 (0.0506) | gerrychain-s250484495 |
| congreso_lugo | 0 (0) | 0.0036 (0.0044) | gerrychain-s47096818 |
| congreso_vizcaya | 0 (0) | 0.0549 (0.0767) | gerrychain-s1495274892 |
| extremadura | 0 (1) | 0.1073 (0.1230) | gerrychain-s1715659553 |
| galicia | 4 (6) | 0.5618 (0.5618) | gerrychain-s1325857207 |
| madrid | 21 (24) | 0.7387 (0.7387) | gerrychain-s291855033 |
| pais_vasco | 6 (9) | 0.2362 (0.2362) | gerrychain-s1946423693 |
