## 2026-11-10 — T-132 — Banco de generadores: validez y calidad en los 71 territorios

**Causa.** Petición del Planificador tras la matriz base: completar la comparación de generadores (A) con los territorios
grandes, medir la calidad (no solo la validez) y probar la semilla de factibilidad del certificador exacto (T-136).
Los resultados llegaron a la rama de #601 después de su fusión.

**Cambio.** Solo resultados en `docs/ESTUDIOS/T132_BATERIA_MOTOR/`: `BANCO.csv` (validez por territorio, generador y
semilla), `CALIDAD.csv` (fuera de tolerancia, desvío máximo, ECM, municipios partidos, distritos mixtos, Polsby-Popper) y
`RESUMEN_GENERADORES.md`. El código (`herramientas/banco_generadores.py` y `requirements-banco-motor.lock`) ya está en main
por #601.

**Resultado.** Canónico 71/71; GerryChain de producción 355/355 (mejor de 5: mejora 19, empata 45, empeora 6 frente al
canónico); semilla por árboles + ReCom 188/355 (30/71 siempre válidos); semilla exacta CP-SAT + ReCom 3/5 (La Rioja y Madrid
sin respuesta en 900 s).

**Pruebas.** Sin código nuevo; datos generados en local con `banco_generadores.py ejecutar|matriz|calidad`.
