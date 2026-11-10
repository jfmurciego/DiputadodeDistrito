## 2026-11-10 — T-160 — Núcleo de reglas del motor 2 (F1, paso 2: estado incremental, poda y enumerador)

- Causa: los generadores del motor 2 y el enumerador exacto deben consultar la misma definición de plan válido que
  `evaluar` (diseño en `docs/ARQUITECTURA/NUCLEO_REGLAS.md`).
- Cambio (`ddd_motor2/reglas/`, producción no lo importa; huellas intactas): `evaluar` por ámbitos (distrito,
  municipio, cuotas, núcleo, plan) compartidos con `Estado` incremental (`aplicar`, `movimiento_valido`: no añade
  violaciones nuevas); `podar` (predicados monótonos de un plan parcial) y `enumerar` (particiones canónicas con
  presupuesto de nodos, veredicto de cada hoja con `evaluar`, `completo=False` si se agota; alimenta `elegir_metodo`).
- Pruebas: `python -m unittest tests.test_motor2_reglas` (25 tests): invariante `Estado.violaciones() == evaluar(...)`
  tras movimientos aleatorios; enumerador = fuerza bruta en 25 rejillas; poda monótona contra fuerza bruta; recuento
  literal en una cadena de 4.
- Riesgo: rendimiento del `Estado` sin medir en Madrid/Barcelona (antes de F3).
