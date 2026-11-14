# T-294 — Analítica del visor sin cookies (propuesta, fase 1)

Solo propuesta: no se monta nada. Decisión del propietario antes de la fase 2. Contexto: D-71 (analítica sin cookies aplazada
hasta publicar el visor v2) y D-92 (lo público es el visor y el sitio; nada del motor entra en la analítica).

## Punto de partida (verificado en el repositorio)
- Hosting: **GitHub Pages** (P50 `desplegar-visor-publico.yml`, permisos `pages: write`, `id-token: write`) con el dominio
  `diputadodedistrito.es` (T-116/T-283) y raíz que redirige a `/v2/`. Sitio 100 % estático.
- Consecuencia: **GitHub Pages no permite cabeceras HTTP propias ni código de servidor.** La CSP solo puede ir como
  `<meta http-equiv="Content-Security-Policy">` (sin `frame-ancestors`). No hay logs de acceso para el propietario; GitHub
  solo da en «Insights → Traffic» visitas y referentes de los últimos 14 días, a quien tiene permisos de escritura.
- `visor/v2/index.html` ya carga `maplibre-gl` desde `unpkg.com` (tercero que ve la IP del visitante). Es un asunto de
  privacidad previo a cualquier analítica; la propuesta lo recoge como acción aparte (autoalojar la librería).

## Marco legal (España, resumen técnico, no asesoría jurídica)
- LSSI art. 22.2 (transposición de ePrivacy art. 5.3): consentimiento para cookies o dispositivos de almacenamiento y acceso
  **salvo** los estrictamente necesarios. La AEPD (Guía de cookies) incluye en el ámbito `localStorage`, huellas del
  navegador e identificadores; la analítica de audiencia **no está exenta** en general, aunque la AEPD admite excepciones
  de facto para analítica de medición estrictamente agregada y de primera parte si no hay identificadores persistentes ni
  cruce de datos. Criterio de diseño: **no leer ni escribir nada en el dispositivo** (ni cookie, ni `localStorage`, ni
  huella) → no entra en el art. 22.2 y no hace falta banner.
- RGPD: una IP es dato personal. Si no se recibe/guarda IP ni identificador, y solo se cuentan agregados, no hay tratamiento
  de datos personales. Un servidor de terceros que recibe la petición ve la IP técnicamente; por eso **un tercero queda
  descartado** salvo que no la registre y lo declare (ver opción b).
- Conclusión: es viable **sin consentimiento y sin banner** si (1) no hay almacenamiento en el dispositivo, (2) la IP no se
  guarda ni se usa (ni siquiera para deduplicar), (3) solo se guardan contadores agregados por ruta y día, (4) hay texto
  de transparencia. Conviene revisión jurídica de ese texto antes de publicar.

## Opciones

### (a) Contador propio con Cloudflare Worker + KV/D1 (recomendada)
- **Qué se guarda:** una fila `(fecha UTC, ruta, contador)`; opcionalmente `(fecha, país o idioma agregado)` fuera de alcance
  salvo petición. Nada más: sin IP, sin user-agent, sin referente, sin hora exacta, sin identificador de sesión.
- **Cómo se evita identificar:** el Worker solo incrementa un contador; no escribe en logs (`observability` desactivado) y
  descarta la cabecera `CF-Connecting-IP` sin leerla. Sin deduplicación por visitante → cuenta **cargas de página**, no
  personas únicas (la métrica se llama «visitas», no «visitantes»). Sin cookie, sin `localStorage`, sin huella.
  Cloudflare, como proxy, trata la IP de forma transitoria para entregar la petición (como cualquier CDN/hosting);
  se declara en la transparencia.
- **Cambio en el visor:** una línea en `visor/v2/index.html` (y V1/técnico si se desea):
  `<script>navigator.sendBeacon('https://contador.diputadodedistrito.es/v',location.pathname)</script>` (~100 bytes,
  sin cabeceras ni cuerpo con datos del usuario; `sendBeacon` no envía cookies de terceros si el Worker va en subdominio
  propio). CSP por meta: `connect-src 'self' https://contador.diputadodedistrito.es`.
- **Hosting:** requiere cuenta Cloudflare (plan gratuito: 100 000 peticiones/día de Workers, KV/D1 gratis a este volumen) y un
  subdominio CNAME `contador.` en el DNS del dominio. No exige mover el sitio: Pages sigue sirviendo. Si el DNS del dominio
  ya está en Cloudflare, no hay trabajo extra; si no, solo se delega ese subdominio.
- **Coste:** 0 € en volumen previsto; el dominio ya existe. Mantenimiento: casi nulo (un Worker de ~40 líneas en el repo,
  versionado y desplegado por workflow nuevo con `produccion`).
- **Lectura de datos:** endpoint protegido (token) o `wrangler d1 execute`; informe diario agregado que `herramientas/`
  puede volcar en un JSON público (`datos/analitica/visitas_por_dia.json`) si el propietario quiere transparencia total.
- **Pruebas:** test unitario del Worker (Miniflare/vitest) que verifique que el cuerpo almacenado solo contiene
  `(fecha, ruta, +1)` y que no hay llamadas a `console.log`/cabeceras; test de contrato del visor (el script no usa cookies,
  `localStorage`, `sessionStorage` ni `fetch` con `credentials`); prueba manual con las herramientas del navegador (pestaña
  Almacenamiento vacía, petición sin cookies).
- **Retirada:** quitar la línea del visor y borrar el Worker + registro DNS; los datos son agregados y se pueden borrar o
  conservar. Reversible en una PR + un borrado.
- **Riesgos:** abuso (inflar contadores): límite por ruta permitida (lista blanca) y tope diario; confianza en un tercero
  (Cloudflare) como infraestructura, no como analítica.

### (b) Autoalojada sin cookies (Plausible CE / Umami / GoatCounter)
- **Qué se guarda:** páginas vistas, referentes, país, navegador y SO agregados; GoatCounter y Plausible calculan «únicos» con
  un hash diario (IP+UA+sal rotatoria) que no se persiste; Umami es configurable.
- **Cómo se evita identificar:** configuración sin cookies ni `localStorage` (por defecto en Plausible/GoatCounter),
  anonimización de IP, sin banners. Más datos que (a) (user-agent, referente) → más superficie de transparencia y la IP llega
  al servidor propio, aunque no se guarde.
- **Hosting:** requiere un servidor propio (VPS ~4-6 €/mes; Plausible CE además ClickHouse + Postgres, ≥2 GB RAM; GoatCounter
  es un binario con SQLite y es la más ligera) con HTTPS, copias de seguridad y actualizaciones de seguridad. No encaja en
  GitHub Pages (hace falta servidor y proceso permanente).
- **Cambio en el visor:** un `<script defer data-domain=… src=…/script.js>` (~1-2 KB) + CSP `script-src`/`connect-src` hacia ese host.
- **Coste:** 50-70 €/año de servidor + operación (parches, copias, RGPD de un encargado propio). **Mantenimiento: el más alto.**
- **Pruebas:** como (a) más comprobar en el servidor que no hay `Set-Cookie` y que los logs de acceso del proxy no guardan IP.
- **Retirada:** quitar el script y apagar el servidor; exportar o borrar la base.
- Versión SaaS (Plausible Cloud, GoatCounter.com, Cloudflare Web Analytics) **descartada** por el criterio del encargo
  (servicio de terceros).

### (c) Sin analítica: solo agregados del hosting
- **Qué se guarda:** nada propio. GitHub Insights → Traffic (visitas únicas y totales, rutas y referentes más vistos, **solo
  14 días**, solo con acceso de escritura al repositorio). Es lo que existe hoy sin hacer nada.
- **Privacidad:** máxima: cero cambios, cero CSP, cero texto nuevo (aun así conviene un aviso breve sobre `unpkg`).
- **Limitaciones:** ventana de 14 días (habría que copiar la cifra semanalmente a mano o con un workflow programado, fuera de
  lo permitido salvo petición); sin series largas ni por escenario.
- **Coste/mantenimiento:** 0. **Retirada:** nada.

## Comparativa

| | (a) Worker contador | (b) Autoalojada | (c) Solo hosting |
|---|---|---|---|
| Datos | ruta+día+contador | páginas, referente, país, UA agregado | tráfico 14 días |
| IP guardada | no | no (llega al servidor) | no accesible |
| Cookie / storage | ninguno | ninguno (configurado) | ninguno |
| Terceros | Cloudflare (solo transporte) | ninguno (VPS) | GitHub (ya existe) |
| Coste | 0 € | 50-70 €/año + operación | 0 € |
| Mantenimiento | muy bajo | alto | nulo |
| Encaje con Pages | sí (subdominio) | servidor aparte | total |
| Serie histórica | sí | sí | no (14 días) |
| Banner de cookies | no | no | no |

## Recomendación
**(a)**, en dos pasos: primero **(c) ya hoy** (nada que montar) y, si el propietario quiere serie histórica, **(a)** por ser
el menor dato posible, el menor coste y el único con encaje limpio en GitHub Pages sin servidor propio. (b) solo si algún día
se quieren referentes/países; su operación no compensa para un sitio estático. Con (a) se decide además autoalojar
`maplibre-gl` (acción independiente) para que el visitante no contacte con `unpkg.com`.

## Fase 2 (solo con decisión del propietario)
1. Worker + workflow de despliegue (`produccion`) y subdominio `contador.`; 2. línea en `visor/v2/index.html` + CSP por meta;
3. tests de contrato (sin storage, sin cookies) y del Worker; 4. texto del pie; 5. informe diario opcional en datos abiertos.
Todo con PR propia, sin tocar P50 hasta decidir la publicación.

## Texto de transparencia para el pie (opción a)
> **Medición de visitas.** Este sitio cuenta cuántas veces se carga cada página, por día. No usa cookies ni guarda nada en tu
> dispositivo, no registra tu dirección IP ni datos de tu navegador, no te identifica ni te sigue entre páginas o sitios y
> no comparte datos con terceros. Solo se conserva un número por página y día. La infraestructura (alojamiento y red de
> entrega) procesa tu dirección IP de forma transitoria para entregarte la página, como cualquier servicio web, sin
> conservarla para esta medición.

Variante para (c): «Este sitio no utiliza cookies ni herramientas de analítica propias. El alojamiento (GitHub Pages) puede
tratar datos técnicos de conexión según su política de privacidad».
