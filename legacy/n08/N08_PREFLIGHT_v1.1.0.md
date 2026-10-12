# N08 — Preflight sobre N06 y fuentes INE 2025/2025 integradas
Versión 1.1.0; fecha 2026-10-12; alcance preflight sin piloto; estado BLOCKED.
Origen: docs/ESTUDIOS/N06_DECISION_K_20261012/N08_PREFLIGHT_20261012.md (expediente conservado íntegro).
Cambio: reconciliación de N06 con PR #241 sobre main f87445f5d75a53cee17cd3bcc711854318b795ff.

N06 está aprobado; K=407 y 52 cuotas se contrastan con la población acreditada. La pareja INE 2025/2025, CUSEC, manifest y hashes se preservan íntegros: 36.554 unidades, 49.128.297 habitantes, 338 filas históricas ausentes. Cantabria conserva P=593.623 y K=5 como candidato de evaluación, sin seleccionar ni ejecutar piloto. generation_authorized=false.

Bloqueos técnicos restantes:
- Topología: falta política nacional acreditada de contigüidad, islas, enclaves y discontinuidades; overlay, solapamientos y contactos no certificados por N07.
- Grafo: falta acreditar fronteras compartidas válidas, conectividad y ausencia de aristas ficticias dentro de cada provincia.
- Componentes físicos: falta inventario nominal y poblacional y prueba de factibilidad con la cuota provincial, sin inferir excepciones.
- Disciplina municipal: siguen pendientes unidad mínima y régimen de indivisibilidad/subdivisión municipal.
- Límites poblacionales internos: falta fijar y acreditar umbrales operacionales; 120.000 y el redondeo de K no los sustituyen; Soria/Ceuta/Melilla mantienen excepción poblacional expresa.
- Compatibilidad M01–M06: falta evidencia del consumo nacional de entradas, grafo y componentes, cuotas y barreras provinciales, límites internos y manifiestos de salida, sin heredar K/floor/cap autonómicos.

No se declara READY. Esta integración no acredita topología, contigüidad, disciplina municipal ni factibilidad del motor. No se ejecutan piloto, 00 ni M01–M08 productivos.
