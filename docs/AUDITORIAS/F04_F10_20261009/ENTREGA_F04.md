# DDD F04 — entrega material local

Versión 1.0.0. Fecha 2026-10-10. Estado: candidato para revisión local. Alcance: Fuentes oficiales, F04 A/B. Origen: encargo explícito del propietario; sin predecesor.

Base: 7ce06043fe74102196152ad07ad17f47b1779a6b. Sin modificación de código productivo, contratos, catálogos operativos, otros frentes ni las evidencias F01–F03. DDD_GOBIERNO.md no localizado tras búsquedas dirigidas; ruta solicitada. Se aplican AGENTS.md y POLITICA_DE_VERSIONES.md existentes; no se modifica gobierno.

Se recuperaron los cinco artefactos históricos exactos definidos en artifact-metadata.json, tras comprobar ausencia local; original exterior e interior coinciden con SHA esperado, tamaño y CRC. Los metadatos GitHub conservan run/commit, origen y adquisición histórica en manifiestos de procedencia. La población real Periodo y la colección histórica INE de seccionado acreditan 2025/2025, separado de la edición de catálogo 2025. No se adquirieron fuentes oficiales nuevas.

A: Andalucía, Comunidad Valenciana y Extremadura disponen ahora de originales, inventarios, procedencia, fechas por fuente, identidad calculada y receipts de la operación real de recuperación. B: Aragón y Castilla y León conservan sus receipts históricos, cuya identidad coincide, y reciben informes nuevos sobre bytes reales. No se exige fuente electoral para estos materiales.

El builder estricto existente rechazó los cinco originales por Total vacío. Sus fallos están en logs/completar.stderr y resultados-cinco.json. Los diagnósticos producidos con el reconciliador existente y validate_report_bindings preservan los vacíos y documentan BLOCKED; no se sustituyen esos fallos ni se relaja ninguna puerta.

Los vacíos corresponden exclusivamente a claves fuera del universo del seccionado congelado del mismo año. Se produjo una derivación local separada: selección exacta de las claves existentes en ese seccionado; nunca se retira un valor numérico ni una sección del destino. Cada derivation.json conserva las filas excluidas, línea, clave, valores crudos, hash original y derivado. No hay imputación, reparto, correspondencia entre años ni cambio geométrico. Se conservan 6029/1463/3506/3515/964 secciones y, respectivamente, 8676713/1364621/2401221/5425182/1053345 habitantes.

Los cinco candidatos-v2 pasan el builder original y validate_prepared_package con READY y conservación exacta. Son nuevas identidades locales y receipts de derivación; no se atribuyen a los IDs GitHub originales ni a sus receipts. El acquired_at del candidato identifica la operación local; acquired_at_kind y original_acquisition_dates conservan su semántica. No representa una nueva adquisición oficial ni actualiza la edad de sus fuentes históricas. No se promocionan a catálogos, acreditaciones o producción.

matriz-19.json consolida cinco candidatos nuevos y catorce registros de evidencia exacta anterior, reutilizados sin repetir F01–F03. Esa matriz no declara habilitación de generación ni F08/F10 PASS.

Ejecución: Python 3.10.19 del entorno DDD existente; GeoPandas 1.1.2 y PyYAML 6.0.3. Comandos y resultados están en logs/; no instalaciones. Primer diagnóstico falló por faltar el contexto geométrico del inventario; se corrigió el arnés y se guardó el resultado nuevo en logs/diagnosticos-v2.*. Primer candidato falló por acquired_at no interpretable; queda preservado en andalucia/candidato, sin receipt ni resultado READY. candidato-v2 corrige sólo metadatos temporales de la operación local y conserva fechas originales; todos los validadores pasan. Primeros enlaces de entrega HTTP 403 caducados; se renovaron para los mismos IDs.

Criterio de revisión: cotejar fuentes reales, contratos, exclusión exacta sin habitantes descartados, años y procedencia, invariantes de los informes y separación de identidades. F04 no se declara PASS por la auditoría previa; requiere aceptación de estos entregables materiales. La revisión local separada no equivale por sí sola a aprobación externa o producción.

F05–F10 se continuarán según sus dependencias y aceptación; no se ejecuta ningún paso productivo. No 00, 01, M04, distritos, workflows, push, PR, merge ni publicación.
