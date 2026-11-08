# T-85 · Equivalencia de seccionados INE históricos con el vigente 2025

Fecha: 2026-11-08. Herramienta: `herramientas/equivalencia_seccionados.py` 1.0.0. Datos: `informe.json` (fuentes con sha256).
Decisiones: D-9, D-10 y D-11 (6 generales 2011-2023 sobre los distritos vigentes) y D-13 (peso por población; el área solo si falta).

## Fuentes
- Vigente: seccionado INE 2025 (`inputs/partes/seccionado_2025.zip`, sha256 `55c9da7e…`) y padrón 2025 por sección (INE 65034, `91d3ff9a…`).
- Históricos: cartografía INE detallada `www.ine.es/prodyser/cartografia/seccionado_{2012,2015,2016,2019,2020,2024}.zip`
  (sha256 en `informe.json`). La geometría del espejo T-89 está simplificada: frente al INE 2025 da en Madrid 2024
  1 592 de 4 473 secciones bajo el 95 % de solape, así que no se usa para la equivalencia.
- Votos y censo por sección: espejo T-89 (`data/<elección>/sekzioa/<cpro>.json`, huellas en `orchestracion/fuente_nazioenbehatokia.json`).

## Método
- 1:1 si ≥ 95 % del área de la sección histórica cae en una vigente y esa vigente procede en ≥ 95 % de ella.
- Si no, reparto: población `a(h∩v)/a(v)·pob2025(v)` normalizado (D-13); área `a(h∩v)/a(h)` solo si la población es 0.
- Astillas < 1 % del área histórica descartadas. Traslación sistemática ≥ 20 m corregida: solo Melilla 2012 (63 m en Y).
- Secciones con votos que no están en el seccionado de su año: geometría del seccionado más cercano (≤ 0,05 % de los votos).

## Resultado nacional (% de votos a candidaturas)

| Elección | Seccionado | No 1:1 | Cambian de sección área↔población | Sin geometría |
|---|---|---|---|---|
| 2011-11 | 2012 | 23,32 | 2,66 | 0,02 |
| 2015-12 | 2015 | 12,41 | 1,41 | 0,00 |
| 2016-06 | 2016 | 11,34 | 1,31 | 0,00 |
| 2019-04 | 2019 | 6,39 | 0,83 | 0,00 |
| 2019-11 | 2020 | 5,91 | 0,79 | 0,00 |
| 2023-07 | 2024 | 1,63 | 0,23 | 0,00 |

Ningún voto queda sin sección vigente.

## Prueba del censo (área frente a población)
El censo de cada elección se lleva al vigente con los dos pesos y se compara con el censo real de 2023 en las secciones
vigentes que reciben reparto (total escalado para quitar el crecimiento). Error ponderado nacional:

| Elección | Error área | Error población | Provincias en que gana población |
|---|---|---|---|
| 2011-11 | 31,06 % | 21,95 % | 51 / 52 |
| 2015-12 | 28,41 % | 18,37 % | 47 / 51 |
| 2016-06 | 28,80 % | 18,15 % | 44 / 51 |
| 2019-04 | 31,41 % | 17,88 % | 42 / 51 |
| 2019-11 | 32,05 % | 17,98 % | 38 / 48 |

Gana la población, lo que confirma la D-13. El área gana en Palencia 2011 (35 secciones), Salamanca (8-10), Soria (3),
Jaén, Lugo, Teruel, León, Córdoba 2016 y Orense 2015 (menos de 1 punto salvo Salamanca, Soria y Jaén); en Ávila, Zamora,
Lérida y Segovia empatan (una sola vigente por reparto). Limitación:
el peso usa el padrón 2025, que se parece al censo de 2023 de la referencia; la prueba favorece algo a la población.

## % de votos que no queda 1:1, por provincia (código INE) y elección
| Prov. | 201111 | 201512 | 201606 | 201904 | 201911 | 202307 |
|---|---|---|---|---|---|---|
| 01 | 36.7 | 23.6 | 23.5 | 2.0 | 0.9 | 0.9 |
| 02 | 21.8 | 9.3 | 5.9 | 2.2 | 2.2 | 0.0 |
| 03 | 17.1 | 9.6 | 7.8 | 6.6 | 6.7 | 0.3 |
| 04 | 37.8 | 16.6 | 14.5 | 11.6 | 11.7 | 5.8 |
| 05 | 14.9 | 10.0 | 7.3 | 7.4 | 4.9 | 1.0 |
| 06 | 51.4 | 12.5 | 6.1 | 4.2 | 4.1 | 1.5 |
| 07 | 15.3 | 6.9 | 6.6 | 3.6 | 3.6 | 0.8 |
| 08 | 18.1 | 10.1 | 9.9 | 4.9 | 3.7 | 0.1 |
| 09 | 41.5 | 18.8 | 15.5 | 12.2 | 11.5 | 7.7 |
| 10 | 11.3 | 8.2 | 7.6 | 6.7 | 6.7 | 0.3 |
| 11 | 23.8 | 17.5 | 17.3 | 3.3 | 2.9 | 1.1 |
| 12 | 20.0 | 8.0 | 7.7 | 3.2 | 3.1 | 2.0 |
| 13 | 9.7 | 6.3 | 6.1 | 4.3 | 4.3 | 0.6 |
| 14 | 28.7 | 18.2 | 17.1 | 10.3 | 9.2 | 0.6 |
| 15 | 22.9 | 13.7 | 13.2 | 8.9 | 5.1 | 0.5 |
| 16 | 5.1 | 2.0 | 1.9 | 2.1 | 2.1 | 0.0 |
| 17 | 28.5 | 12.7 | 8.0 | 2.8 | 2.7 | 0.0 |
| 18 | 26.9 | 19.2 | 16.3 | 7.8 | 7.3 | 0.4 |
| 19 | 36.1 | 15.7 | 15.0 | 13.6 | 13.7 | 3.9 |
| 20 | 25.6 | 5.9 | 5.7 | 3.2 | 3.2 | 0.3 |
| 21 | 34.7 | 20.0 | 20.3 | 4.0 | 4.0 | 0.5 |
| 22 | 14.1 | 1.6 | 1.7 | 1.2 | 0.0 | 0.0 |
| 23 | 27.4 | 13.8 | 8.8 | 5.3 | 5.3 | 3.6 |
| 24 | 25.5 | 19.4 | 18.6 | 11.7 | 5.8 | 1.3 |
| 25 | 8.0 | 5.9 | 5.0 | 3.7 | 3.6 | 3.8 |
| 26 | 17.0 | 12.9 | 13.0 | 6.5 | 6.4 | 4.1 |
| 27 | 24.2 | 11.6 | 6.9 | 4.1 | 3.0 | 1.9 |
| 28 | 17.0 | 10.1 | 10.2 | 6.6 | 6.7 | 1.9 |
| 29 | 39.7 | 21.5 | 16.9 | 8.8 | 8.3 | 1.4 |
| 30 | 21.9 | 8.1 | 6.8 | 3.9 | 3.7 | 1.6 |
| 31 | 6.6 | 7.0 | 7.0 | 7.3 | 7.4 | 1.4 |
| 32 | 26.5 | 11.2 | 11.4 | 5.7 | 4.2 | 0.4 |
| 33 | 24.3 | 12.6 | 11.3 | 5.8 | 5.7 | 1.2 |
| 34 | 27.0 | 17.0 | 16.7 | 11.0 | 11.1 | 5.9 |
| 35 | 15.6 | 8.5 | 8.5 | 5.5 | 5.3 | 1.9 |
| 36 | 43.4 | 17.2 | 11.8 | 8.5 | 8.5 | 0.2 |
| 37 | 18.0 | 4.9 | 4.8 | 4.7 | 4.7 | 1.7 |
| 38 | 21.7 | 12.6 | 12.6 | 4.2 | 4.1 | 1.4 |
| 39 | 38.3 | 11.8 | 11.4 | 10.2 | 9.7 | 6.2 |
| 40 | 24.5 | 14.4 | 4.8 | 4.1 | 4.1 | 3.6 |
| 41 | 40.9 | 20.6 | 20.4 | 3.7 | 3.6 | 0.6 |
| 42 | 6.7 | 6.0 | 4.1 | 4.2 | 4.3 | 0.0 |
| 43 | 26.5 | 15.5 | 15.0 | 12.6 | 12.6 | 12.8 |
| 44 | 29.3 | 10.3 | 10.0 | 6.1 | 4.9 | 2.4 |
| 45 | 30.7 | 19.2 | 19.1 | 5.5 | 5.5 | 0.6 |
| 46 | 17.3 | 13.4 | 13.1 | 11.5 | 11.5 | 3.3 |
| 47 | 19.3 | 7.6 | 7.6 | 4.1 | 4.2 | 0.8 |
| 48 | 17.1 | 9.2 | 7.5 | 4.7 | 4.7 | 1.4 |
| 49 | 11.3 | 5.0 | 4.9 | 5.1 | 4.5 | 3.7 |
| 50 | 20.0 | 12.5 | 11.3 | 9.5 | 8.3 | 1.3 |
| 51 | 49.5 | 48.6 | 48.7 | 23.7 | 0.0 | 0.0 |
| 52 | 41.6 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

Badajoz 2011 (51 %) y Ceuta 2015-2016 (49 %) son cambios reales del seccionado (secciones de 2012 con término rural que
el INE separó después), no desplazamientos. Las tablas de equivalencia (sección histórica → vigente, con los dos pesos;
11 MB) no se versionan: se regeneran con la orden de la cabecera a partir de las fuentes con sha256.
