## 2026-11-23 — T-440 — Medir la web como un navegador y distinguir el bloqueo del CDN

- **Causa:** el run de `medir-web` 45087927501 dio 403 en todas las páginas desde el runner (respuestas de 3-5 KB en ~50 ms) salvo `/mapa/explorar.js`: es el filtro de bots de Cloudflare ante el `User-Agent` de `curl`, no la web caída, y la tabla no lo distinguía.
- **Cambio:** `herramientas/medir_web.py` 1.1.0 (copia de 1.0.0 en `legacy/`): pide con `User-Agent`, `Accept` y `Accept-Language` de navegador; lee las cabeceras `cf-mitigated` y `server` (`%header{…}` de curl ≥ 7.84; el runner trae 8.5) y marca «403 (bloqueado por el CDN)» cuando el 403 lo da Cloudflare; añade un aviso al pie con el recuento. Si nada responde 200 y es por el CDN, avisa y sale 0; si no, error como antes.
- **Pruebas:** `tests/test_t440_medir_web.py` (cabeceras de navegador, 403 de Cloudflare con y sin `cf-mitigated`, un 403 de la web no cuenta como CDN, tabla y aviso, salida 0 con todo bloqueado y 1 con todo caído). Gobernanza en local.
- **Riesgos:** ninguno (solo lectura). Si el bloqueo persiste con cabeceras de navegador, la decisión es del propietario en Cloudflare (ver la PR).
