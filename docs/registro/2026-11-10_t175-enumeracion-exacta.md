## 2026-11-10 — T-175 — Enumeración exacta para territorios pequeños (motor nuevo y certificador)

- Causa: condición previa al corte 5.0.0. Donde el espacio de planes cabe, el motor nuevo debía enumerar todos los
  planes válidos y elegir con la regla de calidad vigente; el certificador debía usar la misma regla.
- Cambio: `ddd_motor2/calidad.py` 1.0.0 (regla lexicográfica única, salida de la competición), `ddd_motor2/exhaustivo.py`
  1.0.0 (decisión por `Criterio.metodo`, enumeración y mejor por calidad; CLI), `reglas/enumerar.py` 1.1.0 (mejor por
  clave), `competicion.py` 1.2.0 (candidato «exhaustivo»), `competidor.py` 1.1.0 (M05 del exhaustivo) y
  `herramientas/certificador_exacto.py` 1.4.0 (`mejor_por_calidad` en `--objetivo enumerar`). Sin cambios en producción,
  huellas ni workflows.
- Resultados (`docs/ESTUDIOS/T136_CERTIFICADOR_EXACTO.md`): Álava, 1 plan válido exacto por las dos vías, igual al
  publicado; Soria (K=1), 1 plan. Huesca, Lugo y Albacete no terminan: 200.000 nodos en 125 s en Huesca y 2.000.000
  en 601-732 s en Lugo y Albacete, sin planes vistos; CP-SAT, solo recuentos parciales.
- Pruebas: `python -m unittest tests.test_motor2_exhaustivo tests.test_motor2_competicion tests.test_motor2_competir tests.test_motor2_informe tests.test_motor2_semilla tests.test_motor2_competidor tests.test_motor2_reglas tests.test_certificador_nucleos tests.test_certificador_exacto tests.test_certificador_ligero`.
