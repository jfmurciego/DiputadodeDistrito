## 2026-11-08 — T-84 — Visor Nacional: encuadre móvil y atajo a Canarias

Causa: a 390 px el mapa inicial (centro y zoom fijos) mostraba solo el centro de la Península (aviso de T-93b), y Canarias queda fuera del encuadre inicial. Corrección de lo dicho en la PR #513: Canarias, Ceuta y Melilla SÍ están en `datos_abiertos` (49 provincias); faltan Alicante, Barcelona y Málaga, de las 52.
Cambio: `visor/nacional/nacional.js` 1.0.2 e `index.html` 1.0.1: encuadre inicial por límites (Península) y botones Península/Canarias. Copias anteriores en `legacy/visor/nacional/`.
Efectos: ninguno en módulos, huellas ni workflows; sin publicación.
Pruebas: capturas Playwright a 390 px (Península completa; Canarias), `tests.test_visor_nacional`, `GovernanceHeaders`.
Riesgos: bajos.
