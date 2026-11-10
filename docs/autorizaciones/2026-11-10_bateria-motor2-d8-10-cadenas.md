# Autorización de campaña 2026-11-10_bateria-motor2-d8-10-cadenas

- Decisión: D-52 (autorización por campaña). Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: «Autorizo la campaña 2026-11-10_bateria-motor2-d8-10-cadenas tal como figura en la ficha.»
- Fecha y hora de la frase (Europe/Madrid): 2026-11-10 17:33 (aprox.)
- Estado de la ficha: ACEPTADA. T-208 en `main` (#678); entradas: `motor=motor2`, `funcion=D8`, `cadenas=10`.
- Caducidad: 2026-11-13 17:33 (72 h desde la frase).
- Gasto semanal al autorizar: se mide al recibir la frase (`herramientas/metricas_proceso.py`) y se anota aquí; tope 15.000 min/semana, aviso al 70 %.

## Límites
| Campo | Contenido |
|---|---|
| Qué se lanza | `bateria-motor.yml` («Auxiliar — Batería del Motor») en modo motor2 (entradas exactas según T-208 en `main`), `archivar=false` |
| Territorios | 1) Soria (Congreso) como prueba; 2) solo si la prueba termina en success y con resultado válido, los 71 (`territorios` vacío) |
| Mapa / motor | motor nuevo con D8 y 10 cadenas; sin relevo del motor vigente |
| Publica | no |
| Tope de coste | 2 ejecuciones (prueba + 71) más reintentos; 800 min de Actions (suma de la duración de los jobs). Estimado 600-650 min (Planificador); referencia: la batería de los 71 con el motor nuevo sin D8 tardó 221 min |
| Tope de reintentos | 1 por ejecución, solo tras fallo transitorio (red, runner, rate limit; p. ej. ConnectionResetError en la descarga del INE) |
| FUERA | lo de `README.md`; publicar; escribir en `main`; archivar en R2; relevo del motor; cambios de motor, contrato o criterio |
| Parada | primer fallo no transitorio → no relanzar, diagnóstico, informar y esperar nueva frase. Si la prueba de Soria no es válida, no se lanzan los 71 |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|
| 17:33 | Soria (prueba) | batería motor2 D8 N=10, `territorios=congreso_soria` | 42855755112 | SUCCESS: aceptación PARCIAL (solo Soria), 0 no válidos, 0 peores, huella reproducible | 1 / 5 min | 0/1 |
| 17:39 | los 71 | batería motor2 D8 N=10, `territorios` vacío | 42856811551 | EN_VUELO | 2 / 5 min + en curso | 0/1 |

## Cierre
Estado: `EN_CURSO`. Último uso: —.

Frase propuesta: «Autorizo la campaña 2026-11-10_bateria-motor2-d8-10-cadenas tal como figura en la ficha.»
