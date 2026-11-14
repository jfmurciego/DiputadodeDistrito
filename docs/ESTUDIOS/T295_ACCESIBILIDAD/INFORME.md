# T-295 · Accesibilidad WCAG 2.1 AA del visor V3

Ámbito: `visor/v3/` (index.html, v3.css, v3.js 1.2.0), sobre #763 (panel de procedencia incluido). V2 no se toca (sus contratos y tests, sin beneficio barato).
Método: revisión estática del marcado, CSS y JS + pruebas en Node (`tests/test_visor_v3_ui.js`); contrastes calculados con la fórmula WCAG. No se ha probado con lector de pantalla real ni con navegador: queda como verificación manual recomendada.

| Criterio | Hallazgo | Estado |
|---|---|---|
| 1.1.1 Texto alternativo | Botones `⌖ P C` solo con `title`; glifos de modos leídos por lectores | Arreglado: `aria-label` y glifos `aria-hidden` |
| 1.3.1 Información y relaciones | Mapa solo visual; sin equivalente textual | Arreglado: tabla «Resultados en tabla» (provincia, ganador por nombre, %, escaños) con `caption`, `th scope` |
| 1.3.1 Landmarks | `aside` sin nombre; leyenda sin rol | Arreglado: `aria-label`, `role=group` |
| 1.4.1 Uso del color | Partido solo por color en el mapa | Parcial: leyenda con nombre y borde, tabla con nombre de partido. No se añaden patrones al mapa: cambiaría el diseño visual y exige imágenes MapLibre; la tabla cubre la información |
| 1.4.3 Contraste texto | Grises #6e7078/#737078/#777/#78747a (<4,5:1) y fin del degradado del encabezado (~4,0:1 con texto blanco) | Arreglado: texto #575962; degradado oscurecido al final (#7d5547). Colores de partido sin cambios |
| 1.4.4 / 1.4.10 Zoom y reflow | Leyenda y cabecera desbordaban a 320 px | Arreglado: `@media(max-width:480px)` (leyenda, nav, tarjetas, tabla con scroll propio). Sin verificar visualmente |
| 1.4.11 Contraste no textual | Bordes de controles (#d8d7d7 ≈1,4:1) y foco naranja (2,1:1); swatches sin borde | Arreglado: bordes #868992 (≥3:1), foco #14161a con halo blanco, borde en swatches |
| 2.1.1 Teclado | Mapa inalcanzable para elegir territorio | Arreglado: tabla con botones por provincia; buscador ya existente; ayuda con atajos de MapLibre (flechas, +/−) |
| 2.4.1 Saltar bloques | No había | Arreglado: enlace «Saltar al mapa» |
| 2.4.3 Orden/foco | Recrear la tabla al seleccionar perdería el foco | Evitado: la tabla solo se regenera si cambia ámbito/elección |
| 2.4.7 Foco visible | Existe pero con bajo contraste | Arreglado (ver 1.4.11) |
| 2.2.2 / 2.3.3 Movimiento | `fitBounds` animado, sin respeto de preferencias | Arreglado: `duration:0` y CSS con `prefers-reduced-motion` |
| 2.5.5 Tamaño de objetivo (AAA, cubre 2.5.8 de 2.2) | Botones de ~24–30 px | Arreglado: mínimo 36 px en controles principales; casillas de opciones no ampliadas |
| 3.1.1 Idioma | `lang="es"` ya presente | Correcto. Controles de MapLibre ahora en español (`locale`) |
| 4.1.2 Nombre, rol, valor | `aria-pressed` correcto en segmentos; `dialog` sin nombre | Arreglado: `aria-labelledby`, `aria-haspopup` |
| 4.1.3 Mensajes de estado | `aria-live` en toda la columna (ruido) y en procedencia | Arreglado: una sola región `#sr-status` que anuncia tipo, nombre, ruta y datos de la selección; `#map-notice` ya era `role=status` |

## No arreglado
- Patrones/texturas en el polígono del mapa (1.4.1): alteraría el diseño; mitigado por tabla y etiquetas de provincia.
- `role="application"` del mapa: se mantiene (MapLibre gestiona teclado); descrito con `aria-describedby`.
- Orden de encabezados (h2 de herramientas antes del h1): no se reordena para no cambiar el diseño.
- Cambiar de capa/nivel no anuncia el cambio de mapa (solo la selección y avisos).
- V2: fuera de alcance.
