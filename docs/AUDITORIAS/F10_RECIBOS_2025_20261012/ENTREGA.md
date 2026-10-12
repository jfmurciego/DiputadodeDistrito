# F10 — Consumo territorial de tres fuentes oficiales 2025/2025

**Fecha:** 2026-10-12. **Versión:** 1.0.0. **Estado:** candidato a integración, sin promoción.  
**Base:** `main@c59c2653f58f4fead236f09bee51c354a7e89904`.

La autorización del titular `F10-20261012-PAIR-2025` cambió la referencia territorial en Andalucía, Aragón y Castilla y León a población/seccionado INE 2025/2025. Los tres paquetes originales F10 ya estaban conservados, pero los receipts no podían incorporarse porque el contrato anterior exigía seccionado 2026.

Se verificaron de forma independiente los ZIP originales del archivo protegido `DDD_F10_5_ARTEFACTOS_AUTENTICOS_20261011.zip` y los receipts versionados del repositorio. Los SHA-256 de los ZIP, de `prepared_sources.zip` y del informe de compatibilidad coinciden exactamente con las identidades declaradas. Los tres informes declaran `READY`, no registran causas y conservan exactamente 8.676.713, 1.364.621 y 2.401.221 habitantes, respectivamente. El expediente JSON contiene los SHA completos y los runs.

Se registran mediante `independent_source_evidence`, ya admitido por el contrato #179 y probado previamente con Extremadura. `promoted: false` conserva íntegramente `preparation_evidence`, `last_valid_checkpoint` y productos históricos. No se altera ningún ZIP ni ningún resultado electoral. El planificador de legislatura reconoce los receipts independientes auténticos y reutiliza las fuentes 2025/2025, con validación y fallo cerrado en receipts promovidos o mal clasificados. Los tests CI prueban identidad del receipt y admisión territorial documental, sin inferir que CI tenga acceso a los ZIP locales protegidos.

**Separación de puertas:** el **receipt territorial 2025/2025** se puede consumir independientemente. La **correspondencia entre las secciones territoriales 2025 y los resultados electorales 2026** sigue `BLOCKED_PENDING_OFFICIAL_EVIDENCE`. Ningún PASS de fuentes conjunto/electoral, ejecución, M01–M08, promoción o publicación se deriva de esta PR. Comunidad Valenciana permanece BLOCKED y su población 2023 incompleta.
