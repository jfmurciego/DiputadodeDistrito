## 2026-11-10 — T-163 — Motor 2: orquestador de la competición canónico + GerryChain (pasos 1-3: orquestador, semilla pública, informe)

- Causa: D-48: la primera versión del motor nuevo es una competición canónico + GerryChain bajo el núcleo de reglas.
- Cambio: `ddd_motor2/competicion.py` (solo stdlib): `competir(entrada, canonico, cadena, semillas, destino)` ejecuta el
  canónico y una cadena por semilla mediante adaptadores (protocolo `Generador` → composición M06), juzga todos con
  `problema_y_plan` + `evaluar` (Criterio D-44 por defecto) y elige por clave lexicográfica: evaluable → violaciones duras
  → fuera de tolerancia → desvío máximo → ECM (fracciones exactas) → huella del plan (sin etiquetas) → orden (canónico
  primero). Núcleos cerrados con la composición del canónico como referencia común. Un generador que falla queda fuera
  sin tumbar la competición; sin referencia de núcleos y con unidades cerradas, ERROR_DATOS; `Resultado.valido` dice si
  el ganador es válido.
  `ddd_motor2/generadores.py`: adaptadores reales `Canonico` (`bateria_motor.motor_uno`, M05 7.4.4) y `GerryChain`
  (`banco_generadores.ejecutar_uno`, `ddd_core/m05_gerrychain_strategy.py`: la de producción y la única con evidencia en
  los 71) y `entrada_bateria(t, out)`. No se toca producción, huellas, `ddd_core` ni workflows.
- Pruebas: `python -m unittest tests.test_motor2_competicion` (generadores sintéticos).
- Cambio: `ddd_motor2/semilla.py` (esquema `ddd-semilla-publica/1`, ancla PROPUESTA a confirmar por el propietario):
  sha256 del padrón (rol `population`) y del seccionado (rol `target_sectioning`) declarados en
  `generation_state.source_inputs` del contrato + territorio + i; semilla_i = sha256(...)[:16] mod (2^31−2) + 1. Sin huella,
  `ErrorContrato` (nunca semilla fija). Los 71 contratos de la batería la traen.
  `competicion.py`: `competir_publico(entrada, canonico, cadena, destino, n_cadenas=5)` y `Resultado.huella()`
  (reglas, semillas, plan y sha256 de la composición de cada candidato; sin tiempos ni rutas).
- Pruebas: `python -m unittest tests.test_motor2_semilla` (fórmula, dependencia del dato y del territorio, fallo sin
  huella, dos ejecuciones con huella idéntica).
- Cambio: `ddd_motor2/informe.py`: `escribir(resultado, carpeta)` → `COMPETICION.json` (`Resultado.a_dict()` + motivo
  frente al segundo y frente al canónico, `mejora_al_canonico`) y `COMPETICION.md` (ganador, motivo, huella, semillas
  públicas, tabla ordenada por calidad con tiempos e incidencias por regla).
- Pruebas: `python -m unittest tests.test_motor2_informe`.
- Siguiente: interfaz para la batería T-132 (PR aparte).
