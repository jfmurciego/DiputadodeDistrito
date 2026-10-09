# CYL-01 — Inventario de fuentes para Castilla y León

**Fecha:** 2026-09-11
**Estado:** fuentes base y correspondencia CUSEC validadas en diagnóstico; pendiente de aceptación reproducible en GitHub

## Objetivo
Confirmar si las fuentes nacionales ya disponibles permiten construir M01 para Castilla y León sin incorporar nuevas fuentes externas.

## Fuente geométrica

`inputs/seccionado_2025.zip` contiene el shapefile nacional `SECC_CE_20250101`, CRS **EPSG:25830**, con `CUSEC`, `CUMUN`, `CPRO`, `NMUN` y demás campos territoriales requeridos.

| CPRO | Provincia | Secciones |
|---|---|---:|
| 05 | Ávila | 308 |
| 09 | Burgos | 577 |
| 24 | León | 444 |
| 34 | Palencia | 273 |
| 37 | Salamanca | 530 |
| 40 | Segovia | 276 |
| 42 | Soria | 218 |
| 47 | Valladolid | 565 |
| 49 | Zamora | 315 |
| **Total** | **Castilla y León** | **3.506** |

Los 3.506 CUSEC geométricos son únicos y no nulos.

## Fuente de población

`inputs/65034.csv.zip` contiene `65034.csv`, fuente nacional tabulada. Filtro aplicado, idéntico en semántica al de Aragón:
- `Periodo = 2025`;
- `Sexo = Total`;
- `Edad = Todas las edades`;
- sección no nula;
- provincias 05, 09, 24, 34, 37, 40, 42, 47 y 49.

Tras leer correctamente el fichero como tabulado y normalizar `Secciones` a CUSEC de diez dígitos, el resultado es **3.506 CUSEC únicos**, exactamente los mismos que en la geometría.

No existen:
- `geometry_only`: 0;
- `population_only`: 0;
- duplicados CUSEC: 0;
- población ausente tras el join: 0.

## Población 2025 reconciliada

| Provincia | Población |
|---|---:|
| Ávila | 160.738 |
| Burgos | 362.663 |
| León | 448.030 |
| Palencia | 158.702 |
| Salamanca | 328.446 |
| Segovia | 158.251 |
| Soria | 90.183 |
| Valladolid | 528.644 |
| Zamora | 165.564 |
| **Castilla y León** | **2.401.221** |

## Resolución de la aparente discrepancia inicial

El conteo previo de 3.555 no representaba CUSEC reconciliados y no debe conservarse como anomalía territorial. Al aplicar la misma lógica de lectura y normalización que M01, población y geometría forman una correspondencia **1:1 de 3.506 secciones**.

Por tanto, no se necesita una excepción Castilla y León ni una regla de descarte.

## Decisión CYL-01

Las fuentes base nacionales actuales son suficientes para M01. La configuración territorial v0.3.0 usa las fuentes compartidas del repositorio y escribe sus productos dentro de `territorios/castilla_y_leon/`.

## Criterio de aceptación M01 en GitHub

La ejecución reproducible debe demostrar simultáneamente:
- `rows_out = 3506`;
- `missing_population_rows = 0`;
- población total = `2.401.221`;
- nueve provincias exactas;
- CUSEC único y no nulo.

Solo entonces CYL-01/M01 se promociona y se abre M02/M03.
