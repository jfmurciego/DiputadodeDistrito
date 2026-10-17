> **Actualización 2026-10-17:** autorización expresa del propietario el 2026-10-15 para adquirir cartografía oficial CNIG/IGN y solicitar el histórico vigente a 2025-01-01. `source_download=true` **sólo para esta adquisición**, `NAT-C-056=READY`. Estado de datos: **no descargado; no acreditado**. Las alusiones a `source_download=false` inferiores son históricas (2026-10-14), no vigentes. `generation_authorized=false`.

# Expediente único de adquisición: límites administrativos independientes 2025

**Campaña:** `ddd-national-campaign-20261013`  
**Tarea de catálogo:** `NAT-C-055`  
**Tarea de recibo pendiente:** `NAT-C-056`  
**Fecha de consulta del catálogo:** 2026-10-14  
**Estado:** candidato oficial identificado; paquete no descargado; no acreditado.  
**Permiso:** `source_download=false`; esta ficha no autoriza descarga ni incorporación de datos.

## Fuente candidata y autoridad

El candidato común para las 52 unidades es el producto **Límites municipales, provinciales y autonómicos** del Centro Nacional de Información Geográfica (CNIG), organismo del Instituto Geográfico Nacional (IGN), alimentado por la Base de Datos de Líneas Límite Jurisdiccionales de España (BDLJE) y las delimitaciones inscritas en el Registro Central de Cartografía (RCC).

- Catálogo oficial: <https://centrodedescargas.cnig.es/CentroDescargas/limites-municipales-provinciales-autonomicos>
- Ficha candidata GML: <https://centrodedescargas.cnig.es/CentroDescargas/detalleArchivo?sec=12408588>
- Identificador de producto: `LILIM` (Límites municipales, provinciales y autonómicos).
- Archivo candidato anunciado: `LINEAS_LIMITE_GML.ZIP`, ficha “Límites y Unidades Administrativas Actuales”.
- Edición disponible comprobada: 2026-08-10; cobertura: toda España; escala nominal 1:25.000; tamaño anunciado: 63,18 MB.
- Referencia geodésica anunciada: ETRS89 en Península, Illes Balears, Ceuta y Melilla; REGCAN95 en Canarias. El CRS exacto de cada capa y su transformación deben verificarse en los bytes recibidos.
- Licencia indicada por CNIG: condiciones compatibles con CC-BY 4.0; registrar atribución en cualquier derivado.

La fuente es institucionalmente independiente del seccionado INE 2025. **La edición actual de 2026 no acredita por sí sola la geometría vigente a 2025-01-01.** Antes de usarla se debe comprobar que los segmentos/capas incluyen vigencia temporal suficiente para reconstruir esa fecha, o sustituirla por un snapshot oficial histórico efectivo en esa fecha. La ficha del producto también advierte que algunos tramos son provisionales y que la incertidumbre posicional ronda 40 m salvo líneas replanteadas con mayor precisión. Por tanto, el producto sirve para contraste independiente de dominio y estado administrativo; no se empleará para reparar geometrías INE, crear adyacencias seccionales ni imponer exactitud topológica que su precisión no respalde.

## Requisito de recibo (NAT-C-056)

Una adquisición autorizada debe conservar, en un único receipt nacional:

1. URL de catálogo y ficha exacta, autoridad, nombre de producto/archivo, identificador, edición de publicación y fecha/hora de adquisición.
2. Los bytes originales sin alteración, SHA-256, tamaño, licencia/atribución, versión del software de descarga y recibo HTTP o equivalente.
3. CRS/capas/campos realmente presentes; identificadores de entidad; códigos administrativos y su tabla de correspondencia oficial con CPRO/CUMUN.
4. Fecha de vigencia de cada delimitación necesaria para reconstruir 2025-01-01; fuente y expediente RCC que sostienen tramos inscritos, provisionales o modificados.
5. Un dictamen explícito de aptitud temporal y de cobertura antes de desbloquear cualquier contraste provincial. Si no se puede demostrar vigencia en la fecha censal, no se sustituirá por “la edición más cercana”: se solicitará un snapshot histórico oficial con fecha efectiva 2025-01-01 o una fuente oficial equivalente.

No se aceptarán páginas de visualización, mosaicos generalizados, mapas autonómicos, la geometría INE repetida, ni una segunda exportación del mismo producto como sustitutos independientes.

## Prueba por provincia (NAT-C-003…054)

Tras validar el receipt común, cada CPRO 01–52 tendrá un informe independiente con: claves esperadas y encontradas, correspondencia CPRO/CUMUN, CRS y transformación aplicada, cobertura, geometrías/entidades ausentes o repetidas, selección temporal, estado jurídico/provisional, comparación del dominio con las secciones INE 2025, diferencias geométricas y su sensibilidad, anomalías y hashes. El contraste no modificará ni acreditará automáticamente el grafo físico seccional N08.

El cierre nacional 52/52 se conserva en `NAT-C-002` y solo podrá evaluarse una vez disponibles los 52 informes. Los recuentos y hashes N08 ya acreditados permanecen intactos.

## Inventario local y causa del bloqueo

La edición INE 2025 y el producto topológico N08 52/52 están en el repositorio; comparten el linaje INE y no son una delimitación administrativa externa. La búsqueda independiente revisó artefactos N08, worktrees relacionados y cachés DDD-control/DDD-almacén; no halló bytes de un paquete nacional CNIG/RCC ni su hash. Los GeoJSON simplificados de autonomías y productos electorales regionales no cubren ni acreditan límites provinciales. Esta búsqueda está acotada a esas ubicaciones, no afirma que no exista otra copia fuera de ellas.

**Próximo paso:** obtener autorización expresa para la adquisición puntual o recibir del Director/propietario el paquete oficial equivalente. Hasta entonces `NAT-C-056` es `WAIT_OWNER`, las pruebas provinciales esperan el recibo y ningún estado topológico se eleva.
