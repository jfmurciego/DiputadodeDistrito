## 2026-11-10 — T-163 — Motor 2: semilla pública de la competición (paso 2)

- Causa: D-48: las N semillas de GerryChain se derivan de un dato oficial fijado de antemano (misma entrada ⇒ mismo mapa).
- Cambio: `ddd_motor2/semilla.py` (esquema `ddd-semilla-publica/1`, ancla PROPUESTA a confirmar por el propietario):
  sha256 del padrón (rol `population`) y del seccionado (rol `target_sectioning`) declarados en
  `generation_state.source_inputs` del contrato + territorio + i; semilla_i = sha256(...)[:16] mod (2^31−2) + 1. Sin huella,
  `ErrorContrato` (nunca semilla fija). Los 71 contratos de la batería la traen.
  `competicion.py` 1.1.0: `competir_publico(entrada, canonico, cadena, destino, n_cadenas=5)` y `Resultado.huella()`
  (reglas, semillas, plan y sha256 de la composición de cada candidato; sin tiempos ni rutas).
- Pruebas: `python -m unittest tests.test_motor2_semilla` (fórmula, dependencia del dato y del territorio, fallo sin
  huella, dos ejecuciones con huella idéntica).
- Siguiente: informe por territorio (paso 3).
