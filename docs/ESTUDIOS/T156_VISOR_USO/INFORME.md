# T-156 · Visor: accesibilidad, peso y medición de uso (10-11)

Solo lectura y documento. Auditado: el sitio construido en local desde `main` (mismas copias que el paso «Construir sitio candidato» de `_reutilizable-publicar-sitio.yml`: v1, `/nacional/`, `/v2/`, `/dashboard/`), con Chromium + Playwright 1.63 y axe-core 4.10.2 (reglas wcag2a/2aa/21aa + best-practice). MapLibre 5.7.0 y axe se bajaron del registro npm a la carpeta temporal (no instalado nada en el repo) porque unpkg no es alcanzable. Script y resultados crudos: `auditoria_visor.js`, `axe_resultados.json`.

## No se pudo comprobar
- **El sitio publicado** (github.io, zenodo): no alcanzable. Lo publicado puede diferir si no está al día con `main`.
- Datos generados en CI y ausentes en local: `datos/` (INDEX, resultados), `v2/datos/{territorial,rotacion}.json`, `secciones/`. Por eso Territorial, Rotación y Secciones salen «sin datos» y no se auditaron sus estados activos; `/nacional/` quedó sin polígonos.
- Teselas de OpenStreetMap (v1 y nacional) y MapLibre desde CDN: sin red; el peso del CDN se ha medido con el paquete npm (mismo fichero).
- Lector de pantalla real (NVDA/VoiceOver) y mapa operado solo con teclado: no probados; solo reglas automáticas (cubren ~30-40 % de los problemas reales).
- Tiempos de carga: el estrangulamiento de red de Playwright no afecta a lo servido por `route()`; los tiempos son **estimados** (peso ÷ ancho de banda + viajes de ida y vuelta), no medidos.

## (a) Peso y carga de `/v2/` (portada)
| Recurso | Sin comprimir | gzip |
|---|---|---|
| MapLibre JS (unpkg) | 939 KB | 249 KB |
| `provincias.json` | 358 KB | 102 KB |
| `comunidades.json` | 161 KB | 46 KB |
| `v2.js` + `v2.css` + HTML + textos | 60 KB | 18 KB |
| MapLibre CSS | 69 KB | 10 KB |
| **Total (sin teselas)** | **~1,59 MB** | **~425 KB** |

(La suma automática del informe, 2,0 MB / 538 KB, cuenta dos veces `provincias.json` y el CSS de MapLibre: ver defecto 4.)
Estimación (todo en serie, ~8 viajes): **3G lenta (400 kbit/s, 400 ms)**: ~9 s de transferencia + ~3 s de latencia ≈ **12-13 s** hasta mapa; **4G (9 Mbit/s, 170 ms)** ≈ **1,5-2 s**. Móvil (Pixel 7, 412 px): sin desbordamiento horizontal; DOMContentLoaded 0,4-1,8 s con los ficheros propios estrangulados.
Otras páginas (gzip): v1 ≈ 278 KB, nacional ≈ 274 KB (más teselas OSM, no medidas), dashboard ≈ 50 KB (`status.json` 444 KB → 37 KB), hemiciclo/métricas < 5 KB.
Con las capas de CI el peso crece: no medido (secciones censales por provincia, tamaño desconocido en local).

## Defectos priorizados
**Alta**
1. **`/v2/` sin `<h1>` visible**: los títulos salen de `web/textos.md`, hoy vacío; la página no tiene encabezado de nivel 1 (axe `page-has-heading-one`) y las secciones aparecen sin título. Lector de pantalla: sin estructura. Se resuelve al escribir los textos; mientras tanto, un `<h1>` fijo de respaldo en el HTML.
2. **Sin contenido sin JS ni fallo controlado**: si falla unpkg o un JSON, el mapa queda vacío sin mensaje (en local, los 404 de `datos/*.json` opcionales salen en consola, sin aviso al usuario salvo el chip «sin datos»). Añadir `<noscript>` y mensaje de error del mapa.
3. **Dependencia de unpkg.com** (3 CDNs sin `integrity` ni copia propia): un caído/bloqueo deja v1, v2 y nacional sin mapa; riesgo de cadena de suministro. Opciones: alojar MapLibre en el sitio (gzip 259 KB) o fijar con `integrity` (SRI) + `crossorigin`.

**Media**
4. **Doble descarga**: `v2.js` pide `datos/provincias.json` dos veces (líneas 56 y 144) y MapLibre CSS aparece dos veces en la red (precarga + hoja); unificar en una promesa.
5. **Contraste** (axe, serious): etiquetas «Sistema/Capa/Vista» en v2 (#68716d sobre #f6f1e7, 4,47:1 con 10 px negrita; mínimo 4,5) — 5 nodos; dashboard `.bad > p` (4,49:1) — 2 nodos; enlaces v1 y nacional (atribución MapLibre) 2,02:1 con el texto circundante (mínimo 3:1, ahí sin subrayado). Arreglo de una línea de CSS cada uno. Además axe dejó «por revisar» 6 contrastes en el dashboard y 1 en v2/nacional/hemiciclo (fondos con degradado o gráfico).
6. **Objetivos táctiles pequeños**: 18 de 35 controles de `/v2/` miden menos de 44×44 px en móvil (WCAG 2.2 AA exige 24×24; 44 es la recomendación). Revisar `.chip` y `.tab`.
7. **Sin enlace «saltar al contenido»** en ninguna página (la cabecera con pestañas obliga a ~10 tabulaciones antes del mapa en v2).
8. **Mapa**: el lienzo no tiene etiqueta ni equivalente textual propio; hay `region-chip` y ficha con `aria-live` como alternativa, pero no se verificó con lector de pantalla que se pueda elegir provincia solo con teclado.
9. **Dashboard**: `status.json` 444 KB (37 KB gzip) para una página de estado; `.side-stack` es un `aside` anidado en otro landmark (moderate).

**Baja**
10. Hemiciclo: `th-has-data-cells` por revisar. 11. `aria-allowed-role` por revisar en v2 (`role="button"` sobre `.model`, v2.js:62; usar `<button>`). 12. Teselas OSM (v1/nacional): sin atribución comprobada ni caché propia; dependen de un tercero con política de uso limitada.

**Bien**: foco visible en todos los controles (0 sin contorno), `prefers-reduced-motion` respetado, `lang="es"`, `viewport` correcto, `aria-pressed/aria-live/role=img` con etiqueta en el hemiciclo, sin desbordamiento en 412 px, nada de `localStorage`/cookies/terceros de seguimiento (solo unpkg y OSM, que ven la IP del visitante).

## (b) Medir uso sin cookies ni rastreo de personas
Condición de partida: el sitio es estático (GitHub Pages) y **no tiene ningún script de analítica ni cookie**. En Pages no hay registros de servidor accesibles, así que «solo registros agregados» exige un servicio delante (no hay opción sin añadir algo). Precios y condiciones: de memoria, **verificar antes de decidir**.

| Opción | Datos que da | Coste (orientativo) | Privacidad | Qué añadir a la web |
|---|---|---|---|---|
| **Cloudflare Web Analytics** | Páginas vistas, visitantes únicos aproximados, país, referrer, navegador/dispositivo, Core Web Vitals (rendimiento real). Sin eventos propios. | Gratis | Sin cookies ni huella individual; datos en Cloudflare (EE. UU./UE). Con balizas JS no hace falta mover el DNS. | Una línea `<script defer src=".../beacon.min.js" data-cf-beacon='{"token":"…"}'>` en cada HTML y cuenta Cloudflare. |
| **GoatCounter** | Visitas por página, referrer, país, navegador, tamaño de pantalla, tendencia; eventos propios con `goatcounter.count()` (p. ej. cambio de capa). | Gratis para uso no comercial (donación) o autoalojable (binario Go + SQLite) | Sin cookies, sin IP guardada; código abierto; script ~3,5 KB; sin banner. | `<script data-goatcounter="https://<sitio>.goatcounter.com/count" async src="//gc.zgo.at/count.js">` + opcional `count()` en `setTab`/`cambiar`/`ponCapa` de v2.js. |
| **Plausible** | Como GoatCounter más objetivos/embudos, UTM, eventos con propiedades, API. | Cloud de pago (unos 9 €/mes el plan básico, por volumen) o Community Edition autoalojada gratis | Sin cookies ni IP guardada; UE (Alemania) en cloud; script ~1 KB. | `<script defer data-domain="…" src="https://plausible.io/js/script.js">` + `plausible('capa',{props})`; autoalojado exige un servidor (Docker, ClickHouse). |
| **Solo registros agregados propios** | Nada hoy (Pages no entrega logs). Con proxy/Worker de Cloudflare o un servidor propio: peticiones por ruta, código, país. Sin JS en el cliente. | Cloudflare gratis hasta cierto volumen; servidor propio = mantenimiento | Máxima: ni script ni dato en el navegador; cuenta bots y cachés, no personas. | Mover el dominio detrás de Cloudflare (cambio de DNS, decisión del propietario) y consultar su analítica de zona. Sin dominio propio no es posible. |
| Complemento sin cambios | Pestaña «Traffic» de GitHub (visitas/clones del repo, 14 días): mide el repositorio, no el visor. Descargas del release/Zenodo: contadores propios. | Gratis | — | Nada. |

Recomendación técnica (opciones, no decisión): para solo «cuánta gente entra y por dónde» → **Cloudflare Web Analytics** (cero coste, una línea); si se quiere saber qué usa (pestañas, capas, provincias elegidas) → **GoatCounter** (eventos, gratis, abierto). Ambos añaden un tercero que recibe la petición del script; hay que anotarlo en la página de privacidad/metodología (no existe hoy) y decidir si el lugar de tratamiento importa. Para la RGPD/LSSI: sin cookies ni almacenamiento en el equipo no se requiere banner en los tres, pero la conveniencia de aviso legal/privacidad y la base jurídica la fija el propietario (consultar, no asesoro). Cualquier opción exige tocar `visor/index.html`, `visor/nacional/`, `visor/v2/index.html` y el dashboard (ficheros compartidos: coordinar) y cambia el CSP si se añade uno; nada se ha instalado.
