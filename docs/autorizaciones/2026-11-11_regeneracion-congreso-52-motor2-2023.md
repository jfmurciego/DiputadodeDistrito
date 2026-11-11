# Autorización de campaña 2026-11-11_regeneracion-congreso-52-motor2-2023

- Decisión: D-52 (autorización por campaña) y D-81. Chat del Operador: session_01KQDtFsAtHP9atzNnDthr9A.
- Frase literal del propietario: «Autorizo la campaña 2026-11-11_regeneracion-congreso-52-motor2-2023 tal como figura en la ficha.» Añadió: «No monitorices ningun job, ni este ni el autonomico».
- Fecha y hora de la frase (Europe/Madrid): 2026-11-11 01:05 (aprox.)
- Estado de la ficha: ACEPTADA. Sin vigilancia de runs (orden del propietario): cada paso siguiente se da al recibir aviso del Coordinador/Planificador o del propietario.
- Caducidad: 2026-11-12 01:05 (24 h).
- Gasto semanal al autorizar: se mide al recibir la frase y se anota aquí; tope 15.000 min/semana, aviso al 70 %. **AVISO**: con la nocturna de las 19 en paralelo, el acumulado previsto puede acercarse al 70 %.

## Límites
| Campo | Contenido |
|---|---|
| Qué se lanza | `ejecucion-completa-proyecto.yml` («P00 Campaña»): `execution_mode=Generar desde fuente territorial acreditada`, `motor=motor2`, `optimization_algorithm=Canónico`, `publication_mode=territorial_only`, `cadena_electoral=true`, `publish_result=false`; contratos actuales (Congreso 2023) |
| Referencia | antes de la prueba, una batería «VER Verificación del motor» (`bateria-motor.yml`, `motor=motor2`, `funcion=D8`, `cadenas=10`, `territorios=congreso_la_rioja`) con el código actual; cuenta en el tope |
| Prueba | Congreso La Rioja (`Congreso La Rioja`). En la batería r3 (run 42886114842) mejoró al canónico: ganador `ponderado-s1629856150`, huella `c023261ac67d0dd3…` |
| Condición de la prueba | la cadena completa (territorial → legislatura → electoral) en success, y el mismo ganador y la misma huella que la batería de referencia para `congreso_la_rioja`; si no, parar e informar |
| Resto | si pasa la prueba, las otras 51 circunscripciones del Congreso, en tandas que respeten el límite de runners y sin tocar un territorio con run en curso |
| Paralelo | puede correr a la vez que `2026-11-10_regeneracion-nocturna-corte-71-v2` (19 autonómicas): territorios distintos |
| Publica | no |
| Tope de coste | 1 batería de referencia + 52 cadenas más reintentos; 3.500 min de Actions (suma de la duración de los jobs) |
| Tope de reintentos | 1 por territorio, solo tras fallo transitorio (red, runner, rate limit) |
| FUERA | lo de `README.md`; publicar; Congreso de 350; borrados; cambios de motor, contrato o criterio; aprobar `produccion` |
| Parada | primer fallo no transitorio → no lanzar más tandas; diagnóstico; informar y esperar nueva frase |

## Ejecutado
| Hora | Territorio | Workflow y modo | Run | Resultado | Ejecuciones/min acumulados | Reintento (n/R) |
|---|---|---|---|---|---|---|
| 01:02 | Congreso La Rioja (referencia) | batería motor2 D8 N=10, `territorios=congreso_la_rioja` | 42928165086 | SUCCESS (PARCIAL solo por huellas): VALIDO 12/12, gana `ponderado-s1629856150` (mejora), huella `5f2a151e600b87e3a1e12552eb6f2c9e3c26ab1fbcdc87283cd854a35ce6892f` | 1 / — | 0/1 |
| 01:32 | Congreso La Rioja (prueba) | P00 Campaña, Generar desde fuente, motor2, Canónico, territorial_only + cadena_electoral, sin publicar | 42932144515 | SUCCESS: mismo ganador y huella que la referencia (61 secciones cambiadas); legislatura 42935599438 success; electoral 42935762636 success, sin publicar | 2 / — | 0/1 |
| 02:38 | las 51 restantes | P00 Campaña, mismas entradas | ver lista | PARADA (04:47, aviso del Planificador): fallo no transitorio en Álava (42940320710; Activación 42952637226 «sin un par durable válido», exit 54); Albacete, Barcelona y Cádiz fallan en «Actualizar estado operativo único» (push a main rechazado por contención). 15 territoriales en success, 1 en curso (Jaén, se deja terminar), 31 sin empezar cancelados por el Operador (force-cancel) | 53 / — | 0/1 |

Runs de las 51 (P00 territorial; cada uno encadena legislatura y electoral): Congreso Albacete 42940326013, Congreso Alicante 42940331557, Congreso Almería 42940336572, Congreso Asturias 42940479208, Congreso Badajoz 42940345930, Congreso Baleares 42940350970, Congreso Barcelona 42940355981, Congreso Burgos 42940361074, Congreso Cantabria 42940510614, Congreso Castellón 42940377493, Congreso Ceuta 42940573533, Congreso Ciudad Real 42940382446, Congreso Cuenca 42940397668, Congreso Cáceres 42940366579, Congreso Cádiz 42940371696, Congreso Córdoba 42940387433, Congreso Gerona 42940402050, Congreso Granada 42940407337, Congreso Guadalajara 42940412378, Congreso Guipúzcoa 42940417361, Congreso Huelva 42940422226, Congreso Huesca 42940427352, Congreso Jaén 42940432935, Congreso La Coruña 42940392520, Congreso Las Palmas 42940489856, Congreso León 42940437972, Congreso Lugo 42940448596, Congreso Lérida 42940443438, Congreso Madrid 42940454004, Congreso Melilla 42940578685, Congreso Murcia 42940463842, Congreso Málaga 42940458916, Congreso Navarra 42940468939, Congreso Orense 42940474219, Congreso Palencia 42940484559, Congreso Pontevedra 42940495323, Congreso Salamanca 42940500600, Congreso Santa Cruz de Tenerife 42940505848, Congreso Segovia 42940515676, Congreso Sevilla 42940520877, Congreso Soria 42940525976, Congreso Tarragona 42940531574, Congreso Teruel 42940536681, Congreso Toledo 42940542275, Congreso Valencia 42940547803, Congreso Valladolid 42940553251, Congreso Vizcaya 42940558507, Congreso Zamora 42940563499, Congreso Zaragoza 42940568653, Congreso Álava 42940320710, Congreso Ávila 42940341213.

Territorial success: Alicante,Almería,Badajoz,Baleares,Castellón,Ciudad Real,Cuenca,Cáceres,Córdoba,Gerona,Granada,Guadalajara,Guipúzcoa,La Coruña,Ávila. Cancelados sin empezar: Asturias,Burgos,Cantabria,Ceuta,Huelva,Huesca,Las Palmas,León,Lugo,Lérida,Madrid,Melilla,Murcia,Málaga,Navarra,Orense,Palencia,Pontevedra,Salamanca,Santa Cruz de Tenerife,Segovia,Sevilla,Soria,Tarragona,Teruel,Toledo,Valencia,Valladolid,Vizcaya,Zamora,Zaragoza.

## Cierre
Estado: `PARADA` (primer fallo no transitorio: Álava). Sin relanzar; hace falta diagnóstico y frase nueva. Último uso: 2026-11-11.

Frase propuesta: «Autorizo la campaña 2026-11-11_regeneracion-congreso-52-motor2-2023 tal como figura en la ficha.»
