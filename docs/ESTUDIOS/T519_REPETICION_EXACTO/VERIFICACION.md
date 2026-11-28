# T-519 · Verificación independiente

Fecha: 2026-11-28. Veredicto: **CONFIRMADO**. Las cifras cuadran; `INFORME.md` no se ha corregido.

- **Tabla frente a los ficheros.** Releídos los 20 `COMPETICION.json` de la medición con un guion propio (sin
  `tabla.py`): ganador, clave D8, estado y etapas del exacto, `huella_resultado`, composición y reloj coinciden con
  `RESULTADOS.json` y con las 20 filas del informe (0 diferencias). El sha256 de cada composición es el del CSV del
  ganador en disco. El recuento por territorio (mapas, huellas, estados, cotas) y los 47 min de reloj también cuadran.
- **Frente a T-507.** Comprobado contra `docs/ESTUDIOS/T507_EXACTO_K5/RESULTADOS.json` de `main` (esta rama no lo
  trae): mismo plan en las 4 de Castellón, La Coruña, Guipúzcoa y Sevilla; en Tarragona, en 2 de 4.
- **Ejecución repetida por mí.** La Coruña (nac15, el más rápido en reposo), una competición completa, sola en la
  máquina, 104 s, commit 4adc9712: ganador exacto, `huella_resultado` 5422228aaf3a…, composición c39a0bbc8ec9…, los 13
  candidatos iguales a los de «reposo 1». La cota de la etapa abierta (frontera) sale 241.807.973: un quinto valor.
- **La conclusión se sigue de los datos**, con dos precisiones. «Reposo 1» y «reposo 2» corrieron a la vez (lo dice
  el método): ninguna de las 20 fue sola. Los datos descartan la velocidad como causa (un núcleo coincide con una de
  las de reposo), pero no prueban que sea el número de hilos: eso es una hipótesis razonable, no una medida.
- **Motor sin cambios.** De 548968c4 a `main` de hoy (536a7898) no cambian `ddd_motor2`, `paquetes` ni los `.lock`.
- **El arreglo (`HILOS = 1`).** Es el más pequeño en código (una constante) y el único de los vistos que va a la
  causa. Quitar el estado de las etapas de la huella arreglaría Castellón y no Tarragona. Quedarse con el plan de la
  última etapa cerrada tampoco vale: que una etapa cierre es justo lo que cambia. Pero no está medido y es el de
  mayor alcance: cambia plan y huella en todo territorio con exacto y obliga a repetir T-507.
- **No comprobado.** Que con un hilo el resultado se repita (ni en Tarragona ni en Castellón); la frecuencia de cada
  mapa de Tarragona; otra clase de máquina. Solo he repetido una ejecución, como pedía el encargo.
