# Contratos funcionales M01–M08

Esta carpeta documenta cada módulo como una unidad de transformación auditable. La documentación del módulo y sus outputs cumplen funciones distintas: **el documento explica por qué existe y qué contrato debe cumplir; el output demuestra qué produjo una ejecución concreta**.

| Módulo | Estado que crea | Producto navegable en Git | Producto geográfico/estructural pesado |
|---|---|---|---|
| M01 | secciones censales con población | `secciones.csv` | GeoJSON de 1.463 secciones |
| M02 | topología de vecindad | `adyacencias.jsonl` | el propio JSONL es canónico |
| M03 | grafo territorial | `grafo.json` | el propio JSON es canónico |
| M04 | distritación inicial | `asignacion_inicial.csv` | GeoJSON de secciones asignadas |
| M05 | distritación optimizada | `asignacion_optimizada.csv` | GeoJSON optimizado |
| M06 | entidades distritales consolidadas | `catalogo_distritos.csv` + `composicion_distritos.csv` | GeoJSON de secciones y 67 distritos |
| M07 | agregación electoral | CSV por partido + resumen | GeoJSON de secciones electorales |
| M08 | producto electoral territorial | `distritos_resultados.csv` | GeoJSON final de distritos |

## Regla de completud
Un informe responde «¿cómo fue el módulo?». Un producto responde «¿qué entidades produjo?». Ambos son necesarios. Nunca se considerará auditable una ejecución que conserve el primero y descarte el segundo.

## Regla de geometrías
Las geometrías comprimidas no se versionan repetidamente dentro del historial Git porque multiplicarían decenas de MB por ejecución. Se conservan como artefactos M01–M08 de la ejecución de Actions. En Git queda la proyección tabular completa y `PRODUCTOS.json` con ruta, tamaño y SHA-256, de modo que el binario descargado puede verificarse byte a byte.

## Regla de preparación reutilizada
M01-M03 no se atribuyen falsamente a cada ejecución iterativa. Si se restauran desde caché, la ejecución conserva su copia/proyección auditable y referencia la `preparation_key`. La preparación vigente `a9d5cbb1...069d4` fue producida por GitHub Run #3; su expediente está en `resultados/preparaciones/<preparation_key>/REFERENCIA.json`.

## Documentos
- `M01_BASE_TERRITORIAL.md`
- `M02_ADYACENCIAS.md`
- `M03_GRAFO_TERRITORIAL.md`
- `M04_SOLUCION_INICIAL.md`
- `M05_OPTIMIZACION.md`
- `M06_CONSOLIDACION_TERRITORIAL.md`
- `M07_AGREGACION_ELECTORAL.md`
- `M08_PRODUCTO_FINAL.md`
