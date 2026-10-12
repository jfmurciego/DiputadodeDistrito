# F10 — Referencia territorial INE 2025/2025 para las elecciones de 2026

**Versión:** 1.0.0  
**Fecha:** 2026-10-12  
**Estado:** decisión del titular autorizada para referencia territorial; candidato a revisión técnica de implementación  
**Alcance:** Andalucía, Aragón y Castilla y León  
**Motivo:** ausencia de población seccional 2026 y correspondencias incompletas entre los seccionados INE 2025 y 2026  
**Origen:** autorización expresa del propietario en el chat de dirección DDD de 2026-10-12

## Decisión

El ámbito territorial de las tres campañas de elección 2026 empleará la pareja **población por sección INE 2025 + seccionado INE 2025**, ambos de la misma edición oficial, como **referencia territorial**. El año electoral sigue siendo 2026. La colección de secciones 2026 continúa siendo una fuente oficial válida para su propio año, pero no se usa como geometría de esta pareja territorial 2025.

La identidad de la decisión está en `configuracion/decisiones/f10_referencia_territorial_2025_2026.json`. La matriz distingue `section_required_year=2026` de `section_selected_year=2025` y registra exactamente un año de desfase. El validador admite esa selección sólo para tres territorios y exige aprobación documental y estado electoral pendiente. Se conserva la validación normal para los restantes 16 territorios.

## Distinción electoral obligatoria

**No hay acreditación de equivalencia ni de correspondencia 2025→2026.** Los resultados electorales por sección de 2026 no podrán asignarse directamente al seccionado territorial 2025 por mera igualdad del código. La incorporación electoral requiere una correspondencia independiente, oficial y verificable o decisión posterior expresa, con todas sus puertas. No se inventa trasvase electoral.

Esta decisión **no autoriza ejecutar `00`, M01–M08, generación ni publicación**, ni promueve fuentes nuevas ni recalifica los 19 consumidores. Se conservan productos certificados y receipts históricos. La puerta de datos poblacionales, geométricos, administrativos y topológicos debe validarse por cada paquete de forma independiente. Los informes del experimento de correspondencia 2025→2026 permanecen como evidencia histórica, no como baseline activo.

## Resultado esperado y verificación

El resolver de preparación devuelve `population_year_selected=2025`, `section_year_selected=2025`, `section_year_required=2026`, `electoral_2026_crosswalk_status=BLOCKED_PENDING_OFFICIAL_EVIDENCE` y `generation_authorized_by_reference_decision=false` para cada territorio. Si se altera la decisión o se intenta aplicar a otro territorio, debe fallar cerrado. No declarar PASS F10 hasta comprobar el recibo y el consumidor reales; no declarar PASS electoral por seleccionar una geometría diferente.

PR separada para esta decisión, sin fusión automática. No requiere cambios en K, límites poblacionales ni la política de los otros 16 territorios.
