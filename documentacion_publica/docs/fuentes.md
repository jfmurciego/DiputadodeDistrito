# Fuentes y derechos de uso

## Inventario existente

DDD ya tiene un catálogo oficial de fuentes, un catálogo operacional de preparación, contratos territoriales/electorales y recibos de evidencia. El portal debe construir una vista de consulta sobre esos registros, conservando su identidad, en lugar de crear un catálogo paralelo editado a mano.

| Registro | Responsabilidad |
|---|---|
| `fuentes/catalogo_oficial.yaml` | Proveedores, endpoints, formatos y políticas de edición |
| `configuracion/catalogo_preparacion.yaml` | Preparaciones y referencias acreditadas por territorio |
| `territorios/<id>/evidencia/` | Recibos, manifiestos y linaje de productos |
| `orchestracion/publicaciones_visor.json` | Activos utilizados por el visor |

## Ficha pública mínima propuesta

Cada recurso debe identificar proveedor, URL original, fecha de recuperación, fecha de referencia de los datos, edición territorial, elección cuando corresponda, licencia y atribución, formato, CRS, tamaño y SHA-256. La versión del código y el contrato que lo transforman deben poder seguirse desde su ficha.

Edición territorial, año poblacional, fecha de cartografía y fecha electoral son campos diferentes. No deben inferirse todos de un nombre como `2025`. En la muestra de Cantabria hay un atributo `POP_2023`: su interpretación exige consultar la procedencia, sin renombrarlo por apariencia.

## Antes de redistribuir

La disponibilidad pública de un archivo no basta para establecer sus derechos de reutilización. Para cada fuente, documentar condiciones de uso y atribución, fecha de consulta y permiso de redistribución. Cuando no esté resuelto, mostrar la ficha y el enlace al proveedor; mantener la copia de trabajo restringida.

La licencia del código, la de cada fuente y la de los productos derivados deben declararse por separado. Esta auditoría no certifica las licencias de todas las fuentes. Esa revisión es un hito pendiente antes de abrir descargas masivas.

[Catálogo oficial revisado](https://github.com/jfmurciego/DiputadodeDistrito/blob/11f0ba2b775a889f2316e31ebdbd859cbc50ab13/fuentes/catalogo_oficial.yaml)

*Versión 1.0.0 · 2026-11-03 · Archivo nuevo.*
