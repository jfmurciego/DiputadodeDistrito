## 2026-11-10 — T-174 — Hueco de analítica sin cookies (Cloudflare Web Analytics), inactivo sin token

**Causa.** El propietario eligió Cloudflare Web Analytics para medir uso sin cookies (nota `docs/ESTUDIOS/T156_VISOR_USO/`).

**Cambio.** Bloque `ANALITICA:INICIO…FIN` idéntico antes de `</body>` en `visor/index.html` (1.4.2), `visor/nacional/index.html` (1.0.2) y `visor/v2/index.html`; copias en `legacy/`. `TOKEN=""` en el repo: sin token no se inyecta nada. Con token añade solo `https://static.cloudflareinsights.com/beacon.min.js` (`data-cf-beacon={"token":…}`) y un aviso breve de privacidad con enlace a la documentación de Cloudflare. No usa cookies ni almacenamiento (el código no los toca). No hay CSP en el sitio; no se añade. No se tocan workflows (v1 y nacional se copian como HTML, por eso el bloque va en línea); el dashboard no incluye el bloque.

**Pruebas.** `tests/test_visor_analitica.py` (Node, DOM mínimo): bloques idénticos y token vacío; sin token, cero nodos; con token, solo el beacon de Cloudflare más el aviso; únicos hosts permitidos en el bloque.

**Riesgos / pendiente.** El entorno no alcanza `developers.cloudflare.com`: las afirmaciones del aviso («no usa cookies ni almacenamiento local, no sigue entre sitios», y el host del beacon) no se han verificado contra su documentación; la URL citada es la portada de Web Analytics (fecha de consulta pendiente: 2026-11-10, no leída). Verificar antes de activar. Despliega con la próxima publicación del visor (permiso del propietario en el chat del Operador). Para activarlo, el propietario crea el sitio en Cloudflare Web Analytics, copia el token del beacon y se pone en `TOKEN=""` de las tres páginas.
