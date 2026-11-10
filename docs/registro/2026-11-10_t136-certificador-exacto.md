## 2026-11-10 — T-136 — Prototipo de certificador exacto (CP-SAT)

- **Causa:** decisión del propietario sobre el motor (opción B, punto B): saber si una circunscripción admite una
  partición válida, cuál es la mejor o probar que no existe, con las mismas reglas que la validación de producción.
- **Cambio:** `herramientas/certificador_exacto.py` 1.0.0 (nuevo): modelo OR-Tools CP-SAT con las reglas de
  `validar_ejecucion.py` 1.3.5 (K, población con exenciones, contigüidad M03 por árbol padre/nivel, provincia,
  disciplina municipal R012), objetivos factibilidad, minimax y techo mínimo, pista desde una composición y
  comprobación independiente de la solución. Estudio en `docs/ESTUDIOS/T136_CERTIFICADOR_EXACTO.md`. No toca el motor.
- **Resultados:** Cádiz con techo 115 % es infactible (prueba en 29 s) y el techo mínimo es 1,15919× (óptimo, igual
  11/11 al publicado); Huesca admite equilibrio exacto (motor ±71 hab.); Madrid (3.603 átomos, K=59) no es tratable
  con el modelo monolítico (8 GB, sin respuesta).
- **Pruebas:** `python -m unittest tests.test_certificador_exacto` (4 tests; se saltan sin `ortools`).
- **Modo de 00:** ninguno (herramienta de diagnóstico).
