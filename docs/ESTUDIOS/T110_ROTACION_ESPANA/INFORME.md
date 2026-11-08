# T-110 · Histórico de generales 2011-2023 sobre los distritos vigentes (49 provincias con M06)

VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)

Salida: `datos/resultados/historico/<elección>/congreso_<t>.csv` (+ `_partidos.csv`), `MANIFEST.json` (sha256 de cada fuente)
y `rotacion/congreso_<t>.csv` (ganador homologado por elección y nº de cambios; homologación T-97 + D-20, se suman las
siglas de la misma familia antes de elegir ganador). Generado con `reagregacion_historico.py --lote` 1.2.0 (peso por
población, D-13). Cuadre completo: `cuadre.json` (por provincia × elección y lista `no_cuadra`).
Fuentes: espejo T-89 (`orchestracion/fuente_nazioenbehatokia.json`), seccionados INE 2012-2024 y 2025 y padrón 65034 (sha256
en `docs/AUDITORIAS/T85_EQUIVALENCIA_SECCIONADOS/informe.json`, todos verificados), M06 de `datos_abiertos/INDEX.json`
(sha256 verificado), Infoelectoral 2023 (`02202307_MESA.zip`, release `fuente-infoelectoral-02202307`, sha256 en `cuadre.json`).

## Resultado
- 49 territorios × 6 elecciones = 294 reagregaciones: 0 secciones vigentes sin distrito, diferencia 0 votos entre
  distritos + perdidos y el espejo (partido a partido), 0 errores frente al BOE (2019-11 y 2023: 104 provincia-elección,
  453 partidos comparados), 0 siglas sin homologar, ganador de 2023 idéntico al M08 versionado en los 49 territorios.
- Espejo (Observatorio) frente a Infoelectoral 2023, 52 provincias: igual al voto que las mesas sin CERA (diferencia 0 en
  todas); frente al total provincial de Infoelectoral falta solo el CERA (0,27 %-3,08 %).
- Peso no 1:1 (T-85): el reparto por población afecta al 23,3 % de los votos en 2011 y al 1,6 % en 2023.

## Lo que no cuadra (7 incidencias; detalle en `cuadre.json`)
| Qué | Motivo |
|---|---|
| Alicante (03), Barcelona (08), Málaga (29): sin reagregación | No hay producto M06 publicado (49/52). El espejo sí cuadra con Infoelectoral. Se completan al publicar su M06 y relanzar `--lote`. |
| León, Lugo, Orense y Asturias, 2011: 807, 1.128, 399 y 1.541 votos perdidos (0,20-0,54 %) | Secciones del espejo sin geometría en el seccionado INE 2012 (comprobado en Orense: 1 sección, 3208601002). Se informan, no se reparten. Lugo supera por poco el 0,5 % de D-17 (criterio de las archivistas, no de B). |

Límites: el espejo no trae el voto CERA (sin repartir a distritos); 2011-2019-04 no tienen oficial local por candidatura,
solo el contraste con el espejo; los ficheros BOE solo traen candidaturas con escaño.
