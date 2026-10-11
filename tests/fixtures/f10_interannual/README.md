# Regresiones reales F10

Versión: 1.0.0. Fecha: 2026-10-12. Estado: candidato. Alcance: pruebas locales de Fuentes Oficiales. Origen: adquisiciones conservadas de 2026-10-11. Motivo: acreditar cantidades retenidas por correspondencia sin inventar destinos.

Los tres JSON gzip contienen las secciones poblacionales sin destino del diagnóstico original, las secciones objetivo sin población y una sección de control con igualdad exacta. Las geometrías proceden de los ZIP normalizados identificados por SHA-256 y tamaño en cada fixture. No contienen simplificación ni redondeo adicional. La población procede del miembro CSV materializado del mismo inventario. El informe original determina exclusivamente el subconjunto; la conciliación y las relaciones interiores se vuelven a calcular en el test.

Los déficits reproducidos son 31.024, 319.989 y 84.197 habitantes. Contabilizar el input íntegro entre asignado y retenido no acredita conservación de población en el objetivo. Las fusiones, reparticiones y cambios de frontera siguen bloqueados bajo el contrato vigente.

El fixture de población valenciana contiene tres filas literales de `65034.csv` dentro del ZIP nacional reconstruible desde `inputs/partes`, cuya huella está fijada por `reconstruir_fuentes.sh`. El conteo de observaciones para 2023 es 1.236/444/1.823 para 03/12/46; coincide con la cobertura geométrica. Este snapshot histórico constituye evidencia independiente y no sustituye el payload poblacional F10, que no fue conservado. Las filas prueban que el filtro vigente reconoce 46; no prueban que la respuesta original perdida tuviese la misma cobertura.

La reproducción completa, con comprobación de huellas materiales y evidencia geométrica durable, se ejecuta mediante `python -m herramientas.auditar_compatibilidad_interanual_f10 --evidence <adquisiciones>/<territorio>/evidence --output <ruta-nueva>.json`. El comando no adquiere fuentes, no modifica evidencias anteriores ni promueve resultados. Los hashes y las cantidades del replay completo figuran en `docs/AUDITORIAS/F10_COMPATIBILIDAD_INTERANUAL_20261012/reconciliacion.json`.
