## 2026-11-14 — T-295 — Accesibilidad WCAG 2.1 AA del visor V3

Causa: el visor V3 dependía del color y del puntero (mapa sin equivalente textual ni teclado), con foco y grises de bajo contraste, botones sin nombre accesible y sin respeto de `prefers-reduced-motion`.
Cambio: `visor/v3/v3.js` 1.2.0 (anuncio de la selección, tabla alternativa operable con teclado, movimiento reducido, controles de MapLibre en español), `v3.css` 1.1.0 (foco, contraste, objetivos, reflow 320 px) e `index.html` (enlace de salto, nombres accesibles, región viva). Informe en `docs/ESTUDIOS/T295_ACCESIBILIDAD/INFORME.md`; copias en `legacy/`. Sin cambio de datos ni colores de partido.
Pruebas: `tests/test_visor_v3_ui.js` 1.2.0 (marcado, contrastes, anuncio, tabla).
Riesgos: construida sobre la rama de #763 (debe entrar antes). Sin verificar con lector de pantalla ni navegador real. Sin 00 ni P50.
