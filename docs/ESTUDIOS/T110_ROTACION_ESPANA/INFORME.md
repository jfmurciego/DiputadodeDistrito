# T-110 · Histórico de generales 2011-2023 sobre los distritos vigentes (52 provincias)

VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)

Salida: `datos/resultados/historico/<elección>/congreso_<t>.csv` (+ `_partidos.csv`), `MANIFEST.json` (sha256 de cada fuente)
y `rotacion/congreso_<t>.csv` (ganador homologado por elección y nº de cambios; homologación T-97 + D-20, se suman las
siglas de la misma familia antes de elegir ganador). Generado con `reagregacion_historico.py --lote` 1.2.0 (peso por
población, D-13). Cuadre completo: `cuadre.json` (por provincia × elección y lista `no_cuadra`).
Fuentes: espejo T-89 (`orchestracion/fuente_nazioenbehatokia.json`), seccionados INE 2012-2024 y 2025 y padrón 65034 (sha256
en `docs/AUDITORIAS/T85_EQUIVALENCIA_SECCIONADOS/informe.json`, todos verificados), M06 de `datos_abiertos/INDEX.json`
(sha256 verificado; Alicante, Barcelona y Málaga, del `canonical_m06` de `orchestracion/publicaciones_visor.json`, blob con sha256 verificado), Infoelectoral 2023 (`02202307_MESA.zip`, release `fuente-infoelectoral-02202307`, sha256 en `cuadre.json`).

## Resultado
- 52 territorios × 6 elecciones = 312 reagregaciones: 0 secciones vigentes sin distrito, diferencia 0 votos entre
  distritos + perdidos y el espejo (partido a partido), 0 errores frente al BOE (2019-11 y 2023: 104 provincia-elección,
  453 partidos comparados), 0 siglas sin homologar, ganador de 2023 idéntico al M08 versionado en los 49 territorios que lo tienen.
- Espejo (Observatorio) frente a Infoelectoral 2023, 52 provincias: igual al voto que las mesas sin CERA (diferencia 0 en
  todas); frente al total provincial de Infoelectoral falta solo el CERA (0,27 %-3,08 %).
- Peso no 1:1 (T-85): el reparto por población afecta al 23,3 % de los votos en 2011 y al 1,6 % en 2023.

## Lo que no cuadra (5 incidencias, todas de 2011; detalle en `cuadre.json`)
| Provincia | Votos perdidos | % | Secciones del espejo sin geometría en el seccionado INE 2012 |
|---|---|---|---|
| Alicante (03) | 1.877 | 0,21 | 5 (0301407021, 0301405021, 0303101016, 0306503022, 0301408020) |
| León (24) | 807 | 0,28 | 1 (2408905012) |
| Lugo (27) | 1.128 | 0,54 | 3 (2701501005, 2703401002, 2706001004) |
| Orense (32) | 399 | 0,20 | 1 (3208601002) |
| Asturias (33) | 1.541 | 0,25 | 3 (3301901003, 3304404017, 3301103001) |

Ninguna de esas 13 secciones existe en el seccionado 2025 (no hay 1:1 por código), pero sus municipios sí tienen secciones vigentes.
Se informan, no se reparten. **Propuesta de tratamiento (la decide el Coordinador/propietario, incluido el tope):** repartir esos votos entre las
secciones vigentes de su municipio (primeros 5 dígitos del código) con el peso de población de D-13, como hace D-17, y
listarlas en la evidencia. Con el tope de D-17 (0,5 % de los votos de la provincia) entrarían todas menos Lugo (0,54 %).
Efecto en la rotación: ninguno apreciable (≤ 0,54 % de una provincia en 2011).

Límites: el espejo no trae el voto CERA (sin repartir a distritos); 2011-2019-04 no tienen oficial local por candidatura,
solo el contraste con el espejo; los ficheros BOE solo traen candidaturas con escaño.
