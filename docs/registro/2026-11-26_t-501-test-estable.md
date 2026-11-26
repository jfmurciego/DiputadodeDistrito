## 2026-11-26 — T-501 — Test inestable del Explorar: `flush` espera a la condición

**Causa.** `tests/test_visor_v4_explorar_aut.js:146` (Castilla-La Mancha) fallaba de forma intermitente: 2 de 40 ejecuciones en `main` limpio y 3 de 25 en una rama. El `flush` de las pruebas del Explorar daba 60 vueltas fijas del bucle de eventos y a veces no bastaban mientras la verificación sha256 (hilos de Node) seguía en curso. La causa es una inferencia por la frecuencia y el punto del fallo, confirmada porque con la espera por condición no vuelve a fallar.

**Cambio.** En `test_visor_v4_explorar.js` 1.2.0, `test_visor_v4_explorar_aut.js` 1.2.0 y `test_visor_v4_explorar_actual.js` 1.1.0 (copias anteriores en `legacy/tests/`), el navegador simulado cuenta el trabajo asíncrono pendiente (cada `fetch` y cada `crypto.subtle.digest`) y `flush` espera a que no quede ninguno durante 10 vueltas seguidas; si no se estabiliza en 15 s, la prueba falla con un mensaje claro. No se salta ni se pone en cuarentena ningún test y no cambia ningún valor esperado.

**Pruebas.** 200 ejecuciones seguidas en local de cada una de las tres pruebas (600 en total): 0 fallos (aut 0/200, explorar 0/200, explorar_actual 0/200). Antes: aut 3/25 y 2/40 en `main`.

**Riesgos.** Ninguno de producto (solo tests). `test_visor_v4_puntos.js` (T-500, #1017) tiene un `flush` del mismo tipo; se adapta aparte cuando entre esa PR.
