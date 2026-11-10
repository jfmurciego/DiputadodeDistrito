# Autorización de campaña 2026-11-10_bateria-motor2-d8-10-cadenas

- Decisión: D-52 (autorización por campaña). Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: (pendiente)
- Fecha y hora de la frase (Europe/Madrid): (pendiente)
- Estado de la ficha: BORRADOR. Requiere que esté fusionado en `main` el modo motor2 de la batería (T-208); el Planificador avisa al propietario cuando esté lista.
- Caducidad: 72 h desde la frase del propietario.
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

## Cierre
Estado: `BORRADOR` (espera la fusión de T-208 y la frase del propietario). Último uso: —.

Frase propuesta: «Autorizo la campaña 2026-11-10_bateria-motor2-d8-10-cadenas tal como figura en la ficha.»
