# Autorización de campaña 2026-11-10_regeneracion-nocturna-corte-71-v2

- Decisión: D-52 (autorización por campaña). Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: «Autorizo la campaña 2026-11-10_regeneracion-nocturna-corte-71-v2 tal como figura en la ficha.»
- Fecha y hora de la frase (Europe/Madrid): 2026-11-10 22:30 (aprox.)
- Estado de la ficha: BORRADOR. Sustituye a `2026-11-10_regeneracion-nocturna-corte-71` (prueba en La Rioja y requisito T-221). Requiere el relevo del motor (P30 con el motor nuevo) y T-221 (certificación con el plan ganador) fusionados en `main`; el flujo y sus entradas exactas se fijan entonces y se anotan aquí antes del primer lanzamiento.
- Caducidad: 2026-11-11 22:30 (24 h).
- Gasto semanal al autorizar: se mide al recibir la frase y se anota aquí; tope 15.000 min/semana, aviso al 70 %. **AVISO** si el acumulado más el tope de esta campaña supera 10.500 min.

## Límites
| Campo | Contenido |
|---|---|
| Qué se lanza | por territorio, la cadena de producción con el motor nuevo (P30): distritos (territorial) → legislatura → resultados por distrito (electoral), encadenada en GitHub (`publication_mode=territorial_only`, `cadena_electoral=true` o su equivalente tras el corte), sin publicar |
| Territorios | RESTRINGIDO (10-11, decisión del propietario vía Planificador; solo reduce lo autorizado): solo las 19 autonómicas; el Congreso (52) no se regenera hasta la nueva legislatura. Original: los 71 (52 circunscripciones del Congreso + 19 autonómicas); primero 1 territorio de prueba (La Rioja autonómica, `la_rioja`: pequeña, con cambio de plan —ganador con 81 secciones cambiadas— y ruta autonómica; recorre la ruta real del motor nuevo), y el resto solo si la prueba completa la cadena con distritos certificados y resultados por distrito |
| Mapa / motor | motor nuevo (D8, 10 cadenas) tras el relevo; contratos vigentes |
| Publica | no (`publish_result=false`); el visor no cambia |
| Tope de coste | 1 + 70 cadenas más reintentos; 6.500 min de Actions (suma de la duración de los jobs). Estimado: 60-90 min por territorio (generación 26-61 min + legislatura + electoral) ≈ 4.300-6.400 min |
| Concurrencia | lanzar en tandas que respeten el límite de runners; no lanzar un territorio con run en curso (también de `github-actions[bot]`) |
| Tope de reintentos | 1 por territorio, solo tras fallo transitorio (red, runner, rate limit) |
| FUERA | lo de `README.md`; publicar; borrados; cambios de motor, contrato o criterio; aprobar `produccion` (lo hace el propietario si el flujo lo pide) |
| Parada | si la 00 de prueba de La Rioja (motor2) no da el mismo ganador y la misma huella que la batería de Actions para `la_rioja` (referencia: `2026-11-10_bateria-motor2-autonomicas-r5`, fase 2, run 42927322822, con T-217/T-222/T-223 en `main`), parar sin lanzar el resto (añadido el 10-11 a petición del Planificador; solo restringe lo autorizado); primer fallo no transitorio → no lanzar más tandas; los runs en curso de otros territorios siguen; diagnóstico; informar y esperar nueva frase |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|
| 11:26 | La Rioja (prueba) | P00 Campaña, Generar desde fuente, motor2, Canónico, territorial_only + cadena_electoral, sin publicar | 43003614878 | SUCCESS: mismo ganador (`ponderado-s662638790`) y huella que r6; Activación 43006886208 y electoral 43007066596 en success | 1 / — | 0/1 |
| 12:23 | tanda 1: Andalucía 43011608060, Aragón 43011616681, Asturias 43011625216, Baleares 43011633844, Canarias 43011642069 | P00 Campaña motor2 | — | Andalucía FAILURE no transitorio en «Verificar bytes de la fuente territorial acreditada»: «Artefacto territorial ausente o ambiguo» (exit 72); Aragón y Asturias cadena completa; Baleares y Canarias cadena completa | 6 / — | 0/1 |
| 14:03 | tanda 2 (continuación sin Andalucía, confirmada por el propietario: «Confirmo seguir la regeneración nocturna v2 de las autonomías sin Andalucía, en tandas de 5.», 14:02): Cantabria 43025633460, Castilla y León 43025642604, Castilla-La Mancha 43025652192, Cataluña 43025661789, Comunidad Valenciana 43025671156 | P00 Campaña motor2 | — | EN_VUELO | 11 / — | 0/1 |

## Cierre
Estado: `EN_CURSO` sin Andalucía (tanda 2). Caduca 2026-11-11 22:30. Último uso: 2026-11-11.

Frase propuesta: «Autorizo la campaña 2026-11-10_regeneracion-nocturna-corte-71-v2 tal como figura en la ficha.»
