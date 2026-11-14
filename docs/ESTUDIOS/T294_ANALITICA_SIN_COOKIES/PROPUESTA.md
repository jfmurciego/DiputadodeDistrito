# T-294 — Analítica del visor sin cookies (propuesta, 1 página)

Solo propuesta; no se monta nada hasta decidir el propietario (D-71, D-92). Sitio: GitHub Pages en `diputadodedistrito.es`
(estático; **sin cabeceras HTTP ni código de servidor propios**; CSP solo por `<meta>`). Pages no ofrece logs; solo «Insights →
Traffic» (14 días, con permiso de escritura).

## Privacidad y consentimiento (España; criterio técnico, no asesoría jurídica)
LSSI 22.2 exige consentimiento para leer o escribir en el dispositivo (cookies, `localStorage`, huellas). Si **no se
almacena nada en el dispositivo, no se guarda IP ni user-agent y solo se conservan contadores agregados**, no hay datos
personales (RGPD) ni acceso al dispositivo: no hace falta consentimiento ni banner. Se necesita texto de transparencia
(abajo) y conviene revisión jurídica de ese texto.

## Opciones

| | A. Contador propio (Cloudflare Worker) | B. GoatCounter autoalojado | C. Plausible CE autoalojado | D. Ninguno |
|---|---|---|---|---|
| Qué mide | cargas de página por ruta y día | páginas, referentes, país, navegador, «únicos» por hash diario | lo mismo que B, más detalle | solo tráfico de GitHub (14 días) |
| Dónde están los datos | KV/D1 de Cloudflare, solo `(día, ruta, n)` | SQLite en tu servidor | ClickHouse + Postgres en tu servidor | GitHub |
| IP / UA guardados | no (el Worker no los lee ni los registra) | no, pero la IP llega al servidor | no, pero llega al servidor | no accesibles |
| Cookie / storage | ninguno | ninguno | ninguno | ninguno |
| Coste | 0 € (plan gratuito) | VPS 4-6 €/mes (~60 €/año) | VPS ≥2 GB RAM, 6-10 €/mes | 0 € |
| Mantenimiento | muy bajo (~40 líneas, un workflow) | medio (parches, copias, HTTPS) | alto | nulo |
| Cambio en el visor | 1 línea `sendBeacon` (~100 B) + CSP `connect-src` | `<script>` ~3 KB + CSP | `<script>` ~1 KB + CSP | ninguno |
| Retirada | quitar línea, borrar Worker y DNS | quitar script, apagar servidor | igual | — |

Notas: A cuenta **cargas**, no personas únicas, y necesita un subdominio `contador.` (CNAME); Cloudflare solo transporta
la petición. B y C no encajan en Pages: exigen servidor permanente propio. Los SaaS (Plausible Cloud, GoatCounter.com,
Cloudflare Web Analytics) quedan descartados por ser terceros que ven la IP. Pruebas de cualquier opción: test que
verifique que el script no usa cookies, `localStorage`, `sessionStorage` ni `credentials`, y que lo almacenado es solo el
agregado; comprobación manual con las herramientas del navegador (almacenamiento vacío, petición sin cookies).

## Recomendación
**D hoy (no cuesta nada) y A si se quiere serie histórica**: es lo mínimo de datos, 0 €, casi sin operación y la única
que encaja con Pages sin servidor. B solo si se quieren referentes o países; C no compensa en un sitio estático.
Acción independiente: el visor v2 carga `maplibre-gl` desde `unpkg.com` (un tercero ve la IP); conviene autoalojarlo.

## Texto para el pie (opción A)
> **Medición de visitas.** Este sitio cuenta cuántas veces se carga cada página, por día. No usa cookies ni guarda nada en
> tu dispositivo, no registra tu dirección IP ni datos de tu navegador, no te identifica ni te sigue y no comparte datos
> con terceros. Solo se conserva un número por página y día. La infraestructura (alojamiento y red de entrega) trata tu IP
> de forma transitoria para entregarte la página, como cualquier servicio web.

Opción D: «Este sitio no usa cookies ni analítica propia. El alojamiento (GitHub Pages) puede tratar datos técnicos de
conexión según su política de privacidad.»
