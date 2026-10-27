# F10 — Comunidad Valenciana

Versión: 1.0.0. Fecha: 2026-10-27. Estado: expediente preparado, BLOCKED_DECISION.
Alcance: fuentes oficiales; dependencia M02 del frente autonómico. Origen: nuevo expediente sobre base 75fe65b6; sin sustitución de antecedentes.
Cambios y motivo: consolidar evidencia adquirida y la decisión exacta pendiente; evitar otra adquisición 2023 o cambiar la fuente para sortear el bloqueo.

La adquisición 2023/2023 está CLOSED. El consumidor valida el receipt del run 39315133646, identidad `94f094a23493448d9ee38f1b51fe6f73dd0f29b6b7a4410eae8bb5a170c38d62`. La elección es ADMISSIBLE. Persisten `M02_CONTRACT_NOT_BOUND_TO_2023` y ausencia de `evidence.prepared_source_pair`. Resultado conjunto BLOCKED. La proyección y los SHA de evidencia están adjuntos; no se vuelve a descargar ni a extraer el paquete.

La evidencia completa ya conservada contiene 3.503 nodos, 5.216.195 habitantes y cero aislados. Bajo EPSG:25830 hay cero pares por encima de 1 m²; en el universo completo existen 148 pares de área positiva. El contrato que habilita ese CRS está ligado a fuentes 2025. La evaluación 2023 con baseline EPSG:3035 produce dos solapamientos sobre 1 m²: aproximadamente 11,8277 y 12,1112 m² para `4617201001/4619401008` y `4617201001/4619401013`. Las cifras distintas del ensayo WFS antiguo no sustituyen esta evaluación íntegra.

La consulta acotada de metadatos oficiales indexados del INE el 27-10-2026 confirma Secciones_2023 almacenada en EPSG:25830: https://www.ine.es/geoserver/ogc/features/v1/collections?f=text%2Fhtml . Esto acredita un CRS de almacenamiento, no la decisión de aplicación del contrato M02. El intento de abrir el catálogo JSON por el conector devolvió error; no se declara descarga nueva ni respuesta institucional. No hay motivo para readquirir las tres provincias.

**Decisión preparada para el Director y responsable M02:** resolver expresamente si el contrato de cálculo nativo EPSG:25830 puede vincularse a la edición 2023, con evidencia de precisión y regresión, o mantener el baseline EPSG:3035 y solicitar criterio/rectificación oficial al INE. La decisión debe identificar los tres CUSEC, el universo 2023 y las condiciones de reproducibilidad; no basta extender una etiqueta 2025. No se modifica CRS, tolerancia ni geometría en este expediente.

Tras una decisión aprobada: aplicar el vínculo de contrato en el frente responsable, validar M02/M03 con originales 2023, completar prepared_source_pair mediante el consumidor y volver a derivar F10. Mientras tanto no se promueve producto ni se ejecuta territorio. La adquisición queda cerrada y se pasa al siguiente expediente.

Pruebas: cinco casos de `test_f10_valencia_2023_durable_receipt` dentro de 22 pruebas dirigidas PASS; hashes íntegros de originales fijados por esa regresión. La proyección es de metadatos y no reextrae paquetes. CI nueva no ejecutada; revisión separada pendiente del estado exacto antes del commit.
