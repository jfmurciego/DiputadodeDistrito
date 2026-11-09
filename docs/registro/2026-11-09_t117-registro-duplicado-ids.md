## 2026-11-09 — T-117 — El error de activo duplicado nombra las dos entradas

Causa: la 05 42538420980 (production_run_id=42531122768, Castilla y León) falló en «Construir candidato» con «Activo inmutable duplicado» sin decir qué entradas colisionaban; el blob 5143b70a no está en el registro de main, así que chocan dos entradas nuevas del mismo run.
Cambio: `registro_publicaciones_visor.py` 1.3.0; una ubicación inmutable (blob de git, direccionable por contenido) puede servir a entradas de distinta identidad si el sha256 coincide; si no coincide, error que nombra ambas entradas. Cada entrada se verifica por separado.
Pruebas: `tests.test_registro_escenarios`, `GovernanceHeaders`. Riesgo: si el M08 es byte-idéntico al M06, queda registrado sin aviso (revisar el 00).
