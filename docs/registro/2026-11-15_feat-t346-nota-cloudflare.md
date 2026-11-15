## 2026-11-15 — T-346 — Transparencia: el sitio lo sirve Cloudflare (informes NEL/Report-To con la IP)
- Causa: el contador sin cookies devuelve 204 sin Set-Cookie pero con cabeceras NEL/Report-To; el navegador puede enviar informes de red a a.nel.cloudflare.com con la IP, y el texto de transparencia no lo decía (decisión del propietario, opción 1).
- Cambio: una frase añadida al párrafo «Medición de visitas» de `visor/index.html` (V1, 1.4.5), `visor/v3/index.html` y `web/textos.md` (que alimenta V2 y el sitio), tras la frase de la infraestructura; no contradice lo prometido. Nacional y Congreso no llevan ese párrafo (solo la nota de OSM): sin cambio.
- Pruebas: `tests/test_visor_analitica.py` 2.1.0 (test nuevo de la frase), `tests/test_visor_sin_terceros.py`, GovernanceHeaders.
- Riesgos: ninguno en motor, workflows ni huellas; no se publica: el sitio sale con la P50.
