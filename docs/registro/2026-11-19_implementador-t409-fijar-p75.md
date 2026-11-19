## 2026-11-19 — T-409 — Fijar en el repo el run de P75 que publica P40 (doble vuelta V4)

Causa: #927 fusionada; P40 solo publica la doble vuelta de los 52 nac si `configuracion/doble_vuelta_publicada.json` fija el run de P75. Cambio: nuevo `configuracion/doble_vuelta_publicada.json`:
elección 2023-07, `run_p75` `44575597009-1`, clave `doble_vuelta/2023-07/44575597009-1/INFORME.json` y `informe_sha256` `c127f66b…711c`, huella verificada por el Coordinador en el log del job de P75
(run 44575597009, 52/52 OK; no la he podido comprobar yo: R2 y los artefactos no son accesibles desde la nube). Test de formato (`tests/test_t419_publicar_doble_vuelta.py`, clase `Fijado`): claves y tipos, clave coherente con el run,
valores literales y control negativo (un informe distinto con esa clave falla con `INFORME_SHA256_DISTINTO`). Sin código ni workflows. Efecto: la próxima P40 que publique bajará de R2 ese resultado y exigirá esa huella; sin publicar ni lanzar. `no-automerge`.
