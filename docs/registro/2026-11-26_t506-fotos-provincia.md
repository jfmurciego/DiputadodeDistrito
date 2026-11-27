## 2026-11-26 — T-506 — Fotos de provincia de vuelta en el panel de Explorar, sin créditos

**Causa.** T-459 (#1014) sacó del panel derecho la galería «Conoce el territorio» (T-325); el propietario pide recuperar la foto sin el texto de créditos.

**Cambio.** `visor/v4/mapa/index.html` 1.6.0 (sección `territory-gallery`, `galeria.js` y enlace «Créditos de las imágenes» bajo el pie; el pie común no lleva enlaces), `explorar.js` 1.7.0 (llama a `DDDGaleria.render` con `{sinCreditos, soloProvincia}`), `explorar.css` 1.4.0 (estilos de la foto, sin los del pie de créditos), `visor/v2/galeria/galeria.js` 1.1.0 (cuarto argumento opcional; sin él la V3 queda igual) y `creditos.html` 1.1.0 (enlace de vuelta a Explorar). Copias de las versiones anteriores en `legacy/`. Las 52 provincias usan las fotos y el catálogo de T-325 (autor, licencia y enlace de cada una siguen en la página de créditos, obligatorio en las CC BY).

**Pruebas.** Nuevos `tests/test_visor_v4_fotos.py` (52 rutas existen con su sha256; las 52 tienen entrada en créditos con autor, licencia y enlace; el panel no lleva texto de créditos; el pie enlaza la página) y `tests/test_visor_v4_fotos.js` (el módulo real con el catálogo real: 52 fotos cargan y sin créditos en el panel). `test_visor_v4_mapa.py` 2.3.0 (la galería ya no es id retirado). Pasan los test_visor_v4*, `test_visor_galeria_catalogo`, GovernanceHeaders, `test_t220_renombrado` y el guardián.

**Riesgos.** Ninguno de motor ni de huellas. Solo web: la P40 la lanza el Operador después. PR con `no-automerge`.
