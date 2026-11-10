# Autorización de campaña 2026-11-10_bateria-motor2-autonomicas-r4

- Decisión: D-52 (autorización por campaña). Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: (pendiente)
- Fecha y hora de la frase (Europe/Madrid): (pendiente)
- Estado de la ficha: BORRADOR. Requiere T-217 y T-218 fusionadas en `main`; las entradas exactas se fijan con ellas.
- Caducidad: 24 h desde la frase del propietario.
- Gasto semanal al autorizar: se mide al recibir la frase y se anota aquí; tope 15.000 min/semana, aviso al 70 %.

## Límites
| Campo | Contenido |
|---|---|
| Qué se lanza | `bateria-motor.yml` («Auxiliar — Batería del Motor»): `motor=motor2`, `funcion=D8`, `cadenas=10` |
| Fase 1 | una ejecución con `territorios=madrid comunidad_foral_de_navarra` (Comunidad de Madrid y Navarra) |
| Criterio para la fase 2 (objetivo, del run de la fase 1) | run en success y, en ambas, aceptación «SÍ» con «nunca peor que el vigente» y 0 `FALLO_GENERADOR` |
| Fase 2 | una ejecución con las 19 autonómicas: `andalucia aragon canarias cantabria castilla_la_mancha castilla_y_leon cataluna ceuta comunidad_foral_de_navarra comunidad_valenciana extremadura galicia illes_balears la_rioja madrid melilla pais_vasco principado_de_asturias region_de_murcia` |
| Mapa / motor | motor nuevo con D8 y 10 cadenas; sin relevo del motor vigente |
| Publica | no |
| Tope de coste | 2 ejecuciones más reintentos; 400 min de Actions (suma de la duración de los jobs). Referencia r3: las 19 autonómicas, 185 min; Madrid 14 y Navarra 13 |
| Tope de reintentos | 1 por ejecución, solo tras fallo transitorio (red, runner, rate limit) |
| FUERA | lo de `README.md`; publicar; escribir en `main`; archivar en R2; relevo del motor; territorios del Congreso; cambios de motor, contrato o criterio |
| Parada | primer fallo no transitorio → no relanzar; cancelar lo que siga en curso de esa ejecución; diagnóstico; informar y esperar nueva frase |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|

## Cierre
Estado: `BORRADOR` (espera T-217/T-218 y la frase del propietario). Último uso: —.

Frase propuesta: «Autorizo la campaña 2026-11-10_bateria-motor2-autonomicas-r4 tal como figura en la ficha.»
