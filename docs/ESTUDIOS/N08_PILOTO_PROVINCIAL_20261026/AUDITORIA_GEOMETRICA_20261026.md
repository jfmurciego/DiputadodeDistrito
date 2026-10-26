# Adenda de auditoría geométrica — León y Cáceres

- Versión: 1.0.0
- Fecha: 2026-10-26
- Alcance: comprobación diagnóstica sobre geometrías originales INE 2025
- Estado: León supera conectividad física para su candidato; Cáceres permanece bloqueado físicamente
- Anterior: `INFORME.md` (se conserva sin reescribir)

## Método y entorno

La auditoría reconstruyó `seccionado_2025.zip` desde las tres partes protegidas, verificó sus SHA contra `inputs/partes/MANIFEST_PARTES.sha256` y la huella contractual del ZIP, leyó el Shapefile original en EPSG:25830 y unió exactamente por CUSEC. No aplicó buffers, simplificación, ajuste de precisión ni reparación geométrica. Solo las fronteras lineales de longitud positiva se usaron como aristas; contactos puntuales y solapamientos quedaron registrados aparte.

La auditoría encontró un defecto en su propio control de cardinalidad: interpretaba `physical_part_components` del nodo (representantes de componentes conexos) como si fuera el número de polígonos originales de la CUSEC. La regresión mostró, por ejemplo, que `2405001001` tiene dos partes originales que pertenecen al mismo componente provincial. Se corrigió la comparación para contrastar las identidades `CUSEC:pNNNN` de `polygon_part_components` con las partes originales ordenadas por WKB. Se añadieron pruebas de inventario y rechazo de identidades duplicadas.

### Actualización de reproducibilidad

`REPRODUCIBILITY.json` es la instantánea histórica de la primera ejecución en el entorno macOS aislado; sus cuatro `SKIP` reflejan que Shapely no estaba instalado en ese entorno en ese momento. Después, las cuatro pruebas geométricas originales se ejecutaron con el runtime Miniforge indicado arriba y pasaron (4/4); las dos regresiones nuevas también pasaron. El detalle y la distinción de entornos constan en `REPRODUCIBILITY_GEOMETRIA_20261026.json`. La validación de la versión exacta fijada por el workflow corresponde a la CI remota del HEAD publicado.

La CI posterior detectó que el grupo de concurrencia del workflow no declaraba `queue: max`, aunque no cancela ejecuciones activas. Se añadió esa política para que ejecuciones analíticas pendientes se encolen en vez de ser reemplazadas. La corrección queda pendiente de confirmar por CI en el HEAD siguiente. La suite general también mostró fallos de fixtures/run IDs de Castilla-La Mancha y Ceuta; no pertenecen a este diff y no se alteraron.

Runtime local disponible: Python 3.13.12, GeoPandas 1.1.2, Shapely 2.1.2, GEOS 3.14.1, NumPy 2.4.2, pandas 3.0.0, pyogrio 0.12.1/GDAL 3.12.2, pyproj 3.7.2/PROJ 9.7.1. Las cuatro pruebas geométricas omitidas, las dos regresiones nuevas y las suites focales se ejecutaron con este entorno. El workflow conserva su runtime reproducible fijado por lock; la CI del nuevo HEAD debe confirmarlo allí.

## Resultados

### León, CPRO 24, K=4

El candidato `LEON/leon-corrected.json` cubre 444 CUSEC y 452 partes poligonales. Los cuatro distritos tienen un único componente físico y 1.135 aristas lineales internas en conjunto. La auditoría registró 27 contactos puntuales y dos solapamientos, ninguno utilizado como arista. Ambos solapamientos están dentro de `LEON-02`: `2408906006:p0000` con `2408906007:p0000` (0,00009514 m²) y con `2408906009:p0000` (0,00366500 m²); área agregada 0,00376014284156 m². No hay solapamiento entre distritos. Estas anomalías del seccionado se conservan sin reparación y no impiden la conectividad física, pero sí dejan pendiente demostrar que la cobertura geométrica constituye una partición de áreas sin solapes. La geometría no se modificó. SHA-256 del candidato: `bbc7c8b638d02b9c7100c83d7faa449f77161d1c1b49b5a3999dd93ff606bdc3`; SHA-256 de la geometría nacional reconstruida: `55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4`.

**Resultado geométrico:** conectividad física positiva demostrada para esta asignación y esta geometría INE 2025. No acredita límites administrativos CNIG/IGN, no resuelve eventuales excepciones, no certifica el producto y no autoriza generación ni publicación.

### Cáceres, CPRO 10, K=3

El candidato cubre 411 CUSEC y 429 partes poligonales. `CPRO10-01` y `CPRO10-02` son físicamente conexos; `CPRO10-03` tiene dos componentes. Una componente es la parte `1004903001:p0000` de la sección multiparte CUSEC `1004903001` (Casar de Cáceres). La parte no tiene conexión lineal con las demás partes asignadas a ese distrito; los contactos puntuales no se contaron. La provincia como grafo puede tener otras conexiones y este resultado no prueba inviabilidad global ni falta de una reasignación alternativa.

**Resultado geométrico:** candidato de Cáceres no supera conectividad física en su asignación actual. Se conserva como diagnóstico no certificado; no se creó pasarela ni se redistribuyó la CUSEC.

### Alternativa Cáceres `degree_asc` — diagnóstico condicionado

Se ejecutaron los diez órdenes deterministas declarados por la búsqueda acotada (`5.000` estados y `30.000` transiciones máximos por orden), y se aplicó la reparación municipal local existente a cada testigo hallado (máximo `30.000` ensayos por testigo). Hubo tres testigos condicionales y siete órdenes sin testigo dentro de esos límites; no apareció una asignación sin divisiones municipales. Esto no demuestra inexistencia global.

La variante `degree_asc` conserva CUMUN `10037` dividido entre **CPRO10-02 y CPRO10-03**, con los CUSEC completos; las poblaciones de sus fragmentos son 51.453 y 45.145 habitantes. Los distritos resultan en 122.527, 120.085 y 145.578 habitantes, dentro de la banda 109.988–148.806. La auditoría original de partes INE 2025 encontró un componente físico por distrito, 146/122/161 partes y 345/289/387 aristas lineales positivas; 34 contactos puntuales no se usaron como aristas y no hubo solapamientos.

M05 examinó 119 asignaciones para la división de CUMUN 10037 y certifica únicamente que, **con las demás asignaciones CUSEC fijas**, no se pudo consolidar en un solo distrito conectado respetando las cotas. `global_minimality_proven=false`; por ello el candidato conserva `municipal_policy_certified=false`. Esta variante mejora la conectividad física frente al testigo original, pero no elimina la incertidumbre de minimalidad global ni acredita límites CNIG/IGN. Se guarda separada como candidato analítico, con generación y certificación cerradas.

## Estado de certificación y uso

Ambos informes completos están junto a esta adenda y enlazados por `MANIFEST_GEOMETRIA_20261026.json`. León queda validado geométricamente solo en el alcance físico descrito; las demás puertas territoriales e institucionales permanecen separadas. Cáceres continúa como contraste diagnóstico, sin exigir que su resultado condicional sea positivo para aceptar la comprobación geométrica de León. `generation_authorized=false` y `product_certification=NOT_PERFORMED` en ambos artefactos.
