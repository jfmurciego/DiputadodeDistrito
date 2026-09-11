# CYL-01 — Inventario de fuentes para Castilla y León

**Fecha:** 2026-09-11
**Estado:** evidencia inicial confirmada; unión población↔geometría pendiente de auditoría

## Objetivo
Confirmar si las fuentes nacionales ya disponibles en el proyecto permiten construir M01 para Castilla y León sin incorporar todavía nuevas fuentes externas.

## Fuente geométrica

Fuente disponible: `inputs/seccionado_2025.zip`.

Contenido inspeccionado: shapefile nacional `SECC_CE_20250101` con campos `CUSEC`, `CUMUN`, `CSEC`, `CDIS`, `CMUN`, `CPRO`, `CCA`, `CUDIS`, `NPRO`, `NCA`, `NMUN` y geometría.

CRS observado: **EPSG:25830**.

Castilla y León aparece completa bajo los códigos provinciales INE:

| CPRO | Provincia | Secciones geométricas |
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

## Fuente de población

Fuente disponible: `inputs/65034.csv.zip`, fichero `65034.csv` nacional tabulado.

Campos observados: `Total Nacional`, `Provincias`, `Municipios`, `Secciones`, `Sexo`, `Edad`, `Periodo`, `Total`.

Filtro equivalente al utilizado en Aragón para el universo de población:
- `Periodo = 2025`;
- `Sexo = Total`;
- `Edad = Todas las edades`;
- sección no nula.

Filas observadas para las nueve provincias:

| CPRO | Filas de sección en población | Población agregada de esas filas |
|---|---:|---:|
| 05 | 312 | 160.738 |
| 09 | 591 | 362.663 |
| 24 | 451 | 448.030 |
| 34 | 279 | 158.702 |
| 37 | 535 | 328.446 |
| 40 | 278 | 158.251 |
| 42 | 218 | 90.183 |
| 47 | 572 | 528.644 |
| 49 | 319 | 165.564 |

## Hallazgo crítico antes de M01

La fuente geométrica contiene **3.506 secciones**, mientras que la extracción de población devuelve **3.555 filas de sección** para el mismo año/filtro.

La diferencia bruta es de **49 filas adicionales en población** respecto del número de geometrías. Esto no debe resolverse descartando filas silenciosamente ni asumiendo que son duplicados válidos. Antes de aceptar M01 hay que clasificar la diferencia:

1. extraer el CUSEC de diez dígitos de `Secciones`;
2. comprobar unicidad del identificador en la tabla filtrada;
3. comparar conjuntos `CUSEC_geometría` y `CUSEC_población`;
4. identificar `population_only`, `geometry_only` y duplicados;
5. documentar la causa: cambios de seccionado, códigos históricos, duplicidad estadística u otra causa;
6. solo después decidir una regla de unión explícita.

## Conclusión CYL-01 parcial

**No hace falta buscar nuevas fuentes base para arrancar Castilla y León.** Las dos fuentes principales ya son nacionales y contienen las nueve provincias.

El siguiente bloqueo real no es la disponibilidad de datos, sino reconciliar de forma auditable los identificadores de sección entre geometría y población.

## Próximo paso

Crear una auditoría reutilizable de correspondencia de secciones que pueda ejecutarse para cualquier territorio antes de M01. Debe producir conteos y listados de diferencias, y fallar si existe una pérdida no explicada.