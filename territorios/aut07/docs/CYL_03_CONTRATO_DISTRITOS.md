# CYL-03 — Contrato de número de distritos y reparto provincial

**Fecha:** 2026-09-11
**Estado:** decisión de diseño adoptada; límites poblacionales finos todavía pendientes

## 1. Número total de distritos

La XII Legislatura de las Cortes de Castilla y León, constituida en 2026, tiene **82 procuradores**. El proyecto DDD conserva el tamaño de la cámara y transforma la representación en **82 distritos uninominales**.

Por tanto:

`k_districts = 82`

Fuente institucional: Decreto 1/2026 de convocatoria, reproducido en el Diario de Sesiones de las Cortes de Castilla y León de 14/04/2026, que fija 82 procuradores.

## 2. La provincia sigue siendo barrera

Cada distrito debe estar íntegramente dentro de una sola provincia. Los puentes topológicos CYL-02 permiten representar enclaves/exclaves sin romper esta regla.

## 3. El reparto provincial oficial NO se copia

El sistema electoral autonómico vigente distribuye los 82 procuradores con una regla legal propia (mínimo provincial y escalones de población). Esa regla produce 7/11/13/7/10/7/5/15/7.

DDD persigue igualdad poblacional entre representantes. Por ello, igual que en Aragón, el reparto entre provincias se calcula por **Hamilton sobre población de referencia**, manteniendo K total y provincia infranqueable.

Población DDD 2025 validada: **2.401.221**.
Target regional teórico: `2.401.221 / 82 = 29.283,183` habitantes por distrito.

## 4. Reparto Hamilton DDD

| Provincia | Población 2025 | Cuota teórica | Distritos DDD | Target provincial |
|---|---:|---:|---:|---:|
| Ávila | 160.738 | 5,489 | **6** | 26.789,7 |
| Burgos | 362.663 | 12,385 | **12** | 30.221,9 |
| León | 448.030 | 15,300 | **15** | 29.868,7 |
| Palencia | 158.702 | 5,420 | **6** | 26.450,3 |
| Salamanca | 328.446 | 11,216 | **11** | 29.858,7 |
| Segovia | 158.251 | 5,404 | **5** | 31.650,2 |
| Soria | 90.183 | 3,080 | **3** | 30.061,0 |
| Valladolid | 528.644 | 18,053 | **18** | 29.369,1 |
| Zamora | 165.564 | 5,654 | **6** | 27.594,0 |
| **Total** | **2.401.221** | **82,000** | **82** | — |

Distribución canónica candidata:

`05:6, 09:12, 24:15, 34:6, 37:11, 40:5, 42:3, 47:18, 49:6`

## 5. Qué queda pendiente antes de M04

Todavía no se fijan por copia:
- suelo duro;
- techo duro;
- tolerancia fina;
- regla exacta de municipio indivisible/partible;
- tratamiento de capitales/municipios sobredimensionados.

Estos valores deben decidirse con la distribución real de municipios de Castilla y León y comprobar si los principios usados en Aragón son generalizables.

## 6. Siguiente análisis

Calcular, para cada provincia y municipio:
- población / target provincial;
- municipios que caben enteros en un distrito;
- municipios que necesariamente requieren 2, 3 o más distritos;
- impacto de posibles valores de suelo/techo;
- capitales y municipios que obligan a partición interna.

Solo después se abrirá M04.
