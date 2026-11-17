# T-399 · Secciones del seccionado del año sin población en la tabla (D-126/D-128)

**Regla del Planificador (17-11), pendiente de confirmar por el propietario** (PR con `no-automerge`). Herramienta `herramientas/contrato_historico_epoca.py` 1.2.0, contratos 1.3.0.

Caso contrario al de D-153: secciones que el seccionado del año tiene y la tabla de población no (2011-11: el Censo 2011 no las trae; 105 en 29 provincias, p. ej. 0804703001).

1. Valor de la misma sección en el año más cercano del Atlas 30832 con dato entero (empate: el anterior; «.», «..» y `""` no son dato). Para 2011-11 es 2015 en las 103 con dato.
2. Ajuste proporcional al total municipal del Censo 2011 (D-128): residuo = total municipal − suma de las secciones con dato; con residuo > 0 las rellenadas se reescalan a él (restos mayores); con residuo ≤ 0 conservan el valor del Atlas (`sin_ajuste_municipal`, nunca 0).
3. Origen `rellenada_año_cercano`: cuenta como estimada en el umbral del 1 % (D-126).
4. Sin dato en ningún año (0804703001, 3605901003): la provincia queda BLOQUEADA_SIN_DATO (no se inventa).
5. `materializar` solo aplica lo declarado en el contrato (`provincias.<c>.poblacion.sin_poblacion_resuelto`) y falla cerrado si difiere.

Informes (derivados de los contratos: `informe_poblacion`): `informe_provincias.csv` y `cuadre_municipal.csv`.

## Resultado en 2011-11 (fuentes con sha256 de T-357/T-364; las 5 tablas reproducen los sha256 de los contratos 1.2.0)
- 103 secciones rellenadas en 60 municipios (142.996 hab. según el Atlas, 142.842 tras el ajuste: solo 35016 se ajusta), 2 sin dato.
- `materializar`: 48 de 52 provincias OK (antes 2). No materializan: 08 y 36 (sin dato → BLOQUEADA_SIN_DATO), 51 (Melilla, 1,83 % → BLOQUEADA_RELLENO) y 35 (`PUENTE_FUERA_DEL_SECCIONADO`: el puente de La Graciosa, 3502401010, no está en el seccionado 2012; causa distinta, fuera de T-399).
- **Hallazgo para el propietario:** el total municipal del Censo 2011 coincide con la suma de la tabla en 57 de los 60 municipios (residuo 0; 2 más tienen una sección sin dato): el ajuste a ese total no actúa y las rellenadas se SUMAN al total (exceso 141.842 hab.; p. ej. 08205: 19.429 sobre 84.285). Si las secciones nuevas de 2012 parten secciones del Censo, hay doble cómputo; la alternativa coherente sería repartir el municipio entre ambas, o no rellenar.
- Las otras 4 elecciones solo cambian de versión y regla.
