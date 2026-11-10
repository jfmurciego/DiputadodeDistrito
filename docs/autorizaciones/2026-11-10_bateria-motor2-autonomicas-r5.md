# Autorización de campaña 2026-11-10_bateria-motor2-autonomicas-r5

- Decisión: D-52 (autorización por campaña). Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: «Autorizo la campaña 2026-11-10_bateria-motor2-autonomicas-r5 tal como figura en la ficha.»
- Fecha y hora de la frase (Europe/Madrid): 2026-11-11 00:10 (aprox.)
- Estado de la ficha: BORRADOR. Repite `-r4` (PARADA: la aceptación no descontaba el vigente del recuento de candidatos). Requiere T-222 fusionada en `main` (además de T-217/T-218, ya en `main`).
- Caducidad: 2026-11-12 00:10 (24 h).
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
| 00:22 | Comunidad de Madrid + Navarra (fase 1) | batería motor2 D8 N=10 | 42922787428 | SUCCESS; aceptación «PARCIAL» solo porque faltan las huellas reales (Soria, Álava, Melilla no están en la fase 1); todas las comprobaciones en verde: Madrid y Navarra VALIDO 12/12, mejoran al canónico, ninguna peor que el vigente, 0 FALLO_GENERADOR, recuento correcto. Criterio literal «SÍ» no alcanzable en esta fase: consulta al propietario | 1 / 33 min | 0/1 |

## Cierre
Estado: `EN_CURSO` (T-222 en `main`, #695; main 0d34f64 en verde). Último uso: 2026-11-11.

Frase propuesta: «Autorizo la campaña 2026-11-10_bateria-motor2-autonomicas-r5 tal como figura en la ficha.»
