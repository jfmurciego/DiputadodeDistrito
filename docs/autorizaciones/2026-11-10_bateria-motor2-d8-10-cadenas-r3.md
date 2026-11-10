# Autorización de campaña 2026-11-10_bateria-motor2-d8-10-cadenas-r3

- Decisión: D-52 (autorización por campaña). Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: «Autorizo la campaña 2026-11-10_bateria-motor2-d8-10-cadenas-r3 tal como figura en la ficha.»
- Fecha y hora de la frase (Europe/Madrid): 2026-11-10 19:20 (aprox.)
- Estado de la ficha: BORRADOR. Sustituye a `-r2` (PARADA: el lock del laboratorio subía pandas a 3.0.5 y geopandas a 1.1.4). Requiere T-181b fusionada en `main`.
- Caducidad: 2026-11-13 19:20 (72 h).
- Gasto semanal al autorizar: se mide al recibir la frase y se anota aquí; tope 15.000 min/semana, aviso al 70 %.

## Límites
| Campo | Contenido |
|---|---|
| Qué se lanza | `bateria-motor.yml` («Auxiliar — Batería del Motor»): `motor=motor2`, `funcion=D8`, `cadenas=10` |
| Fase 1 | una ejecución con `territorios=congreso_soria congreso_barcelona` (Barcelona falló en `-r2`) |
| Criterio para la fase 2 (objetivo, del run de la fase 1) | run en success y, en Soria y en Barcelona: todos los candidatos evaluados (1 canónico + 10 ponderadas + exhaustivo si es pequeño), canónico sin fallo, 0 `FALLO_GENERADOR`, y el paso de comprobación de versiones del lock base en verde en ambos jobs de competición |
| Fase 2 | una ejecución con `territorios` vacío (los 71), solo si se cumple el criterio |
| Mapa / motor | motor nuevo con D8 y 10 cadenas; sin relevo del motor vigente |
| Publica | no |
| Tope de coste | 2 ejecuciones más reintentos; 800 min de Actions (suma de la duración de los jobs) |
| Tope de reintentos | 1 por ejecución, solo tras fallo transitorio (red, runner, rate limit) |
| FUERA | lo de `README.md`; publicar; escribir en `main`; archivar en R2; relevo del motor; cambios de motor, contrato o criterio |
| Parada | primer fallo no transitorio → no relanzar; cancelar lo que siga en curso de esa ejecución para no gastar; diagnóstico; informar y esperar nueva frase |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|

## Cierre
Estado: `ACEPTADA, EN_ESPERA` de T-181b en `main` (no estaba al recibir la frase). Último uso: —.

Frase propuesta: «Autorizo la campaña 2026-11-10_bateria-motor2-d8-10-cadenas-r3 tal como figura en la ficha.»
