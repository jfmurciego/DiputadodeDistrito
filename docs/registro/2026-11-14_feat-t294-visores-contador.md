## 2026-11-14 — T-294 — Contador en los visores y texto de transparencia (fase 2, parte 2)

- **Causa:** el propietario eligió la opción A (contador propio sin cookies) y el texto de transparencia en el pie; el Worker ya está en `main` (#780) y los visores sirven maplibre-gl desde el sitio (T-310, #781).
- **Cambio:** una línea `sendBeacon` a `contador.diputadodedistrito.es` (solo la ruta) en `visor/index.html` (V1), `visor/v2/index.html` y `visor/v3/index.html`; sustituye el bloque inactivo de Cloudflare Web Analytics (T-174, sin token) de V1, V2 y `visor/nacional/index.html` (nacional no lleva contador: `/nacional/` no está en la lista blanca). Texto de transparencia de la propuesta, fijado por el propietario al elegir la opción A, en `web/textos.md` (`pieTexto`, V2) y como párrafo en V1 y V3. Sin CSP: los visores no la tienen. OpenStreetMap sigue como excepción pendiente de `test_visor_sin_terceros`.
- **Pruebas:** `tests/test_visor_analitica.py` 2.0.0 (copia anterior en `legacy/tests/`), `tests/test_contador_worker.py`, `tests/test_visor_sin_terceros.py` y los de visor V2/V3 en local. No publica el sitio ni despliega el Worker.
- **PR:** pendiente (`no-automerge`).
