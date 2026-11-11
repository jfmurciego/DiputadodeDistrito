# Autorización de campaña 2026-11-11_regeneracion-congreso-52-motor2-2023

- Decisión: D-52 (autorización por campaña) y D-81. Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: «Autorizo la campaña 2026-11-11_regeneracion-congreso-52-motor2-2023 tal como figura en la ficha.» Añadió: «No monitorices ningun job, ni este ni el autonomico».
- Fecha y hora de la frase (Europe/Madrid): 2026-11-11 01:05 (aprox.)
- Estado de la ficha: ACEPTADA. Sin vigilancia de runs (orden del propietario): cada paso siguiente se da al recibir aviso del Coordinador/Planificador o del propietario.
- Caducidad: 2026-11-12 01:05 (24 h).
- Gasto semanal al autorizar: se mide al recibir la frase y se anota aquí; tope 15.000 min/semana, aviso al 70 %. **AVISO**: con la nocturna de las 19 en paralelo, el acumulado previsto puede acercarse al 70 %.

## Límites
| Campo | Contenido |
|---|---|
| Qué se lanza | `ejecucion-completa-proyecto.yml` («P00 Campaña»): `execution_mode=Generar desde fuente territorial acreditada`, `motor=motor2`, `optimization_algorithm=Canónico`, `publication_mode=territorial_only`, `cadena_electoral=true`, `publish_result=false`; contratos actuales (Congreso 2023) |
| Referencia | antes de la prueba, una batería «VER Verificación del motor» (`bateria-motor.yml`, `motor=motor2`, `funcion=D8`, `cadenas=10`, `territorios=congreso_la_rioja`) con el código actual; cuenta en el tope |
| Prueba | Congreso La Rioja (`Congreso La Rioja`). En la batería r3 (run 42886114842) mejoró al canónico: ganador `ponderado-s1629856150`, huella `c023261ac67d0dd3…` |
| Condición de la prueba | la cadena completa (territorial → legislatura → electoral) en success, y el mismo ganador y la misma huella que la batería de referencia para `congreso_la_rioja`; si no, parar e informar |
| Resto | si pasa la prueba, las otras 51 circunscripciones del Congreso, en tandas que respeten el límite de runners y sin tocar un territorio con run en curso |
| Paralelo | puede correr a la vez que `2026-11-10_regeneracion-nocturna-corte-71-v2` (19 autonómicas): territorios distintos |
| Publica | no |
| Tope de coste | 1 batería de referencia + 52 cadenas más reintentos; 3.500 min de Actions (suma de la duración de los jobs) |
| Tope de reintentos | 1 por territorio, solo tras fallo transitorio (red, runner, rate limit) |
| FUERA | lo de `README.md`; publicar; Congreso de 350; borrados; cambios de motor, contrato o criterio; aprobar `produccion` |
| Parada | primer fallo no transitorio → no lanzar más tandas; diagnóstico; informar y esperar nueva frase |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|
| 01:02 | Congreso La Rioja (referencia) | batería motor2 D8 N=10, `territorios=congreso_la_rioja` | 42928165086 | EN_VUELO | 1 / — | 0/1 |

## Cierre
Estado: `EN_CURSO`. Último uso: 2026-11-11.

Frase propuesta: «Autorizo la campaña 2026-11-11_regeneracion-congreso-52-motor2-2023 tal como figura en la ficha.»
