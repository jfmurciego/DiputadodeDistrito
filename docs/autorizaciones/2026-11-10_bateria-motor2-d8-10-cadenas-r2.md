# Autorización de campaña 2026-11-10_bateria-motor2-d8-10-cadenas-r2

- Decisión: D-52 (autorización por campaña). Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: «Autorizo la campaña 2026-11-10_bateria-motor2-d8-10-cadenas-r2 tal como figura en la ficha.»
- Fecha y hora de la frase (Europe/Madrid): 2026-11-10 18:34 (aprox.)
- Estado de la ficha: BORRADOR. Repite la campaña `2026-11-10_bateria-motor2-d8-10-cadenas`, que no midió el motor nuevo (las 10 cadenas fallaron por falta de networkx/gerrychain en el flujo). Requiere T-181 fusionada en `main`.
- Caducidad: 2026-11-13 18:34 (72 h). T-181 en `main` (#681).
- Gasto semanal al autorizar: se mide al recibir la frase y se anota aquí; tope 15.000 min/semana, aviso al 70 %.

## Límites
| Campo | Contenido |
|---|---|
| Qué se lanza | `bateria-motor.yml` («Auxiliar — Batería del Motor»): `motor=motor2`, `funcion=D8`, `cadenas=10` |
| Territorios | 1) Soria (Congreso) como prueba; 2) los 71 (`territorios` vacío) solo si Soria termina en success Y su informe muestra las 10 cadenas ponderadas evaluadas (válidas o con motivo de rechazo del núcleo), 0 `FALLO_GENERADOR` y el recuento de candidatos según el flujo: 1 canónico + 10 ponderadas + exhaustivo si el territorio es pequeño (Soria: 12; sin GerryChain de producción) |
| Mapa / motor | motor nuevo con D8 y 10 cadenas; sin relevo del motor vigente |
| Publica | no |
| Tope de coste | 2 ejecuciones (prueba + 71) más reintentos; 800 min de Actions (suma de la duración de los jobs). Referencia: la ejecución anterior sin cadenas tardó ~440 min |
| Tope de reintentos | 1 por ejecución, solo tras fallo transitorio (red, runner, rate limit) |
| FUERA | lo de `README.md`; publicar; escribir en `main`; archivar en R2; relevo del motor; cambios de motor, contrato o criterio |
| Parada | primer fallo no transitorio → no relanzar, diagnóstico, informar y esperar nueva frase. Si Soria no cumple la condición de candidatos, no se lanzan los 71 |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|
| 18:34 | Soria (prueba) | batería motor2 D8 N=10, `territorios=congreso_soria` | 42866296198 | EN_VUELO | 1 / — | 0/1 |

## Cierre
Estado: `EN_CURSO`. Último uso: —.

Frase propuesta: «Autorizo la campaña 2026-11-10_bateria-motor2-d8-10-cadenas-r2 tal como figura en la ficha.»
