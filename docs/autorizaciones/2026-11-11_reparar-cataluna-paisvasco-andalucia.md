# Autorización de campaña 2026-11-11_reparar-cataluna-paisvasco-andalucia

- Decisión: D-52 (autorización por campaña). Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: «Autorizo la campaña 2026-11-11_reparar-cataluna-paisvasco-andalucia tal como figura en la ficha.»
- Fecha y hora de la frase (Europe/Madrid): 2026-11-11 15:14 (aprox.)
- Estado de la ficha: BORRADOR.
- Caducidad: 2026-11-12 15:14 (24 h).
- Gasto semanal al autorizar: se mide al recibir la frase y se anota aquí; tope 15.000 min/semana, aviso al 70 %.

## Límites
| Campo | Contenido |
|---|---|
| (A1) Cataluña, en orden | 1) `preparacion-resultados-electorales.yml` («P10 Fuentes — P12 Electorales»): `territory_id=09 Cataluña`, `data_edition=2025`, `reutilizar_si_ya_preparada=false`; 2) `preparacion-legislatura-vigente.yml` («P00 Campaña — Legislatura»): `territory=09 Cataluña`, `operation=prepare_one`; 3) `ejecucion-completa-proyecto.yml` («P00 Campaña»): `execution_mode=Reutilizar progreso existente`, `motor=motor2`, `optimization_algorithm=Canónico`, `publication_mode=territorial_only`, `publish_result=false` (su territorial motor2 ya está hecho, run 43025661789) |
| (A2) País Vasco, en orden | 1) P12 `territory_id=16 País Vasco`, `data_edition=2025`, `reutilizar_si_ya_preparada=false`; 2) P00 Campaña `execution_mode=Generar desde fuente territorial acreditada`, `motor=motor2`, `optimization_algorithm=Canónico`, `publication_mode=territorial_only`, `cadena_electoral=true`, `publish_result=false` (regenera su territorial y encadena legislatura y electoral). Sale de las pendientes de `2026-11-10_regeneracion-nocturna-corte-71-v2` |
| Condición tras el paso 1 | si hace falta un receipt nuevo en el catálogo para usar el paquete electoral regenerado: parar y avisar (lo prepara un implementador) |
| (B) Andalucía, solo con T-244 fusionada en `main` | 1) preparación electoral con `reutilizar_si_ya_preparada=false` solo si su paquete electoral hubiera caducado (hoy vivo hasta 2026-12-08: no se lanza); 2) `preparacion-legislatura-vigente.yml` `territory=01 Andalucía`, `operation=prepare_one`; 3) P00 Campaña `execution_mode=Generar desde fuente territorial acreditada`, `motor=motor2`, `optimization_algorithm=Canónico`, `publication_mode=territorial_only`, `cadena_electoral=true`, `publish_result=false` |
| Secuencia | cada paso solo tras success del anterior del mismo territorio (consulta puntual); Cataluña y País Vasco pueden ir en paralelo entre sí |
| Publica | no |
| Tope de coste | 600 min de Actions (suma de la duración de los jobs) |
| Tope de reintentos | 1 por paso, solo tras fallo transitorio (red, runner, rate limit) |
| FUERA | lo de `README.md`; publicar; otros territorios; cambios de motor, contrato, catálogo o criterio; aprobar `produccion` |
| Parada | primer fallo no transitorio → no seguir; diagnóstico; informar y esperar nueva frase |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|
| 15:14 | Cataluña (paso 1) | P12 Electorales, reutilizar=false | 43036592492 (por orden de despacho; verificar territorio en el log) | EN_VUELO | 1 / — | 0/1 |
| 15:14 | País Vasco (paso 1) | P12 Electorales, reutilizar=false | 43036604667 (ídem) | EN_VUELO | 2 / — | 0/1 |

## Cierre
Estado: `EN_CURSO`. Último uso: 2026-11-11.

Frase propuesta: «Autorizo la campaña 2026-11-11_reparar-cataluna-paisvasco-andalucia tal como figura en la ficha.»
