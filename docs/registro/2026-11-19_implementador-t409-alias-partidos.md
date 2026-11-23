## 2026-11-19 — T-409 — Tabla de alias de partidos (id de fuente → partido homologado) y `--alias` en la doble vuelta

Causa: los ids de partido de P31 no son las siglas homologadas de la tabla de bloques (entre el 16 % y el 54 % de los votos sin casar,
#911). Orden del Planificador: derivar la tabla de la homologación existente y declarar los restos.
Cambio: `herramientas/alias_partidos_generales.py` (`generar`/`comprobar`) deriva, por elección y con prioridad, de
`homologacion_siglas_generales.csv` (sigla_fuente), `reglas_generales.json` (`interior`), `alias_siglas_boe_espejo.csv` (sigla del BOE por
el espejo) e identidad; un id con dos partidos va a conflictos, no a la tabla. Ficheros: `configuracion/alias_partidos_generales.csv`
(555 filas, con origen y fuente), `_pendientes.csv` y `.json` (huellas de las fuentes y cobertura de votos). `doble_vuelta.py` 1.3.0
(copia 1.2.0 en `legacy/`): `--alias` pasa cada id a su partido homologado antes del bloque; sin él nada cambia.
Cobertura (votos): 100 % en las salidas M07 históricas de las 6 elecciones y en los CSV del BOE de 2015-12 a 2023; 2011-11 BOE 92,74 %:
resto declarado = «LA IZQUIERDA PLURAL» (conflicto CHA-IU | IU según provincia; ambos Izquierdas en la tabla de bloques, sin efecto en el
bloque). Pruebas: `test_t409_alias_partidos.py` (tabla = lo derivado hoy, un id un partido, valores de las fuentes, todo partido existe en
la tabla de bloques, resto declarado, conflicto sintético, `--alias`) y 19 de la doble vuelta. Sin tocar workflows ni `modulos/`; el
`--alias` en el paso de P30 va con los ajustes de #911. `no-automerge`.
