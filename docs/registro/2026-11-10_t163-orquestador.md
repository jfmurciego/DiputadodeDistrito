## 2026-11-10 — T-163 — Motor 2: orquestador de la competición canónico + GerryChain (paso 1)

- Causa: D-48: la primera versión del motor nuevo es una competición canónico + GerryChain bajo el núcleo de reglas.
- Cambio: `ddd_motor2/competicion.py` (solo stdlib): `competir(entrada, canonico, cadena, semillas, destino)` ejecuta el
  canónico y una cadena por semilla mediante adaptadores (protocolo `Generador` → composición M06), juzga todos con
  `problema_y_plan` + `evaluar` (Criterio D-44 por defecto) y elige por clave lexicográfica: evaluable → violaciones duras
  → fuera de tolerancia → desvío máximo → ECM (fracciones exactas) → huella del plan (sin etiquetas) → orden (canónico
  primero). Núcleos cerrados con la composición del canónico como referencia común. Un generador que falla queda fuera
  sin tumbar la competición.
  `ddd_motor2/generadores.py`: adaptadores reales `Canonico` (`bateria_motor.motor_uno`, M05 7.4.4) y `GerryChain`
  (`banco_generadores.ejecutar_uno`, `ddd_core/m05_gerrychain_strategy.py`: la de producción y la única con evidencia en
  los 71) y `entrada_bateria(t, out)`. No se toca producción, huellas, `ddd_core` ni workflows.
- Pruebas: `python -m unittest tests.test_motor2_competicion` (generadores sintéticos).
- Siguiente: semilla pública (paso 2), informe por territorio (paso 3), interfaz para la batería T-132 (paso 4).
