# T-450 · Bloqueo 403 de Cloudflare a la medición de la web — diagnóstico y regla recomendada (solo documento)

VERSIÓN: 1.0.0 · FECHA: 2026-11-23 · ESTADO: propuesta (pendiente del propietario) · ANTERIOR: ninguna (fichero nuevo)

Encargo del propietario (23-11, vía Planificador). Nada se cambia en Cloudflare desde aquí: son pasos para el propietario. Los nombres
del panel y lo que permite el plan gratuito están escritos de memoria y llevan «por verificar».

## 1. Lo que se ve en el run 45087927501 (P90 · medir la web, 22-11)

| Página o fichero | HTTP | Tiempo | Bytes (con / sin compresión) |
|---|---|---|---|
| Portada `/`, `/mapa/`, `/mapa/?territorio=nac28` | 403 | 41-71 ms | ≈ 3,1 KB / ≈ 5,3 KB |
| `datos/INDEX.json`, `v2/datos/provincias.json`, `datos/nac28/distritos.geojson`, `data/viewer-results.json`, `mapa/datos/INDEX.json` | 403 | 36-65 ms | ≈ 3,1 KB / ≈ 5,3 KB |
| `mapa/explorar.js` | **200** | 42-116 ms | 18,7 KB / 58,2 KB (el fichero real) |

Lectura:
- Todas las respuestas 403 pesan lo mismo sea cual sea la página o el JSON pedido, y llegan en ~50 ms: no es la web, es **una página
  de bloqueo genérica** del CDN (una web caída o un 403 de GitHub Pages tendría otro tamaño y otra forma).
- Lo único que pasa es un fichero **`.js`**. Cloudflare no aplica sus retos a los recursos que considera estáticos (scripts, estilos,
  imágenes) y sí a las páginas HTML y a los JSON (por verificar). Ese patrón encaja con un **reto gestionado** («managed challenge»)
  a clientes que no son navegador.
- El cliente era `curl` sin cabeceras de navegador (P90 1.2.0). #983 ya pide como un navegador y marca «bloqueado por el CDN».

**Causa probable**, por orden: (1) **Bot Fight Mode** activado (Security → Bots); (2) una regla del WAF o el «Security Level» en
alto / «I'm Under Attack» (Security → Settings); (3) «Browser Integrity Check» (rechaza cabeceras de cliente atípicas). Se confirma en
los eventos (§3).

## 2. A qué afecta

| Qué | ¿Le afecta? | Por qué |
|---|---|---|
| Visitantes con navegador | normalmente no | el navegador resuelve el reto solo; puede ver un instante «comprobando…» |
| **Explorar leyendo datos de `datos.diputadodedistrito.es`** (D-186, #974) | **sí, grave** | una petición `fetch` a otro dominio no puede resolver un reto: si `datos.` queda bajo el mismo filtro, el mapa se queda sin datos. Hoy no se nota porque los datos se sirven en el mismo dominio tras pasar el reto de la página |
| **Vídeo en `media.diputadodedistrito.es`** | posible | el reproductor tampoco resuelve retos; hoy funciona (comprobado el 20-11), pero si el filtro se extiende a `media.` se rompe |
| Buscadores (Google, Bing) | depende | Bot Fight Mode deja pasar a los «bots verificados» (por verificar); un reto general del WAF o el nivel «I'm Under Attack» no |
| Vistas previas al compartir enlaces (WhatsApp, X, LinkedIn) | probable | sus robots no resuelven retos: el enlace sale sin título ni imagen |
| Medición de T-440 | sí | es lo que ha salido en el run |
| P40 (publicar) | no | publica en GitHub Pages por la API y en R2 por `r2.cloudflarestorage.com`, que no pasan por el filtro de la zona; no pide la web pública tras desplegar |
| Pruebas por rama (`pruebas.`, #979) | no para subir; sí para comprobarlas con robots | suben por la API de R2; un navegador las ve; cualquier comprobación automática futura chocaría igual |
| Zenodo / DOI | no directamente | el DOI resuelve a Zenodo; Zenodo no visita la web. Los lectores que lleguen desde el DOI son navegadores |

## 3. Pasos para que el propietario mire (de uno en uno; nombres por verificar)

1. dash.cloudflare.com → la zona `diputadodedistrito.es`.
2. **Security → Events**. Arriba, periodo «Últimas 24 horas» (o el día 22-11 hacia la hora del run).
3. Añadir filtro **«User agent» contiene `curl`** (o filtrar por la IP de un runner de GitHub si aparece).
4. Mirar la columna **«Action taken»** (Bloqueo / Reto gestionado / Reto JS) y **«Service»**: dirá *Bot fight mode*, *Custom rules*,
   *Security level* o *Browser integrity check*. Esa es la causa; apuntarla.
5. Repetir el filtro con **«Host» = `datos.diputadodedistrito.es`** y **`media.diputadodedistrito.es`**: si hay retos ahí, es urgente (§2).
6. Ver los ajustes: **Security → Bots** (¿Bot Fight Mode activado?), **Security → Settings** (Security Level, Browser Integrity Check,
   Challenge Passage) y **Security → WAF → Custom rules** (¿hay reglas con acción «Challenge» o «Block»?).
7. Pasar al Coordinador lo que dicen «Action taken» y «Service» (captura sin datos personales).

## 4. Regla mínima recomendada

Objetivo: que pasen los **navegadores normales**, los **buscadores verificados** y la **medición** (con una cabecera secreta), y que
**`datos.` y `media.` nunca reciban retos**, sin abrir la web a cualquier robot.

1. **Bot Fight Mode: desactivado.** En el plan gratuito no admite excepciones (las reglas del WAF no lo saltan; por verificar): con él
   no hay forma de dejar pasar a la medición ni de proteger `datos.`/`media.`. Su papel lo cubren las reglas 2-4.
2. **Security Level: «Medium»** (no «High» ni «I'm Under Attack») y **Browser Integrity Check activado** (frena clientes con cabeceras
   falsas; los navegadores y los buscadores verificados pasan).
3. **WAF → Custom rules → regla «Permitir medición, buscadores y datos»**, acción **Skip** (saltar: el resto de reglas personalizadas, el
   Security Level y el Browser Integrity Check), con la expresión (texto para pegar en el editor de expresiones):

   ```
   (http.request.headers["x-ddd-medicion"][0] eq "<SECRETO>")
   or (cf.client.bot)
   or (http.host in {"datos.diputadodedistrito.es" "media.diputadodedistrito.es"} and http.request.method in {"GET" "HEAD" "OPTIONS"})
   ```

   - `<SECRETO>`: una cadena larga aleatoria; se guarda también como secreto del repositorio `MEDICION_CDN` y P90 la envía en la
     medición (cambio pequeño en `medir_web.py`, otra PR). No se escribe en ningún fichero ni chat.
   - `cf.client.bot` = bots verificados por Cloudflare (Google, Bing…); por verificar que el campo está en el plan gratuito.
   - `datos.` y `media.` son ficheros públicos de solo lectura: no hay nada que proteger con retos, y un reto los rompe.
4. **Opcional, si preocupa el abuso de `datos.`**: una regla de límite de peticiones (el plan gratuito trae una, por verificar) sobre
   `datos.diputadodedistrito.es`, por ejemplo 300 peticiones por minuto e IP, acción «Block» 1 minuto. Bloquea en vez de retar, así
   un navegador normal (que pide unas decenas) nunca la toca.

Después: relanzar `medir-web` (Operador, con la frase del propietario) y comprobar que todo da 200 y que ninguna fila sale «bloqueado
por el CDN».

## 5. Preguntas al propietario (con recomendación)

1. **¿Desactivar Bot Fight Mode?** *Recomiendo sí*: no admite excepciones y pone en riesgo los datos del mapa y el vídeo; lo sustituye
   la regla del §4.
2. **¿Medición con cabecera secreta (`MEDICION_CDN`)?** *Recomiendo sí*: deja pasar solo a P90 sin abrir la web a otros robots.
3. **¿`datos.` y `media.` siempre sin retos (solo lectura: GET, HEAD, OPTIONS)?** *Recomiendo sí*: un reto en esos dominios rompe el mapa y
   el vídeo para todos los visitantes.
4. **¿Dejar pasar a los bots verificados (buscadores)?** *Recomiendo sí*: es lo que pide el encargo y no abre la puerta a robots desconocidos.
5. **¿Regla de límite de peticiones en `datos.`?** *Recomiendo no por ahora*: tráfico bajo y ficheros pequeños; se añade si los eventos
   muestran abuso.
6. **¿Mirar primero los eventos (§3) antes de tocar nada?** *Recomiendo sí*: confirma la causa en dos minutos y evita cambiar lo que no es.
