# T-519 · Verificación independiente

Fecha: 2026-11-28. Veredicto: **CONFIRMADO**. Las cifras cuadran; `INFORME.md` no se ha corregido.

- **Tabla frente a los ficheros.** Releídos los 20 `COMPETICION.json` con un guion propio (sin `tabla.py`): ganador,
  clave D8, estado y etapas del exacto, `huella_resultado`, composición y reloj coinciden con `RESULTADOS.json` y con
  las 20 filas del informe (0 diferencias). El sha256 de cada composición es el del CSV del ganador en disco.
- **Frente a T-507** (`RESULTADOS.json` de `main`; esta rama no lo trae): mismo plan en las 4 de Castellón, La Coruña,
  Guipúzcoa y Sevilla; en Tarragona, en 2 de 4.
- **Ejecución repetida por mí.** La Coruña (nac15, el más rápido en reposo), competición completa, sola en la máquina,
  104 s, commit 4adc9712: ganador exacto, `huella_resultado` 5422228aaf3a…, composición c39a0bbc8ec9…, los 13
  candidatos iguales a los de «reposo 1». La cota de la etapa abierta sale 241.807.973: un quinto valor distinto.
- **La conclusión se sigue de los datos**, con una precisión: «reposo 1» y «reposo 2» corrieron a la vez (lo dice el
  método) y ninguna de las 20 fue sola. Los datos descartan la velocidad como causa; que la causa sean los 4 hilos
  es una hipótesis razonable, no una medida.
- **Motor sin cambios**: de 548968c4 al `main` de hoy (536a7898) no cambian `ddd_motor2`, `paquetes` ni los `.lock`.
- **El arreglo (`HILOS = 1`)** es el más pequeño en código y el único de los vistos que va a la causa: quitar el
  estado de las etapas de la huella arreglaría Castellón y no Tarragona, y quedarse con el plan de la última etapa
  cerrada no vale, porque que una etapa cierre es justo lo que cambia. Pero no está medido y es el de mayor alcance.
- **No comprobado**: que con un hilo se repita; la frecuencia de cada mapa de Tarragona; otra clase de máquina.
