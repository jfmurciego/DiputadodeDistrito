# N08 — expedientes nominales de componentes pendientes de acreditación

**Continuidad de la campaña nacional:** la integración técnica de PR #268/#270 y la auditoría de entrada 52/52 constan ya en `main` (19-10-2026). Este incremento **no vuelve a generar datos**: extrae del producto N08 original, protegido por el SHA del manifiesto fijado en código, un expediente por cada uno de los componentes seccionales aislados en las cinco provincias donde falla una condición necesaria de población y contigüidad estricta.

## Qué produce

`python -m herramientas.expedientes_excepciones_congreso_n08 --output /ruta/nueva/expedientes.json` lee únicamente los archivos provinciales originales del INE 2025, calcula la población exacta por componente, la relación de CUSEC y CUMUN, las cotas aprobadas para los distritos y una lista nominal de **10 componentes secundarios** que requieren clasificación y decisión. Se comprueba que el conjunto de CUSEC esté completo, que no haya duplicados y que las cifras concilien con N08.

| CPRO | Caso de examen | Componentes de grafo | Naturaleza pendiente |
|---|---|---:|---|
| 07 Baleares | Menorca, Ibiza, Formentera | 4 | Excepción insular nominal, no puente marítimo |
| 09 Burgos | Treviño, La Puebla de Arganzón, Hacinas y Monasterio de la Sierra | 4 | Distinguir enclaves, ledanías y defectos cartográficos |
| 17 Gerona | Llívia | 2 | Enclave internacional, fuente temporal pendiente |
| 34 Palencia | Berzosilla y Villodrigo | 3 | Delimitación oficial de enclaves pendiente |
| 36 Pontevedra | A Illa de Arousa | 2 | Isla; no atribuir continuidad por aristas marítimas |

Los nombres sirven **sólo para orientar la investigación**. Los CUSEC y las poblaciones proceden del producto N08, no de esta tabla. La extracción de componentes no prueba que todo caso sea un enclave legal ni autoriza una excepción.

## Regla de decisión futura por componente

1. Conservar el expediente INE 2025, su lista o digest completo de CUSEC y el SHA original.
2. Contrastar su límite administrativo con geometría vectorial **independiente**, fechada y acreditada como efectiva al 01/01/2025, incluyendo fuente y títulos RCC de los límites pertinentes.
3. Clasificar formalmente `ISLA / ENCLAVE / LEDANÍA / DEFECTO_CARTOGRÁFICO / NO_ACREDITADO`, **sin deducir la clase del grafo**.
4. Si existe una discontinuidad legítima, elevar al propietario una excepción *individual* con edición, alcance CUSEC, reglas de vigencia y prueba de caducidad cuando cambie la fuente.
5. Si el dato es erróneo, conservar el original y la corrección acreditada como capas/versiones distintas. No crear aristas ficticias o conectar islas.
6. Sólo con excepciones ratificadas y comprobaciones posteriores volver a estudiar la partición real de K=407.

**Límite de aceptación:** `generation_authorized=false`. Esto es un expediente de evidencia para la decisión nominal, **no** certificado de los 407 distritos, no acredita recepción CNIG y no verifica fronteras 52/52.

La exportación JSON se adjunta como artefacto de CI; no altera `TASK_REGISTRY.json`, `CAMPAIGN_MANIFEST.json` ni documentos históricos cuyos hashes y decisiones permanecen vigentes hasta que haya un evento verificable de acreditación o decisión.
