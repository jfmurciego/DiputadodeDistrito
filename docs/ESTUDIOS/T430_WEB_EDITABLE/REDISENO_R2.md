# T-430b · La web servida desde R2, con entorno de pruebas — rediseño (solo documento)

VERSIÓN: 1.0.0 · FECHA: 2026-11-22 · ESTADO: propuesta (pendiente del propietario) · ANTERIOR: ninguna (fichero nuevo)

**Decisión de partida (D-193, propietario, 22-11; sustituye en parte a D-186).** No hay repositorio aparte: la web sigue en este
repositorio (`visor/v4/`). El propietario quiere (a) un entorno de pruebas donde ver cada cambio antes de publicarlo y (b) la web
servida desde R2, no desde GitHub Pages. Se mantiene el índice «actual» de los datos en el bucket `ddd-web-datos` (D-188, D-192) y la
fase 1 ya fusionada (#957). De `DISENO.md` 1.3.0 quedan sin efecto el repositorio `ddd-web`, Cloudflare Pages y el traslado con
historial (§3, §7 C); sigue valiendo lo demás (datos, caché de 60 s, Zenodo, V3 congelada, pruebas de jerga y de enlaces).

**Cifras externas.** Lo que dependa de Cloudflare (planes, límites, nombres del panel, si una regla sirve con un dominio de R2)
está escrito de memoria y lleva «por verificar»: se comprueba en el ensayo antes de cortar.

## 1. Cómo llega la web a R2

### 1.1 Tres buckets, cada uno con su dirección

| Bucket (nuevo salvo el de datos) | Dirección | Qué guarda | Quién escribe |
|---|---|---|---|
| `ddd-web-sitio` | `diputadodedistrito.es` (y `www.`) | la web pública: portada, Comprender, Explorar, Metodología, `/docs/`, V1-V3 congeladas, redirecciones de `/v4/` | P40 (al publicar) |
| `ddd-web-pruebas` | `pruebas.diputadodedistrito.es` | una carpeta por rama: `/<rama>/…` | el job de pruebas (§2) |
| `ddd-web-datos` (ya diseñado, #957) | `datos.diputadodedistrito.es` | `web/actual/` (datos vigentes + `actual.json`) | P40 |

Buckets separados y no carpetas de uno solo: cada uno tiene su llave (la de pruebas no puede tocar la web pública), su dirección y
su limpieza; y el dominio propio de R2 se enlaza a un bucket entero (por verificar que no admite «solo una carpeta»).

### 1.2 Qué sube P40

P40 ya monta el sitio completo en `/tmp/site-candidate` (V4 en la raíz desde T-428). Cambia solo el destino:

1. **Datos** → `ddd-web-datos/web/actual/` (como ya hace el paso de #957).
2. **Web** → `ddd-web-sitio/`: el mismo árbol del sitio **sin** `datos/`, `data/`, `mapa/datos/` ni `v2/datos/` (eso lo sirve `datos.`).
   Se reutiliza la herramienta de #957 generalizada a un segundo índice (`sitio/actual.json` en el propio bucket): sube solo lo que
   cambió, comprueba el sha256, escribe el índice y borra lo que salió, **con la misma guarda de borrado** (tope y claves válidas).
3. **Orden dentro de la web**: primero imágenes, estilos y código; las páginas HTML al final, para que una página nueva nunca apunte
   a un fichero que aún no está.
4. **Caché** (la pone P40 en cada fichero al subirlo): HTML 60 s; imágenes, estilos y código con una marca de contenido en el enlace
   (`styles.css?v=<8 cifras>`, la añade P40 al subir) y un año; así un cambio de texto se ve en un minuto y lo pesado no se vuelve a bajar.
5. **Explorar** lee los datos de `datos.diputadodedistrito.es/web/actual/` a través de `actual.json` (cambio de una línea de base en
   `explorar.js`, ya diseñado en `DISENO.md` §4.1). Hasta ese cambio, la web en R2 no tendría datos: va **antes** del corte.

### 1.3 La pieza mínima para las carpetas (`/mapa/` → `/mapa/index.html`)

R2 por su dominio no sirve `index.html` al pedir una carpeta (por verificar en el ensayo). Dos opciones:

| Opción | Qué es | Coste | Cubre |
|---|---|---|---|
| **A. Regla de reescritura de Cloudflare** («Transform Rules → URL Rewrite»; nombre del panel por verificar) | sin código: «si la ruta acaba en `/`, pide `…index.html`»; y una «Redirect Rule» de `/mapa` a `/mapa/` | 0 €: el plan gratuito incluye unas pocas reglas (número por verificar) | carpetas y barra final |
| B. Worker delante de R2 | unas 30 líneas que leen del bucket: índice de carpetas, página 404 propia, cabeceras | 0 € hasta el cupo diario gratuito de peticiones (por verificar, del orden de 100 000/día); de pago por encima | todo, también 404 propia y cabeceras de seguridad |

**Recomiendo A** para empezar: no hay código que mantener y cubre lo necesario. La 404 de R2 es un texto técnico en inglés; si molesta,
se pasa a B (pregunta 2). Las redirecciones que ya existen (`/v4/` → raíz, T-428) son páginas HTML estáticas y funcionan igual en R2.

## 2. El entorno de pruebas

### 2.1 Una dirección por rama

- Dirección: `https://pruebas.diputadodedistrito.es/<rama>/` (la rama en minúsculas, con `/` cambiada por `-`; p. ej. `t442-portada-ligera`).
- Funciona en una subcarpeta porque la V4 ya usa enlaces relativos (T-428 la probó bajo `/DiputadodeDistrito/`).
- Datos: los de producción, leídos de `datos.diputadodedistrito.es` (lo que se prueba es la web, no los datos; pregunta 4).
- No aparece en buscadores: P40 inserta `<meta name="robots" content="noindex">` en cada página de pruebas al subirla, y la misma
  regla de Cloudflare puede añadir la cabecera `X-Robots-Tag: noindex` a todo `pruebas.` (por verificar).

### 2.2 Cómo se publica

- Un job nuevo en P90 (que ya corre en cada PR), `pruebas_web`, solo si la PR toca `visor/v4/`: monta la V4 como en P40 (sin
  construir datos: segundos), la sube a `ddd-web-pruebas/<rama>/` con la llave **solo de ese bucket** y escribe la dirección en el
  resumen del job. Tarda ~1-2 min.
- Seguridad: corre con el código de la PR y la llave del bucket de pruebas; las PR desde forks no reciben secretos. La llave no puede
  escribir en `ddd-web-sitio` ni en `ddd-web-datos`.

### 2.3 Cómo se borra

- En cada push a `main` (que ya ejecuta P90), un paso borra las carpetas de `ddd-web-pruebas` cuya rama ya no tiene PR abierta
  (lista de PR abiertas por la API, solo lectura). Cubre fusionadas y cerradas sin tocar los tipos de evento de P90 (cambiarlos crearía
  un check `pruebas` saltado; lección de T-366). Sin vigilantes ni calendario.
- Misma guarda que el resto: solo borra dentro de `ddd-web-pruebas`, carpeta a carpeta, y nunca más de N de una vez sin anulación.

## 3. GitHub Pages y la transición sin cortes

1. **En paralelo**: P40 sigue desplegando GitHub Pages como hoy y, además, sube la web a `ddd-web-sitio`. El bucket se prueba por una
   dirección provisional (p. ej. `nueva.diputadodedistrito.es`) sin tocar el dominio.
2. **Ensayo**: portada, Comprender, Explorar con datos de `datos.`, Metodología, `/docs/`, V3 congelada, redirecciones de `/v4/`, URL
   ya compartidas, móvil (T-442) y tiempos (T-440).
3. **Corte** (minutos, a hora de poco tráfico): en el bucket `ddd-web-sitio`, conectar el dominio `diputadodedistrito.es` (y `www.`).
   Cloudflare sustituye los registros que hoy apuntan a GitHub Pages (por verificar que lo hace solo; si no, se borran a mano antes).
   HTTPS: el certificado de la zona ya cubre el dominio.
4. **Vuelta atrás** (1 minuto): desconectar el dominio del bucket y restaurar los registros de GitHub Pages (se apuntan antes del corte);
   Pages sigue desplegado, así que vuelve tal cual.
5. **Retirada**: dos semanas sin incidencias → P40 deja de desplegar Pages y se desactiva (pregunta 8).

## 4. Qué se queda de T-442 y de #971

- **T-442 (#972)**: sin cambios. Está en `visor/v4/` y sube a R2 igual que el resto.
- **#971 (D-192)**: todo sigue; cambia solo **dónde**: lo que decía «en ddd-web» va en `visor/v4/` de este repositorio, y la marca de
  caché la pone P40 al subir (no `construir.py`). La prueba de tope de 100 KB va a los tests de la V4 (`tests/test_visor_v4_*`). El
  orden «después del corte» pasa a ser «después del corte a R2». La compresión previa en R2 se decide con T-440.

## 5. Cuánto tarda un cambio de texto de punta a punta

| Paso | Hoy | Con este diseño | Con las preguntas 6 y 7 en «sí» |
|---|---|---|---|
| Editar en GitHub (web) y abrir PR | 2 min | 2 min | 2 min |
| Ver el cambio | — (no hay pruebas) | ~2 min (pruebas.) | ~2 min |
| CI de la PR | 15-20 min (batería completa) | 15-20 min | ~2 min (solo pruebas de la web) |
| Fusionar | frase del propietario | igual | igual |
| Publicar | P40 completa (~10-15 min, por medir) + frase | P40 completa + frase | ~2 min, sola al fusionar (solo la web) |
| **Total** | **~30-40 min** | **~30-40 min, con vista previa** | **~8-10 min** |

Sin las preguntas 6 y 7 el entorno de pruebas existe, pero el camino sigue siendo largo: lo que lo acorta es no correr la batería del
motor para un cambio de texto y no reconstruir los datos para publicar una coma.

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| La regla de carpetas no funciona con el dominio de R2 | se comprueba en la dirección provisional; si no, Worker (opción B) |
| Web y datos en orígenes distintos (CORS) | política ya diseñada en `ddd-web-datos` (`DISENO.md` §4.2); ensayo antes del corte |
| La llave de pruebas en el código de una PR | llave limitada al bucket de pruebas; forks sin secretos |
| Atajo de CI (pregunta 6) deja pasar un cambio que rompe algo fuera de la web | el atajo solo vale si la PR toca **únicamente** `visor/v4/`; cualquier otro fichero, batería completa |
| Publicación automática (pregunta 7) publica algo no deseado | solo ficheros de `visor/v4/`, nunca datos; mismo bloqueo de pruebas; vuelta atrás = revertir la PR (se republica sola) |
| Espacio en R2 | la web ≈ 6 MB (sobre todo `visor/v2`) + las ramas de pruebas vivas; dentro del presupuesto (P11, D-176/D-178) |

## 7. Pasos del propietario (de uno en uno; nombres del panel por verificar)

Ahora (no cambian nada de lo que se ve):

1. dash.cloudflare.com → «R2 Object Storage» → «Create bucket» → nombre `ddd-web-sitio` → «Create bucket».
2. Otra vez «Create bucket» → nombre `ddd-web-pruebas` → «Create bucket».
3. En `ddd-web-pruebas` → «Settings» → «Custom Domains» → «Connect Domain» → `pruebas.diputadodedistrito.es` → «Connect». Esperar «Active».
4. En `ddd-web-sitio` → «Settings» → «Custom Domains» → «Connect Domain» → `nueva.diputadodedistrito.es` (dirección provisional) → «Connect».
5. «R2 Object Storage» → «Manage R2 API Tokens» → «Create API token»: nombre `ddd-web-pruebas`, permiso «Object Read & Write», solo
   el bucket `ddd-web-pruebas` → «Create». No cerrar la pantalla.
6. GitHub → repositorio → «Settings» → «Secrets and variables» → «Actions» → «New repository secret»: `R2_PRUEBAS_ACCESS_KEY_ID` y
   después `R2_PRUEBAS_SECRET_ACCESS_KEY` con los dos valores. Cerrar la pantalla de Cloudflare.
7. Repetir 5 y 6 para `ddd-web-sitio`: token `ddd-web-sitio`, secretos `R2_SITIO_ACCESS_KEY_ID` y `R2_SITIO_SECRET_ACCESS_KEY`.
8. Cloudflare → el dominio `diputadodedistrito.es` → «Rules» → «Transform Rules» → «URL Rewrite» → crear la regla que dará el
   implementador (texto para pegar). Lo mismo en «Redirect Rules».

En el corte (más adelante, con el Coordinador):

9. En `ddd-web-sitio` → «Custom Domains» → conectar `diputadodedistrito.es` y `www.diputadodedistrito.es`.
10. GitHub → «Settings» → «Pages» → quitar el dominio propio (después del 9).

## 8. Preguntas al propietario (con recomendación)

1. **¿Tres buckets (sitio, pruebas, datos)?** *Recomiendo sí*: cada llave solo puede tocar el suyo.
2. **¿Regla de Cloudflare (sin código) o Worker para las carpetas?** *Recomiendo la regla*; Worker solo si se quiere una página 404 propia.
3. **¿Las pruebas, públicas sin buscadores o con acceso restringido?** *Recomiendo públicas con «noindex»*: más sencillo; restringirlas
   (Cloudflare Access, gratis para pocos usuarios, por verificar) exige iniciar sesión cada vez.
4. **¿Las pruebas usan los datos de producción?** *Recomiendo sí*: se prueba la web, no los datos.
5. **¿Borrar las pruebas al siguiente push a `main` cuando su PR ya no está abierta?** *Recomiendo sí* (sin calendario ni vigilante).
6. **¿Atajo de CI: si una PR solo toca `visor/v4/`, correr solo el guardián y las pruebas de la web (~2 min) en vez de la batería
   completa?** *Recomiendo sí*: es lo que más acorta el camino. Reduce comprobaciones, por eso necesita tu decisión expresa.
7. **¿Publicar la web sola al fusionar cuando la PR solo toca `visor/v4/` (sin datos, sin P40 completa)?** *Recomiendo sí*: hoy cada
   publicación exige tu frase; esto la sustituiría, solo para textos y diseño de la web, por la fusión misma (que ya exige tu frase).
8. **¿Retirar GitHub Pages dos semanas después del corte?** *Recomiendo sí*.
9. **¿Dirección provisional `nueva.diputadodedistrito.es` para el ensayo?** *Recomiendo sí*; se borra tras el corte.

## 9. Orden propuesto (para cuando se apruebe)

1. PR: Explorar lee de `datos.` vía `actual.json` (con la web aún en Pages y los datos ya en `ddd-web-datos`).
2. PR: P40 sube también la web a `ddd-web-sitio` (en paralelo a Pages) + la marca de caché.
3. PR: job `pruebas_web` en P90 y su limpieza (+ preguntas 6 y 7 si son «sí»).
4. Pasos 1-8 del propietario; ensayo en `nueva.` y `pruebas.`.
5. Corte (pasos 9-10); dos semanas; retirada de Pages.
