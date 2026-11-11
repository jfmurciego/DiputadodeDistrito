# Autorización de campaña 2026-11-11_congreso-completar-31-motor2

- Decisión: D-52 (autorización por campaña) y D-81. Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: «Autorizo la campaña 2026-11-11_congreso-completar-32-motor2 tal como figura en la ficha.» (nombra la versión de 32; esta de 31 es la misma menos Jaén, ya completo: solo restringe)
- Fecha y hora de la frase (Europe/Madrid): 2026-11-11 08:40 (aprox.)
- Estado de la ficha: BORRADOR. Continúa `2026-11-11_regeneracion-congreso-52-motor2-2023` (PARADA en Álava). T-230b (#706) en `main`.
- Caducidad: 2026-11-12 08:40 (24 h).
- Gasto semanal al autorizar: se mide al recibir la frase y se anota aquí; tope 15.000 min/semana, aviso al 70 %.

## Límites
| Campo | Contenido |
|---|---|
| Qué se lanza (31) | `ejecucion-completa-proyecto.yml` («P00 Campaña»): `execution_mode=Generar desde fuente territorial acreditada`, `motor=motor2`, `optimization_algorithm=Canónico`, `publication_mode=territorial_only`, `cadena_electoral=true`, `publish_result=false` |
| Territorios (31) | los 31 cancelados sin empezar (Asturias, Burgos, Cantabria, Ceuta, Huelva, Huesca, Las Palmas, León, Lugo, Lérida, Madrid, Melilla, Murcia, Málaga, Navarra, Orense, Palencia, Pontevedra, Salamanca, Santa Cruz de Tenerife, Segovia, Sevilla, Soria, Tarragona, Teruel, Toledo, Valencia, Valladolid, Vizcaya, Zamora, Zaragoza) |
| Álava | además, una P00 Campaña de Congreso Álava con `execution_mode=Reutilizar progreso existente`, `motor=motor2`, mismas demás entradas (completa su par con T-230b) |
| Tandas | de 5 territorios; la siguiente solo cuando las 5 de la anterior hayan terminado su cadena (territorial → legislatura → electoral). El Operador comprueba el final de cada tanda con una consulta puntual (sin vigilancia continua) o al recibir aviso del Coordinador/Planificador |
| Fuera de esta ficha | Jaén (20 jobs en success y cadena completa: Activación 42955511066 y electoral 42955644352 en success; el «cancelled» del run es solo la marca final); Albacete, Barcelona y Cádiz (cadena completa; solo falló el push del estado operativo compartido) |
| Publica | no |
| Tope de coste | 32 cadenas (31 + Álava) más reintentos; 3.000 min de Actions (suma de la duración de los jobs) |
| Tope de reintentos | 1 por territorio, solo tras fallo transitorio (red, runner, rate limit; un push rechazado por contención cuenta como transitorio) |
| FUERA | lo de `README.md`; publicar; Congreso de 350; borrados; cambios de motor, contrato o criterio; aprobar `produccion` |
| Parada | primer fallo no transitorio → no lanzar más tandas; diagnóstico; informar y esperar nueva frase |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|
| 08:42 | tanda 1: Álava (Reutilizar) 42981402781, Asturias 42981406489, Burgos 42981415070, Cantabria 42981422592, Ceuta 42981430591 | P00 Campaña motor2 | — | SUCCESS: las 5 cadenas completas (territorial, Activación y electoral en success) | 5 / — | 0/1 |
| 10:00 | tanda 2: Huelva 42991542477, Huesca 42991551418, Las Palmas 42991561887, León 42991571678, Lugo 42991580539 | P00 Campaña motor2 | — | SUCCESS: las 5 cadenas completas | 10 / — | 0/1 |
| 11:13 | tanda 3: Madrid 43001749134, Melilla 43001757563, Murcia 43001766635, Málaga 43001775134, Navarra 43001785293 | P00 Campaña motor2 | — | SUCCESS: las 5 cadenas completas | 15 / — | 0/1 |
| 12:27 | tanda 4: Orense 43012119307, Palencia 43012127687, Pontevedra 43012135258, Salamanca 43012143922, Santa Cruz de Tenerife 43012151677 | P00 Campaña motor2 | — | EN_VUELO | 20 / — | 0/1 |

## Cierre
Estado: `EN_CURSO` (tanda 4). Último uso: 2026-11-11.

Frase propuesta: «Autorizo la campaña 2026-11-11_congreso-completar-31-motor2 tal como figura en la ficha.»
