# T-430 · Web editable en minutos — diseño

VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ESTADO: propuesta (pendiente de aprobación del propietario) · ANTERIOR: ninguna (fichero nuevo)

Estado: **DISEÑO** (solo documento; nada creado ni tocado en GitHub, Cloudflare ni GoDaddy).
Encargo aprobado en líneas generales por el propietario el 20-11. Punto de partida: D-181 (V4 aceptada), D-184 y T-428
(V4 en la raíz del dominio, publicada por P40 en GitHub Pages), D-175/D-178 (bucket público de vídeos en
`media.diputadodedistrito.es`).

## 1. Problema y objetivo

Hoy un cambio de una coma en la portada exige PR en el repositorio principal, 15-20 min de CI y una P40 con aprobación.
Objetivo: **texto editado → en la web en 1-2 minutos**, editando en el editor web de GitHub o pegando lo que devuelva una
IA, sin tocar el motor ni su control. Los **datos** (mapas, resultados, doble vuelta) siguen con su control actual.

## 2. Arquitectura

```
 ddd-web (repo nuevo, pequeño)            DiputadodeDistrito (repo principal, sin cambios de control)
 portada, Comprender, Metodología,        motor, P20-P75, publicador, P40
 Explorar (código), estilos, imágenes             │
        │ cada commit                              │ P40 (aprobación «produccion», como hoy)
        ▼                                          ▼
 Cloudflare Pages ──► diputadodedistrito.es    R2 público «ddd-web-datos» ──► datos.diputadodedistrito.es
   (vista previa por rama: <rama>.ddd-web.pages.dev)     (prefijos inmutables + actual.json con sha256)
                         │  Explorar lee con fetch + CORS + sha256  ▲
                         └──────────────────────────────────────────┘
 media.diputadodedistrito.es (vídeo, ya existe, D-175): no cambia.
```

Tres orígenes, tres responsables: **textos** (ddd-web, sin reglas), **datos** (P40, con control), **vídeo** (bucket de
vídeos). El bucket de trabajo sigue privado.

## 3. Qué va a cada repositorio

### 3.1 `ddd-web` (nuevo, público)

| Ruta en ddd-web | Procede de (repo principal) | Notas |
|---|---|---|
| `index.html` | `visor/v4/index.html` | portada |
| `comprender.html` | `visor/v4/comprender.html` | |
| `metodologia.html` | `documentacion_publica/docs/metodo.md` (hoy `/docs/metodo.html`) | pasa a HTML a mano; `/docs/metodo.html` redirige |
| `mapa/index.html`, `explorar.js`, `explorar.css`, `dv.js`, `calendario.json` | `visor/v4/mapa/` | Explorar: solo cambia la base de datos (§4) |
| `styles.css`, `tokens-bloques.css`, `assets/*.webp`, `assets-manifest.json` | `visor/v4/` | sha256 de los WebP en el manifiesto, como hoy |
| `partes/cabecera.html`, `partes/pie.html` | `visor/v4/cabecera.html`, `pie.html` | fuente única (§6) |
| `video.json` | `visor/v4/video.json` | |
| `NOTICE.md`, `PROCEDENCIA.md` | `visor/v4/NOTICE.md`, `docs/ESTUDIOS/T415_V4_PORTADA/PROCEDENCIA.md` | autoría de Vanesa (D-173) |
| `_redirects`, `_headers` | nuevos | redirecciones de URL compartidas (§8) y cabeceras |
| `pruebas/comprobar.py`, `pruebas/jerga.txt` | nuevos (lógica de los tests V4 actuales) | §6 |
| `construir.py` | nuevo | inserta cabecera y pie; copia a `dist/` |
| `LEEME.md` | nuevo | «cómo editar» en 5 líneas |

Quedan **fuera** de ddd-web: `auditoria-registro.html` y `mapa/ejemplo` (hoy en `NO_PUBLICAR.txt`), y todo lo que no sea web.

### 3.2 Repositorio principal (se queda)

Motor, workflows, publicador, `herramientas/publicar_doble_vuelta.py`, datos abiertos (`datos_abiertos/INDEX.json`),
`documentacion_publica/` (documentación técnica, salvo Metodología), V1-V3 (`visor/`, `visor/v2`, `visor/v3`), estudios.
`visor/v4/` se **borra** en una PR posterior al corte, con un `visor/v4/LEEME.md` que diga «la web vive en ddd-web»
(lo exige la regla de gobernanza: copia en `legacy/` de los ficheros versionados). Se retiran `preparar_portada_v4.py` y
los tests solo de V4 (`test_visor_v4_*`, `test_t428_v4_raiz.py`, `test_t419_*` en lo que toca a la copia de v4); los
tests de V3 siguen.

### 3.3 Mover sin perder historial

En una copia limpia (nunca sobre la del trabajo), con `git filter-repo`:

```
git clone https://github.com/jfmurciego/DiputadodeDistrito ddd-web && cd ddd-web
git filter-repo --path visor/v4/ --path documentacion_publica/docs/metodo.md \
  --path docs/ESTUDIOS/T415_V4_PORTADA/PROCEDENCIA.md \
  --path-rename visor/v4/: --path-rename visor/v4/cabecera.html:partes/cabecera.html ...
git remote add origin https://github.com/jfmurciego/ddd-web && git push -u origin main
```

Conserva commits, autores y fechas de cada fichero movido (`git log --follow` funciona en ddd-web). En el principal el
historial también sigue ahí (los ficheros se borran, no se reescribe nada). La reorganización a `partes/`, `metodologia.html`
y la base de datos de Explorar van en commits normales **después** del filtrado, para que el diff sea legible.

## 4. Cómo lee Explorar los datos

### 4.1 Rutas

Hoy Explorar usa rutas relativas en el mismo sitio (`explorar.js`, `BASE`): `../v2/datos/…`, `../datos/INDEX.json`,
`../datos/<geojson>`, `../data/viewer-results.json`, `../datos/catalogo_procedencia.json` y `datos/` (doble vuelta).
Pasa a **un único origen de datos**:

```
https://datos.diputadodedistrito.es/actual.json          ← puntero (caché 60 s)
https://datos.diputadodedistrito.es/p40-<run>/v2/datos/…  ← inmutable
                                              /datos/INDEX.json, /datos/<geojson>, /datos/catalogo_procedencia.json
                                              /data/viewer-results.json
                                              /mapa/datos/…  (doble vuelta)
```

`actual.json`: `{"prefijo":"p40-<run>/","run":<id>,"fecha":…,"ficheros":{"<ruta>":"<sha256>",…}}`. Explorar lee
`actual.json`, construye `BASE` con el prefijo (misma estructura de carpetas que hoy: el cambio en `explorar.js` es una
línea de base, no de lógica) y **verifica el sha256** de cada fichero con `crypto.subtle.digest` antes de pintarlo; si
no casa, no lo pinta y lo dice (igual que hoy con el INDEX, #919/T-415 PR4). La URL de `actual.json` va en un
`mapa/datos.json` de ddd-web, para poder apuntar a otro origen sin tocar código.

### 4.2 CORS

Bucket R2 **nuevo y público solo para la web** (`ddd-web-datos`), con dominio propio `datos.diputadodedistrito.es`
(como `media.`). Política CORS del bucket: `GET`, `HEAD`; sin credenciales; `AllowedOrigins: ["*"]` (los datos son
públicos y abiertos; `*` cubre también las vistas previas `*.ddd-web.pages.dev`). `MaxAgeSeconds: 86400`.

### 4.3 Caché e invalidación

- Ficheros bajo `p40-<run>/`: `Cache-Control: public, max-age=31536000, immutable` (nunca cambian: nada que purgar).
- `actual.json`: `Cache-Control: public, max-age=60`; Explorar lo pide con `cache:"no-cache"`.
- Publicar = subir el prefijo nuevo completo, verificarlo y **al final** reescribir `actual.json` (cambio atómico: una
  visita a medias sigue con el prefijo anterior, que no se borra).
- Volver atrás = reescribir `actual.json` con el prefijo anterior (un paso de P40, sin regenerar).
- Se conservan los 5 últimos prefijos; el borrado de los viejos lo hace P70 con permiso (como D-176).
- Sin purga manual en Cloudflare en el camino normal.

## 5. P40 a partir de ahora

| Hoy | Después |
|---|---|
| monta el sitio completo (V1-V4, docs, datos) y lo despliega en GitHub Pages | monta **solo el árbol de datos** (y la documentación técnica, pregunta 4) y lo sube a R2 `ddd-web-datos` bajo `p40-<run>/`; verifica cada sha256 leyendo de `datos.diputadodedistrito.es`; reescribe `actual.json` |
| `preparar_portada_v4.py` (V4 a la raíz) | se retira: la portada no es de P40 |
| entorno `github-pages` + aprobación | misma aprobación (`produccion`); credenciales R2 nuevas solo de escritura en ese bucket |
| registro `publicaciones_visor.json` | **igual**: el visor sigue mostrando solo lo registrado; la URL de evidencia pasa a la de datos |
| validación del sitio | valida el árbol de datos y que `actual.json` resuelve; la web la validan sus propias pruebas |

Las opciones visibles de P40 no cambian («Qué publicar», «Territorios», «Simular»; D-129/D-130). «Solo el sitio» deja de
tener sentido para textos: pasa a «Solo datos comunes» (pregunta 6). GitHub Pages del principal: tras el corte se quita el
dominio y queda desactivado (o como copia en `jfmurciego.github.io/DiputadodeDistrito/`, pregunta 7).

## 6. Pruebas mínimas de ddd-web (segundos, sin CI pesada)

Python sin dependencias (`pruebas/comprobar.py`, < 5 s). **Se ejecutan dentro de la propia construcción de Cloudflare
Pages** (`python3 pruebas/comprobar.py && python3 construir.py`): si fallan, Cloudflare no publica y la web sigue con la
versión anterior; el propietario ve el fallo en el panel y en el correo de Cloudflare. No hace falta GitHub Actions ni
reglas de PR (opcional: el mismo script en un workflow de 10 s para ver la marca roja en GitHub).

1. **Enlaces rotos**: todo `href`/`src` local resuelve a un fichero de `dist/` y cada `#ancla` existe; ningún enlace a
   `index.html`, a ficheros fuera de la web ni a rutas absolutas «/» que rompan la vista previa (mismas reglas que T-428).
2. **Jerga**: ningún término de `pruebas/jerga.txt` en el texto visible (la lista actual de los tests V4/D-181: códigos
   internos, nombres de módulos y workflows, «run», «checkpoint», «huella», etc.). Fallo con fichero, línea y palabra.
3. **Cabecera y pie idénticos**: las páginas llevan `<!-- incluir: cabecera -->` y `<!-- incluir: pie -->`; `construir.py`
   los sustituye por `partes/*.html`. La prueba exige el marcador en cada página y que ninguna tenga su propia `<header>`/
   `<footer>` fuera de él: así son idénticos por construcción y el menú se edita en un solo sitio (Inicio · Comprender ·
   Explorar · Metodología, D-181; pie con la reserva de acciones legales).
4. **Ningún «M0x»**: expresión `\bM0[0-9]\b` (y `N0[0-9]`) en texto visible, `title`, `alt` y `aria-label`.
5. Extras baratos ya existentes: sin recursos de terceros, sin `/Users/` ni correos, sha256 de los WebP = manifiesto,
   `video.json` con URL de `media.`.

Lo que **no** se prueba en ddd-web: los datos (los prueba P40) ni el motor.

## 7. Pasos manuales del propietario

Lenguaje llano; cada paso dice qué ver al terminar. Se hacen en este orden y nada de esto se hace hasta que se apruebe
el diseño.

**A. GitHub (5 min)**
1. Crear el repositorio público vacío `ddd-web` (sin README). Avisar al Coordinador; el implementador sube el historial (§3.3).

**B. Cloudflare: comprobar el dominio (2 min)**
2. Entrar en dash.cloudflare.com → «Websites» (Sitios). Si `diputadodedistrito.es` aparece como **Activo**, saltar al
   paso 5 (es lo esperado: `media.diputadodedistrito.es` ya funciona y R2 solo admite dominios propios de zonas de Cloudflare).
3. Si no aparece: «Add a site» → `diputadodedistrito.es` → plan Free. Cloudflare copia los registros DNS actuales;
   comprobar que están los de GitHub Pages (4 registros `A` 185.199.108-111.153 y `CNAME www`) y `media`.
4. Cloudflare muestra **dos servidores de nombres**. En GoDaddy: «Mis productos» → dominio → «DNS» → «Servidores de
   nombres» → «Cambiar» → «Usaré mis propios servidores» → pegar los dos → Guardar. Esperar el correo «zona activa»
   (minutos a 24 h). El dominio sigue registrado y pagado en GoDaddy; solo cambia quién responde al DNS.

**C. Cloudflare Pages (10 min)**
5. «Workers & Pages» → «Create» → «Pages» → «Connect to Git» → autorizar GitHub **solo** para `ddd-web`.
6. Proyecto `ddd-web`, rama de producción `main`. Framework: «None». Build command:
   `python3 pruebas/comprobar.py && python3 construir.py`. Output directory: `dist`. Guardar y desplegar.
7. Al terminar: abrir `https://ddd-web.pages.dev` y comprobar portada, Comprender, Metodología y Explorar.
   (Las ramas distintas de `main` salen solas en `https://<rama>.ddd-web.pages.dev`.)

**D. Datos en R2 (10 min)**
8. «R2» → «Create bucket» → `ddd-web-datos` (región automática).
9. En el bucket → «Settings» → «Custom domains» → «Connect domain» → `datos.diputadodedistrito.es`.
10. «Settings» → «CORS policy» → pegar la política que dará el implementador (§4.2).
11. «R2» → «Manage API tokens» → token nuevo con «Object Read & Write» **solo** en `ddd-web-datos`; guardar los dos
    valores como secretos del repositorio principal (`R2_WEB_ACCESS_KEY_ID`, `R2_WEB_SECRET_ACCESS_KEY`). Nunca en el chat.

**E. Primer llenado de datos (Operador, con frase del propietario)**
12. P40 en modo nuevo publica el primer prefijo y `actual.json`. Abrir `https://ddd-web.pages.dev/mapa/` y comprobar
    que Explorar carga un territorio.

**F. Corte (5 min, §8)**
13. En el proyecto Pages → «Custom domains» → «Set up a domain» → `diputadodedistrito.es`; repetir con
    `www.diputadodedistrito.es`. Cloudflare propone cambiar los registros que apuntan a GitHub: aceptar.
14. En GitHub, repositorio principal → Settings → Pages → borrar el dominio propio (después del paso 13, no antes).
15. Comprobar en un navegador privado: `https://diputadodedistrito.es/`, `/mapa/`, `/v3/` y una URL vieja (`/v4/`).

## 8. Corte sin caída

- **Ensayo completo antes**: toda la web en `ddd-web.pages.dev` con datos reales de `datos.` (pasos 1-12) mientras el
  dominio sigue en GitHub Pages. El corte solo empieza con el ensayo aceptado por el propietario.
- **DNS**: con la zona ya en Cloudflare, el cambio de destino es inmediato (sin propagación entre registradores). Si hubiera
  que mover los servidores de nombres (pasos 3-4), se hace **días antes** del corte, con los registros de GitHub copiados:
  la web sigue en GitHub mientras tanto.
- **HTTPS**: Cloudflare emite el certificado del dominio propio de Pages en minutos; mientras, sirve el de la zona
  (Universal SSL). Modo SSL «Full (strict)». Ventana de riesgo: segundos-minutos; hora de poco tráfico.
- **Redirecciones** (`_redirects` de ddd-web, 301 y con la consulta conservada):
  - `/v4/*` → `/:splat` (las URL de la V4 ya compartidas, como hoy hace T-428);
  - `/docs/metodo.html` → `/metodologia.html`;
  - `/v3/*`, `/v2/*`, `/v1/*`, `/nacional/*`, `/congreso/*` → según pregunta 2;
  - `/docs/*` (documentación técnica) → según pregunta 4;
  - `/datos/*` y `/data/*` (descargas enlazadas desde fuera) → `https://datos.diputadodedistrito.es/actual/…` (pregunta 5).
  - `www` → raíz.
- **Vuelta atrás** en 1 minuto: quitar el dominio del proyecto Pages y restaurar los 4 `A` + `CNAME` de GitHub (quedan
  apuntados en el paso 3); volver a poner el dominio en GitHub Pages.

## 9. Relación con Zenodo

- Zenodo archiva **el repositorio principal** (código, datos y paquetes firmados; D-74): no cambia. ddd-web no necesita DOI
  (es presentación); si se quiere, se activa aparte más adelante.
- Los DOI deben apuntar a la web **definitiva**: en metadatos (`.zenodo.json`/`CITATION.cff` `url`, «related identifiers»)
  solo `https://diputadodedistrito.es/` y rutas estables (`/metodologia.html`, `/mapa/?territorio=…`), **nunca**
  `*.pages.dev` ni `github.io`. Hoy `CITATION.cff` dice `https://jfmurciego.github.io/DiputadodeDistrito/`: se corrige
  en la PR del corte (sube VERSIÓN, como manda la gobernanza).
- Las rutas que cite un DOI quedan como **contrato**: la prueba 1 de ddd-web incluye una lista `pruebas/rutas_estables.txt`
  que deben existir o redirigir, para que una edición no rompa una cita.
- Los datos citados por un DOI apuntan a su prefijo inmutable `p40-<run>/` (no a `actual.json`): la cita sigue siendo
  reproducible aunque se publiquen datos nuevos; por eso esos prefijos no se borran (excepción a la poda del §4.3).
- Orden: primero el corte, después el próximo depósito en Zenodo con la URL corregida.

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| Un texto pegado de una IA con jerga, enlaces rotos o HTML roto llega al público | pruebas en la construcción de Pages: si fallan, no se publica; vista previa por rama para cambios grandes |
| Sin revisión, un cambio sustantivo (p. ej. reserva legal del pie) se publica sin que nadie lo vea | es decisión del propietario (sin reglas de PR); la historia de git y el «rollback» de Pages (un clic) lo deshacen |
| Fallo de CORS o de sha256 deja Explorar en blanco | ensayo completo en `pages.dev` antes del corte; mensaje visible en Explorar; vuelta atrás de `actual.json` |
| Explorar (código) y formato de datos (P40) evolucionan en repos distintos | `actual.json` lleva `version_formato`; Explorar rechaza formatos que no conoce; los cambios de formato se hacen compatibles hacia atrás o en pareja |
| Límites de Pages (25 MiB por fichero, 20 000 ficheros) | los datos grandes no van a Pages, van a R2 |
| Credencial de Cloudflare con acceso de más | autorizar la app de Cloudflare solo para `ddd-web`; token R2 solo de ese bucket |
| URL viejas compartidas (V3, `/docs/`, `/datos/`) | `_redirects` con lista probada; prueba de rutas estables |
| Pérdida del contador (T-294, sin desplegar) | no depende de dónde se sirva la web; su lista blanca de orígenes ya es el dominio propio |
| Coste | Pages Free (500 construcciones/mes) y R2 (~0 € a este volumen, sin coste de salida) |
| Dos sitios de verdad durante la transición | la V4 de `visor/v4/` se congela desde que exista ddd-web; se borra del principal tras el corte |

## 11. Preguntas abiertas (con recomendación)

1. **Nombre del repositorio.** `ddd-web`, `diputadodedistrito.es` o `web`. *Recomiendo `ddd-web`* (corto, claro en la URL de vista previa).
2. **Dónde queda la V3.** (a) `/v3/` en ddd-web con su código y datos de R2; (b) subdominio `v3.`; (c) **congelada**: una
   instantánea completa (V1, V2, V3 con sus datos de hoy, sin cambiar un byte) en `datos.diputadodedistrito.es/archivo/2026-11/`
   y `/v3/*` redirige allí. *Recomiendo (c)*: Explorar ya es la V3 completa (D-181); no se mantiene dos veces y las URL
   compartidas siguen funcionando. Requisito a comprobar en el ensayo: R2 no sirve `index.html` de carpeta, así que la
   redirección apunta a `…/v3/index.html` conservando `?consulta` y `#ancla`.
3. **Cabecera y pie: construcción mínima o HTML repetido.** *Recomiendo la construcción mínima* (`construir.py`, < 1 s):
   el menú se edita en un sitio; la alternativa (copia literal en cada página + prueba de igualdad) obliga a editar N
   ficheros por cambio.
4. **Documentación técnica (`/docs/`, salvo Metodología).** (a) P40 la sigue generando y la sube a `datos./docs/`;
   (b) se queda solo en GitHub (enlace al repositorio). *Recomiendo (a)* con `/docs/*` redirigido; comprobar que la
   documentación se genera con URL de fichero (`citar.html`) y no de carpeta, por lo dicho de R2 en la pregunta 2.
5. **Descargas `/datos/` y `/data/` con enlaces externos.** *Recomiendo* un alias estable `datos./actual/…` que P40
   copia también en cada publicación (no inmutable, caché 5 min) y redirigir allí; para citas, el prefijo inmutable.
6. **Opción «Solo el sitio» de P40.** *Recomiendo renombrarla «Solo datos comunes»* (sube índices, procedencia y doble
   vuelta sin territorios nuevos); sin parámetros técnicos nuevos (D-130).
7. **GitHub Pages del principal tras el corte.** *Recomiendo desactivarlo* tras 2 semanas sin incidencias: una copia
   vieja en `github.io` confunde y Zenodo dejará de citarla.
8. **Verificación sha256 en el navegador de ficheros grandes.** *Recomiendo verificar todo* (unos ms por MB); si algún
   GeoJSON pesa demasiado en móvil, verificar el manifiesto y servirlo con `Content-Digest` (decisión tras medir en el ensayo).
9. **¿Prueba también en GitHub Actions?** *Recomiendo no* al principio: la prueba ya bloquea la publicación en Pages;
   añadirla solo si el propietario quiere ver la marca en GitHub.
10. **Edición desde el móvil o por IA con acceso al repo.** *Recomiendo* el editor web de GitHub y, para cambios largos,
    rama + vista previa; una IA con permiso de escritura en ddd-web (no en el principal) es posible más adelante, con el
    mismo bloqueo de pruebas.

## 12. Orden de implementación propuesto (para cuando se apruebe)

1. PR en el principal: P40 con el modo «datos a R2» detrás de una opción interna, sin quitar Pages (ensayo en paralelo).
2. Pasos A-D del propietario; filtrado del historial y commits de reorganización en ddd-web.
3. Primer llenado (Operador, frase del propietario) y ensayo en `pages.dev`.
4. Corte (pasos 13-15), `CITATION.cff`, y PR que retira `visor/v4/` y `preparar_portada_v4.py` del principal.
5. A las 2 semanas: desactivar Pages del principal (pregunta 7).
