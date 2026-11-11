# Autorización de campaña 2026-11-11_congreso-completar-31-motor2

- Decisión: D-52 (autorización por campaña) y D-81. Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: (pendiente)
- Fecha y hora de la frase (Europe/Madrid): (pendiente)
- Estado de la ficha: BORRADOR. Continúa `2026-11-11_regeneracion-congreso-52-motor2-2023` (PARADA en Álava). T-230b (#706) en `main`.
- Caducidad: 24 h desde la frase del propietario.
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

## Cierre
Estado: `BORRADOR`. Último uso: —.

Frase propuesta: «Autorizo la campaña 2026-11-11_congreso-completar-31-motor2 tal como figura en la ficha.»
