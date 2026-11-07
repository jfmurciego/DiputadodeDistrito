# Nombres y comunidades de interés — congreso_zaragoza

Generado por `herramientas/generar_nombres_comunidades_nacional.py` 1.1.0. Sin datos electorales.

- Distritos: 8 (nombres únicos: 8)
- Reglas: MUNICIPIO 5, PRINCIPAL_Y_ENTORNO 3
- Municipios divididos entre distritos (suma por distrito): 6

## C13 partidos judiciales partidos

Fuente: Ley 38/1988, Anexo I (BOE-A-1988-29622), `configuracion/partidos_judiciales.csv`.
- Partidos tocados por la provincia: 7
- Partidos partidos entre distritos: 4
- Cobertura: 99.3% de los municipios, 99.7% de la población (sin partido: 2, listados en `configuracion/partidos_judiciales_no_conciliados.csv`).

| Partido partido | Distritos |
|---|---|
| 50-01 | 6, 7 |
| 50-03 | 0, 1, 2, 3, 4, 5, 6, 7 |
| 50-05 | 5, 7 |
| 50-07 | 5, 6, 7 |

## C13 comarcas partidas

Fuente: Aragón: 33 comarcas.
- Comarcas tocadas por la provincia: 17
- Comarcas partidas entre distritos: 6

| Comarca partida | Distritos |
|---|---|
| Campo de Cariñena | 5, 6 |
| Central | 0, 1, 2, 3, 4, 5, 6, 7 |
| Cinco Villas | 5, 7 |
| Comunidad de Calatayud | 6, 7 |
| Ribera Alta del Ebro | 5, 7 |
| Valdejalón | 5, 6, 7 |

Un municipio dividido cuenta en todos sus distritos; no se asigna población por debajo del municipio.

## Distritos

| Id | Nombre | Regla | Población | Comarcas |
|---|---|---|---|---|
| 0 | Zaragoza 5 | MUNICIPIO | 114305 | 1 |
| 1 | Zaragoza 4 | MUNICIPIO | 114172 | 1 |
| 2 | Zaragoza 3 | MUNICIPIO | 113741 | 1 |
| 3 | Zaragoza 2 | MUNICIPIO | 113865 | 1 |
| 4 | Zaragoza 1 | MUNICIPIO | 114051 | 1 |
| 5 | Zaragoza y entorno | PRINCIPAL_Y_ENTORNO | 136422 | 7 |
| 6 | Calatayud y entorno | PRINCIPAL_Y_ENTORNO | 136391 | 10 |
| 7 | Utebo y entorno | PRINCIPAL_Y_ENTORNO | 136418 | 8 |
