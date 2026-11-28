# T-478 · Indicadores por elección y sistema, 2011-2023

Herramienta: `herramientas/indicadores_sistemas.py` 1.0.0. Tablas en esta carpeta; cada fuente con su sha256 en `fuentes.csv`.
Se regenera con `python herramientas/indicadores_sistemas.py`. Sin ejecuciones, sin publicar.

## Qué se mide y cómo
- **Sistemas** (407 distritos DDD frente a las 52 circunscripciones reales): `real` (escaños oficiales del BOE por provincia),
  `mayoria_simple` (un escaño por distrito, gana el más votado) y `dv_base`, `dv_A`, `dv_B` (doble vuelta por distrito con
  `doble_vuelta.resolver`; en dv_A y dv_B la unidad es la candidatura = bloque coaligado).
- **Indicadores**: Gallagher y Loosemore-Hanby (puntos, votos frente a escaños), número efectivo de partidos en votos y en escaños
  (Laakso-Taagepera), prima al ganador (puntos de escaños sobre votos del más votado), «mayoría fabricada» (>50 % de escaños con <50 % de votos)
  y votos sin representación (% de votos a candidaturas sin escaño en su circunscripción).
- **Votos**: suma de los distritos del mapa, con el partido homologado (`alias_partidos_generales.csv`); sin voto CERA.
  **Escaños reales**: BOE, con CERA, pasados al partido homologado (`alias_siglas_boe_espejo.csv`). Los votos nacionales y los escaños reales
  no comparten exactamente el universo (CERA).
- **Mapas**: 2023 se calcula con los mapas **publicados** (`datos_abiertos/INDEX.json`, 52 territorios, 24.284.335 votos, sha256 verificado 52/52).
  2011-2019 solo existen en el **histórico** (`datos/resultados/historico/`), reagregado sobre mapas M06 *anteriores* (mismo K por provincia,
  407 en total): en 42 de 52 provincias su reparto de votos por distrito difiere del publicado. Por eso 2023 se da con los dos y la columna `mapa`
  lo etiqueta; las filas 2011-2019 son «mapa del histórico», no del publicado.
- En la doble vuelta, «votos sin representación» y la prima se miden sobre la primera vuelta (votos de la candidatura en el distrito).
  La columna `distritos_2v` cuenta los distritos decididos en segunda vuelta.

## Resultados (indicadores.csv)
| Elección | Sistema | Gallagher | L-H | NP votos | NP escaños | Ganador: % votos → % escaños | Sin representar |
|---|---|---|---|---|---|---|---|
| 2011-11 | real | 6,87 | 11,30 | 3,40 | 2,64 | PP 44,7 → 52,6 | 10,1 % |
| 2011-11 | mayoría simple | 24,23 | 35,46 | 3,40 | 1,80 | PP 44,7 → 72,7 | 51,5 % |
| 2015-12 | real | 5,86 | 10,43 | 5,09 | 4,18 | PP 28,5 → 34,6 | 10,4 % |
| 2015-12 | mayoría simple | 23,97 | 32,52 | 5,09 | 2,54 | PP 28,5 → 57,5 | 66,3 % |
| 2016-06 | real | 5,19 | 7,79 | 4,47 | 3,87 | PP 32,8 → 38,6 | 7,4 % |
| 2016-06 | mayoría simple | 28,15 | 37,06 | 4,47 | 2,06 | PP 32,8 → 67,1 | 63,0 % |
| 2019-04 | real | 5,63 | 9,61 | 5,83 | 4,82 | PSOE 28,9 → 35,1 | 10,0 % |
| 2019-04 | mayoría simple | 38,26 | 55,65 | 5,83 | 1,66 | PSOE 28,9 → 76,7 | 69,1 % |
| 2019-11 | real | 6,46 | 11,42 | 5,83 | 4,59 | PSOE 28,3 → 34,3 | 10,7 % |
| 2019-11 | mayoría simple | 27,99 | 41,71 | 5,83 | 2,30 | PSOE 28,3 → 62,7 | 68,7 % |
| 2023-07 (publicado) | real | 5,65 | 9,61 | 4,08 | 3,44 | PP 33,3 → 39,1 | 7,8 % |
| 2023-07 (publicado) | mayoría simple | 21,90 | 31,95 | 4,08 | 2,05 | PP 33,3 → 57,5 | 61,4 % |
| 2023-07 (publicado) | dv_base | 20,38 | 29,60 | 4,08 | 2,21 | PP 33,3 → 55,3 | 62,0 % |
| 2023-07 (publicado) | dv_A | 7,87 | 9,23 | 2,40 | 2,18 | Derecha nacional 46,1 → 55,3 | 46,2 % |
| 2023-07 (publicado) | dv_B | 7,78 | 10,51 | 2,43 | 2,19 | Derecha nacional 46,1 → 55,3 | 47,4 % |

Las filas de doble vuelta de las demás elecciones, y 2023 con el histórico, están en `indicadores.csv`. Hechos que se leen directamente:
- El sistema real da un Gallagher de 5-7 puntos en las seis elecciones; con un escaño por distrito sube a 22-38 en el mismo mapa.
- La mayoría simple de distrito produce «mayoría fabricada» en todas las elecciones; el real solo en 2011 (PP 44,7 % → 52,6 %).
- dv_A y dv_B (coaliciones por bloque) bajan el Gallagher a 8-9 puntos en 2019-11 y 2023-07, pero con **dos candidaturas efectivas** (NP en votos 2,4-3,0):
  la unidad ya no es el partido y no es comparable con el real partido a partido. En 2015-12 y 2016-06 dv_base da primas negativas
  (el más votado en primera vuelta pierde escaños por los trasvases dentro de su bloque).
- 2023, mapa publicado: mayoría simple da PP 234, PSOE 161 y 12 distritos de otros (EH Bildu 6, EAJ-PNV 5, Junts 1). Con el histórico la diferencia es de unos pocos distritos (columna `mapa`).

## Desigualdad territorial (desigualdad_territorial.csv)
Loosemore-Hanby (puntos) de escaños reales por provincia, y de distritos DDD por provincia, frente a la población de la provincia:
| Base | Escaños reales (350) | Distritos DDD (407) |
|---|---|---|
| Población 2022-01-01 (RD 1037/2022) | 10,52 | 1,99 |
| Población 2025-01-01 | 11,02 | 1,68 |
| Censo de la elección 2023 (mapa publicado) | 9,89 | 4,14 |

## Comprobaciones de la auditoría
1. **«PP 33 %» (2023)**: coincide con el % de **votos** del PP (33,33 % sobre 24.284.335 votos de los distritos). No es % de escaños (39,1 % real; 57,5 % de distritos en mayoría simple).
2. **«207 de 325 en 49 provincias»**: viene de `dashboard/hemiciclo.json`, vetado y fuera de git. **No es reproducible** y no se ha reconstruido.
   Con los mapas publicados y mayoría simple sobre 407 distritos, el PP gana 234.
3. **«10,7 % → 1,9 %»**: la auditoría usa «padrón 2023», que no está en git. Con 2022 da 10,52 → 1,99; con 2025, 11,02 → 1,68. Misma magnitud, no la misma cifra: no se declara confirmada.

## Límites
- Desajuste de secciones del mapa publicado sobre el tope del 0,5 %: Badajoz 0,87 %, Valencia 0,77 %, Albacete 0,63 % y Almería 0,52 % (`desajustes_publicado.csv`). Los votos de esas provincias llevan ese error.
- Los escaños reales y los votos no comparten universo (CERA); los coaligados oficiales («PP-PAR», «PP-EU», «UPN-PP»…) se suman al partido homologado que fije la tabla de alias, con su aviso «coaliciones: no comparables entre elecciones».
- Los bloques (dv_A, dv_B) son los de la tabla D-167 del 25-11; otro reparto de bloques cambia esas filas.
- Ninguna cifra viene de memoria: todo sale de los ficheros de `fuentes.csv`.
