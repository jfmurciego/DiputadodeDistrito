# Autorización de campaña 2026-11-11_bateria-motor2-autonomicas-r6

- Decisión: D-52 (autorización por campaña). Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: «Autorizo la campaña 2026-11-11_bateria-motor2-autonomicas-r6 tal como figura en la ficha, y que sea la referencia de La Rioja para la regeneración nocturna v2.»
- Fecha y hora de la frase (Europe/Madrid): 2026-11-11 08:40 (aprox.)
- Estado de la ficha: BORRADOR. Repite la fase 2 de `-r5` (aceptación NO) con T-228 (#699) y T-229 (#700) en `main`.
- Caducidad: 2026-11-12 08:40 (24 h).
- Gasto semanal al autorizar: se mide al recibir la frase y se anota aquí; tope 15.000 min/semana, aviso al 70 %.

## Límites
| Campo | Contenido |
|---|---|
| Qué se lanza | una ejecución de `bateria-motor.yml` («VER Verificación del motor»): `motor=motor2`, `funcion=D8`, `cadenas=10`, `territorios=andalucia aragon canarias cantabria castilla_la_mancha castilla_y_leon cataluna ceuta comunidad_foral_de_navarra comunidad_valenciana extremadura galicia illes_balears la_rioja madrid melilla pais_vasco principado_de_asturias region_de_murcia` |
| Criterio (objetivo) | run en success y aceptación «SÍ»; cuenta como SÍ una aceptación «PARCIAL» cuyo único motivo sea faltar las huellas reales de Soria y Álava (no están entre las 19) si todo lo demás está en verde: 19/19 válidos, 0 `FALLO_GENERADOR`, recuento de candidatos correcto, ninguna peor que el canónico ni que el vigente, ninguna sin vigente comparable salvo Ceuta (sin mapa publicado) |
| Efecto | si se cumple, sirve de referencia de `la_rioja` para `2026-11-10_regeneracion-nocturna-corte-71-v2` (que sigue con su propia frase, caduca 2026-11-11 22:30) |
| Publica | no |
| Tope de coste | 1 ejecución más reintentos; 300 min de Actions (referencia r5 fase 2) |
| Tope de reintentos | 1, solo tras fallo transitorio (red, runner, rate limit) |
| FUERA | lo de `README.md`; publicar; escribir en `main`; archivar en R2; relevo del motor; cambios de motor, contrato o criterio |
| Parada | fallo no transitorio o criterio no cumplido → no relanzar; informar y esperar nueva frase |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|
| 08:42 | las 19 autonómicas | VER motor2 D8 N=10 | 42981399280 | FAILURE: aceptación NO. 7 adquirieron y están bien; 12 (Canarias, Cantabria, Castilla-La Mancha, Castilla y León, Cataluña, Comunidad Valenciana, Extremadura, Galicia, Baleares, Melilla, País Vasco, Murcia) acaban en FALLO_ADQUISICION tras ~490 s, sin error de red en el log (fuentes reconstruidas y verificadas antes): no consta como transitorio → sin reintento | 1 / — | 0/1 |

## Cierre
Estado: `PARADA` (FALLO_ADQUISICION sin causa de red visible; ante la duda, no transitorio). Decide el propietario. Último uso: 2026-11-11.

Frase propuesta: «Autorizo la campaña 2026-11-11_bateria-motor2-autonomicas-r6 tal como figura en la ficha.»
