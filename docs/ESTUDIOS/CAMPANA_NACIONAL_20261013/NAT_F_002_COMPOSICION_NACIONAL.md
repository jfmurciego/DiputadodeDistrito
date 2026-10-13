# NAT-F-002 — Composición candidata nacional

**Versión:** 1.1.0 · **Fecha:** 2026-10-13 · **Estado:** candidato diagnóstico

**Alcance:** agregar asignaciones provinciales ya calculadas en una interfaz reanudable. No ejecuta M01–M06 ni crea particiones.

La auditoría de interfaces encontró lectura/validación de entradas en `congreso_preflight_adapter`, preflight provincial con checkpoint en `preflight_campana_congreso`, factibilidad necesaria/separada en `congreso_feasibility`, solver exacto acotado para grafos pequeños y certificador nacional independiente en `congreso_candidate_certifier`. No existía una interfaz que uniera resultados provinciales validados bajo IDs nacionales deterministas y checkpoint por unidad.

`ddd_core.congreso_national_composer.NationalCandidateComposer` cubre únicamente ese límite. La ruta nacional `from_accredited_inputs` lee el contrato N08, el manifiesto INE, sus partes protegidas y las salidas/crosswalk, además del manifiesto topológico y las 52 unidades. Comprueba los SHA raíz aprobados, identidad y ediciones 2025, cuotas contractuales, cobertura 36.554/52, población 49.128.297 y hashes/canonicalización de cada artefacto. Las cuotas y hashes no se reciben como valores del llamador. Los tests sintéticos usan el constructor separado `synthetic_fixture=True` y nunca acreditan inputs.

Cada unidad se registra con cobertura exacta y K local, se persiste atómicamente y se incorpora a un checkpoint ligado a la identidad de la campaña. Tanto al cargar como al componer se vuelve a verificar el SHA del artefacto, identidad, cobertura y cuota; cambios en contrato, fuentes, topología, universos o cuotas requieren un checkpoint nuevo.

La composición reasigna IDs deterministas de la forma `DDD-<CPRO>-<ordinal>`. No comprueba población, conectividad, disciplina municipal ni excepciones: esas garantías pertenecen al certificador independiente. La salida siempre declara `generation_authorized=false` y `certification_status=NOT_PERFORMED`. Subconjuntos sólo se admiten si el llamador los marca como fixtures sintéticos; la forma completa exige las 52 unidades y K=407.

Pruebas: `pytest -q tests/test_congreso_national_composer.py`. Fixtures sintéticos, sin datos territoriales. Integración de salida con el certificador y ejecución productiva quedan pendientes; esta interfaz no acredita que exista una partición nacional válida.
