# Autorización de campaña 2026-11-10_regeneracion-nocturna-corte-71

- Decisión: D-52 (autorización por campaña). Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: «Autorizo la campaña 2026-11-10_regeneracion-nocturna-corte-71 tal como figura en la ficha.»
- Fecha y hora de la frase (Europe/Madrid): 2026-11-10 22:08 (aprox.)
- Estado de la ficha: BORRADOR. Requiere el relevo del motor (P30 con el motor nuevo) fusionado en `main`; el flujo y sus entradas exactas se fijan entonces y se anotan aquí antes del primer lanzamiento.
- Caducidad: 2026-11-11 22:08 (24 h).
- Gasto semanal al autorizar: se mide al recibir la frase y se anota aquí; tope 15.000 min/semana, aviso al 70 %. **AVISO** si el acumulado más el tope de esta campaña supera 10.500 min.

## Límites
| Campo | Contenido |
|---|---|
| Qué se lanza | por territorio, la cadena de producción con el motor nuevo (P30): distritos (territorial) → legislatura → resultados por distrito (electoral), encadenada en GitHub (`publication_mode=territorial_only`, `cadena_electoral=true` o su equivalente tras el corte), sin publicar |
| Territorios | los 71 (52 circunscripciones del Congreso + 19 autonómicas); primero 1 territorio de prueba (Soria), y el resto solo si la prueba completa la cadena con distritos certificados y resultados por distrito |
| Mapa / motor | motor nuevo (D8, 10 cadenas) tras el relevo; contratos vigentes |
| Publica | no (`publish_result=false`); el visor no cambia |
| Tope de coste | 1 + 70 cadenas más reintentos; 6.500 min de Actions (suma de la duración de los jobs). Estimado: 60-90 min por territorio (generación 26-61 min + legislatura + electoral) ≈ 4.300-6.400 min |
| Concurrencia | lanzar en tandas que respeten el límite de runners; no lanzar un territorio con run en curso (también de `github-actions[bot]`) |
| Tope de reintentos | 1 por territorio, solo tras fallo transitorio (red, runner, rate limit) |
| FUERA | lo de `README.md`; publicar; borrados; cambios de motor, contrato o criterio; aprobar `produccion` (lo hace el propietario si el flujo lo pide) |
| Parada | primer fallo no transitorio → no lanzar más tandas; los runs en curso de otros territorios siguen; diagnóstico; informar y esperar nueva frase |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|

## Cierre
Estado: `SUSTITUIDA` por `2026-11-10_regeneracion-nocturna-corte-71-v2` (cambia la prueba a La Rioja y añade T-221); frase sin uso. Último uso: —.

Frase propuesta: «Autorizo la campaña 2026-11-10_regeneracion-nocturna-corte-71 tal como figura en la ficha.»
