# T-83 paso A · Diseño: histórico 2011-2023 por M07/M08 (D-10, D-12)

VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: aprobado por el Coordinador (08-11) · ANTERIOR: ninguna (fichero nuevo)

## 1. Qué consume M07 hoy
- `--params` del territorio. Bloque `modulo_07_agregar_resultados_electorales`: `in_geojson` (secciones M06,
  `CUSEC_KEY`→`district_id`), `election_contract`, salidas `out_district_party_csv`, `out_district_summary_csv`,
  `out_reconciliation_report` y, opcional, `out_sections_enriched_geojson`.
- El contrato electoral (`ddd_core.electoral_contract`): `election_id`, `sources[]` con adaptador (`long_csv`
  sección/partido/votos, `wide_polling_station_csv`, `nested_json`), diccionario de partidos,
  `source_verification.official_candidate_votes`, `reconciliation`, `non_geocodable_votes`; más la excepción de
  pérdida por elección de `configuracion/excepciones_reconciliacion_electoral_2025.yaml`.
- En 2023 el contrato lo materializa la 03 (`READY_PACKAGE` → `materializar_contrato_electoral_runtime.py`) y M07/M08
  corren dentro de la 00/04.

## 2. Propuesta: B emite un paquete M07; M07/M08 sin cambios
1. `herramientas/reagregacion_historico.py` 1.1.0 (legacy 1.0.0): opción `--paquete DIR` que, tras el paso (2) de B
   (votos llevados a la sección vigente con T-85, peso D-13), escribe por provincia y elección:
   - `secciones.csv` long `section_id,party,votes` sobre el `CUSEC_KEY` vigente; enteros por mayor resto por partido
     (el total provincial no cambia; mismo cuadre exacto que B);
   - `contrato.yaml` con `election_id=congreso_<p>_<AAAA-MM-DD>`, adaptador `long_csv`, partidos con las siglas tal cual
     (homologación de 2019 vía `HOMOLOGACION_2019`), `source_verification.official_candidate_votes` = Infoelectoral/BOE
     donde hay y `non_geocodable_votes` = CERA (oficial − espejo), con sha256 del espejo, de la tabla T-85 y del M06;
   - `participacion.csv` (censo, votantes por distrito): M07 solo agrega votos; censo y votantes salen de B.
2. Herramienta nueva `herramientas/historico_m07m08.py` 1.0.0: params temporal en `territorios/<t>/config/` que apunta
   al M06 vigente (blob canónico, sha256 contra `datos_abiertos/INDEX.json`) y al contrato del paquete, y ejecuta
   `modulos/07_…` y `modulos/08_…` tal cual. Sin M01-M06: no hay M04/M05 ni checkpoints.
3. La asignación sección→distrito pasa a ser la del M06 (exacta), no el «mayor solape» de B: un test compara ambos
   (deben coincidir; si no, se informa la diferencia por distrito).

## 3. Ficheros que toca
- Compartidos (`herramientas/`): `reagregacion_historico.py` (sube versión) y uno nuevo. Nada en `modulos/`,
  `ddd_core/`, workflows, catálogo, política ni contratos de producción `territorios/*/config/*_2025.yaml`.
- Duda para el Coordinador: si M07 rechaza la pérdida CERA con `non_geocodable_votes`, la alternativa es una entrada
  por elección en `excepciones_reconciliacion_electoral_2025.yaml` (configuración compartida): lo aviso antes.
- Tests `tests/test_t83a_historico_m07.py` (sintético: 2 distritos, sección partida, CERA) y registro.

## 4. Qué invalida
- Nada de M04/M05/M06: ni huellas M05, ni checkpoints, ni el par 2023 (`election_id` distinto; no cambia
  `TERRITORIAL_READY_PAIR`). No hace falta ninguna 00.
- El producto histórico queda atado al sha256 del M06: si cambia el M06, se regenera (mismo criterio que el par).

## 5. Salida (visor T-84)
`datos/resultados/historico/<AAAAMM>/<t>/`: `district_party.csv` y `district_summary.csv` de M07, M08 (ganador por
distrito), `participacion.csv`, informe de reconciliación y `MANIFEST.json` con huellas. Capas T-84: ganador = M08;
participación = `participacion.csv`; rotación = cambio de ganador entre elecciones consecutivas, `rotacion.csv`
derivado por distrito; por sección, `out_sections_enriched_geojson` (opcional, pesado: para PMTiles).

## 6. Puerta 04
Aquí se genera fuera de línea. La 04 (`incorporacion-resultados-electorales.yml`) queda solo para publicar, una elección
por universo, lanzada por el Operador con permiso del propietario; adaptarla para leer este paquete es otra tarea
(workflow compartido), no esta PR.

## 7. Pruebas
Test sintético; suite local de M07/M08, gobernanza y contratos; ejecución local en Álava, Badajoz y Huesca × 6
elecciones con cuadre: votos M07 = votos B = espejo, defecto frente a la oficial = CERA.

## 8. Ajustes al implementar
- No hay M06 de secciones publicado: la asignación exacta sale de `datos/composicion/<t>.csv`; las secciones 2025
  recodificadas frente al M06 (6 en Badajoz, 1 en Huesca) van al distrito de mayor solape, como en B.
- `official_candidate_votes` no se declara: la oficial versionada solo trae las candidaturas con escaño. El contraste
  partido a partido sigue en el manifiesto de B. CERA no necesita excepción: M07 no lo imputa a DDD.
