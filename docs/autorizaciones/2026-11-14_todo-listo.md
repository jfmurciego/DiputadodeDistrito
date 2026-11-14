# Autorización de campaña 2026-11-14_todo-listo

- Decisión: D-52. Chat del Operador: session_01KQDtFqw1LBgGn6nCuxP8Yx. Pedida por el Planificador (session_01KQDtFtYpQq5zLM3zjjiapM).
- Frase literal del propietario: «Autorizo la campaña de la ficha 2026-11-14_todo-listo.» Su aclaración en el mismo mensaje: cubre la batería, la regeneración, la publicación de los 71, el ensayo electoral y el borrado de releases y artefactos sobrantes; un reintento por fallo transitorio; parada al primer fallo serio; caduca el 21-11.
- Fecha y hora de la frase (Europe/Madrid): 2026-11-14 15:10 (aprox.). La frase llegó antes de redactar la ficha; la ficha se ciñe a lo que dice la frase.
- Caducidad: 2026-11-21 23:59.
- Gasto semanal al autorizar (09-11 a 14-11, suma de la duración de 4.292 runs, tope 6 h por run; estimación): ~16.900 min (113 % de 15.000). El 52 % son las «Pruebas de la Plataforma». El repositorio vuelve a ser público, así que Actions no cobra. Previsto para la campaña: ~8.000 min.
- Condición de inicio: #747 (renombrado T-220) en `main` con la CI en verde.
- Los 71: el inventario del 12-11 (70 filas) más Andalucía (01), publicada en el lote 43206627505.

## Límites
| Campo | Contenido |
|---|---|
| 1. Batería | una `bateria-motor.yml` (VER): `motor=motor2`, `funcion=D8`, `cadenas=10`, los 71 territorios; el motor de `main` (optimizaciones T-256/T-261/T-262 y semilla oficial T-265, D-90) |
| 2. Regeneración | solo si la aceptación de la batería es «nunca peor» en los 71. `ejecucion-completa-proyecto.yml`: `execution_mode=Generar desde fuente territorial acreditada`, `motor=motor2`, `publication_mode=territorial_only`, `cadena_electoral=true`, `publish_result=false`; los 71, en tandas de 5 (la siguiente cuando las 5 cadenas anteriores han terminado). Cantabria y Extremadura solo en su tanda. Las Palmas con el contrato vigente en `main` |
| 3. Publicación | `desplegar-visor-publico.yml` (P50) por lotes con los runs electorales de la regeneración, con la guarda del INDEX; se quitan del lote los runs sin M08 |
| 4. Ensayo electoral | ensayo en seco de la noche del 29-11 con el motor y las rutas nuevas, en paralelo tras 1, sin publicar; con un flujo ya existente en `main` |
| 5. Borrado | al final: releases antiguas que no son de mapas (borradores `ensemble-*` y `cyl-m06-checkpoint-temp`, `poda_releases_2026-11-14/lista.tsv`; las 3 citadas en el registro del visor se borran solo si la publicación de 3 ya no las cita) y los artefactos de runs fallidos o sustituidos de esta campaña (con el mismo criterio que la propuesta del 14-11) |
| Tope de coste | 1 batería, 71 cadenas P00, P50 por lotes, ensayo, más reintentos; 10.000 min de Actions |
| Tope de reintentos | 1 por lanzamiento, solo tras un fallo transitorio con evidencia en el log (503, red, runner, rate limit) |
| FUERA | Congreso de 350; cambios de motor, contrato o criterio; aprobar `produccion`; fusionar `no-automerge`; borrar releases `mapa-*`, `fuente-*`, `almacen-m06-*` o `viewer-*` |
| Parada | al primer fallo no transitorio, a la caducidad o al tope: no lanzar más; diagnóstico; informar y esperar una frase nueva |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|
| 15:23 | — | P50 `desplegar-visor-publico.yml` «Sitio completo», `production_run_id` vacío (orden directa del propietario: «Publica de nuevo el sitio en diputadodedistrito.es: P50 solo sitio, con production_run_id vacío.») | 43604649733 | SUCCESS: PAGE_URL https://diputadodedistrito.es/, DEPLOYMENT_OUTCOME success | 1 / — | 0/1 |
| 15:28 | los 71 | 1. `bateria-motor.yml` motor2 D8 N=10 (main 2c4e2471, en verde sobre b5bd69e) | 43605070831 | EN_VUELO | 2 / — | 0/1 |

## Cierre
Estado: `EN_CURSO`.
