## 2026-11-10 — T-197 — Ensayo de la noche electoral de las generales de 2026 (ZIP 2023 disfrazado)

Autorización: tarea T-197 del Planificador (local; sin lanzar ni publicar). Solo documentación y guion de ensayo; sin tocar herramientas, módulos, ddd_core ni workflows.
Causa: preparar la noche del 29-11-2026 para que solo falte cargar la fuente de Interior.
Cambio: `docs/ESTUDIOS/T197_generales_2026/ENSAYO.md` (resultado de las 52 y lista de lo que falta) y `ensayo.py` (guion reproducible).
Pruebas: ejecución local de las 52: ingestión 52/52, asignación por distrito 52/52 (30/30 idénticos al publicado de 2023), 350 escaños (50/50 iguales al oficial 2023 con la misma K), registro simulado válido.
Riesgos: ninguno en producción. Hallazgos para decisión: homologación 2026 sin cobertura de siglas de Interior, registro sin dimensión de elección, `FECHA` fija en `resultados_partidos.py`, tabla de equivalencia 2026 pendiente. No invalida huellas ni checkpoints.
