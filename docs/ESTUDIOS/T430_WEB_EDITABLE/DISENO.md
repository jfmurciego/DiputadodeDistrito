# T-430 · Web editable en minutos — diseño

VERSIÓN: 1.2.0 · FECHA: 2026-11-20 · ESTADO: aprobado (D-186, 20-11, propietario vía Planificador): preguntas 1 a 11 respondidas · ANTERIOR: 1.1.0 (#951, fusionada); 1.2.0 alinea los menores del revisor de #951 y la fase 1 (#957): carpetas por huella de contenido, un solo esquema del índice, ruta de la V3 congelada y de `actual/`, cifras externas «por verificar»; P11 aprobada

> **Cifras externas.** Toda cifra o límite de Cloudflare, GitHub o GoDaddy de este documento está escrita de memoria y
> lleva «(por verificar)»: se coteja con la página oficial, con fecha, en el ensayo (§8) y antes de implementar.

Estado: **DISEÑO** (solo documento; nada creado ni tocado en GitHub, Cloudflare ni GoDaddy).
Encargo aprobado en líneas generales por el propietario el 20-11. Punto de partida: D-181 (V4 aceptada), D-184 y T-428
(V4 en la raíz del dominio, publicada por P40 en GitHub Pages), D-175/D-178 (bucket público de vídeos en
`media.diputadodedistrito.es`).

## 0. Decisiones (D-186, 20-11)

- **La web ES la V4**, y es lo único que vive y se mantiene en `ddd-web`. La V3 no se mantiene: queda como **archivo
  congelado** (pregunta 2, opción c) solo para no romper enlaces viejos, sin protagonismo (ningún enlace del menú).
- **Reparto del propietario**: en GitHub (repositorio principal) están los **cálculos y el algoritmo**; en R2 están las
  **fuentes y los mapas generados**. La web tira de R2 **cada vez**, a través de un índice publicado («actual», §4.0) que
  dice qué versión de cada mapa y dato está vigente, con sha256: una regeneración se ve sin tocar la web.
- Preguntas 1 y 3 a 10: **sí, según la recomendación**. Pregunta 11 (espacio en R2): **sí** (mismo presupuesto; el exceso se decide con D-176/D-178).

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
   (vista previa por rama: <rama>.ddd-web.pages.dev)     (carpetas inmutables por mapa + índice actual.json con sha256)
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

### 4.0 De dónde tira la web cada vez (D-186)

```
 GitHub (principal)            R2 público «datos.diputadodedistrito.es»               ddd-web (la V4)
 cálculos y algoritmo  ──P40──►  mapas/<territorio>/<version>/…   (inmutable, sha256)
                                 comunes/<version>/…              (índices, procedencia)
                                 actual.json  ◄── índice vigente (caché 60 s) ◄── 1. la página lo lee al abrir
                                    │  "nac28": {version, run, ficheros}             2. pide cada fichero por su ruta
                                    │  "comunes": {version, run, ficheros}           3. comprueba el sha256 y lo pinta
                                    └─ lo reescribe P40 al final de cada publicación (solo cambia lo regenerado)
```

Regla: **la web no lleva datos ni números de run**. Solo sabe la dirección de `actual.json` (en `mapa/datos.json`). Cada
entrada del índice es independiente: regenerar un territorio sube su carpeta nueva y cambia **solo su línea**; el resto
de la web y de los mapas no se toca. Volver atrás un territorio = devolver su línea al run anterior.


### 4.1 Rutas

Hoy Explorar usa rutas relativas en el mismo sitio (`explorar.js`, `BASE`): `../v2/datos/…`, `../datos/INDEX.json`,
`../datos/<geojson>`, `../data/viewer-results.json`, `../datos/catalogo_procedencia.json` y `datos/` (doble vuelta).
Pasa a **un único origen de datos**:

```
https://datos.diputadodedistrito.es/actual.json                    ← índice vigente (caché 60 s)
https://datos.diputadodedistrito.es/mapas/<territorio>/<version>/…      ← inmutable: GeoJSON, doble vuelta, resultados
https://datos.diputadodedistrito.es/comunes/<version>/…                 ← inmutable: v2/datos, INDEX, procedencia, viewer-results
https://datos.diputadodedistrito.es/archivo/v3-2026-11/…            ← V3 congelada (D-186)
```

`actual.json` (esquema sencillo):

```json
{"version_formato": 1, "publicado": "2026-11-20T12:00:00Z", "p40_run": 123,
 "comunes":  {"version": "<16 hex>", "run": 123, "ficheros": {"datos/INDEX.json": "<sha256>", "v2/datos/provincias.json": "<sha256>"}},
 "mapas": {"nac28": {"version": "<16 hex>", "run": 456, "ficheros": {"distritos.geojson": "<sha256>", "doble_vuelta.json": "<sha256>"}}}}
```

`<version>` = 16 primeras cifras hexadecimales del sha256 del listado «ruta sha256» del grupo (fase 1, #957): mismo contenido, misma carpeta; contenido distinto, carpeta nueva. No se usa el número de run porque la doble vuelta puede cambiar sin una 00 nueva; el run va en el índice. La ruta de cada fichero se deduce sin ambigüedad: `comunes/<version>/<fichero>` o `mapas/<territorio>/<version>/<fichero>`.
Explorar lee `actual.json`, sustituye las rutas relativas de hoy (`BASE` de `explorar.js`) por esas y **verifica el sha256** de cada fichero con `crypto.subtle.digest` antes de pintarlo; si
no casa, no lo pinta y lo dice (igual que hoy con el INDEX, #919/T-415 PR4). La URL de `actual.json` va en un
`mapa/datos.json` de ddd-web, para poder apuntar a otro origen sin tocar código.

### 4.2 CORS

Bucket R2 **nuevo y público solo para la web** (`ddd-web-datos`), con dominio propio `datos.diputadodedistrito.es`
(como `media.`). Política CORS del bucket: `GET`, `HEAD`; sin credenciales; `AllowedOrigins: ["*"]` (los datos son
públicos y abiertos; `*` cubre también las vistas previas `*.ddd-web.pages.dev`). `MaxAgeSeconds: 86400` (nombres de los campos de la política CORS de R2: por verificar).

### 4.3 Caché e invalidación

- Ficheros bajo `mapas/…/<version>/` y `comunes/<version>/`: `Cache-Control: public, max-age=31536000, immutable` (nunca cambian: nada que purgar).
- `actual.json`: `Cache-Control: public, max-age=60`; Explorar lo pide con `cache:"no-cache"`.
- Publicar = subir solo las carpetas nuevas (territorios regenerados y, si cambian, comunes), verificarlas leyendo del
  dominio público y **al final** reescribir `actual.json` (cambio atómico: una visita a medias sigue con lo anterior, que no se borra).
- Volver atrás = devolver la línea del territorio (o de comunes) a su run anterior (un paso de P40, sin regenerar).
- Se conservan los 5 últimos runs de cada territorio y de comunes; el borrado de los viejos lo hace P70 con permiso (como D-176).
- Sin purga manual en Cloudflare en el camino normal.

### 4.4 Tamaño en R2 (estimación por verificar)

Una publicación completa (todos los territorios + comunes) ≈ árbol de datos que hoy publica P40: GeoJSON M06 (~50 MB, CLAUDE.md), `v2/datos` (~5 MB en `visor/v2`), doble
vuelta e índices (pocos MB): **~60 MB por publicación completa** (una regeneración de un territorio, mucho menos). Cinco versiones de todo ≈ 0,3 GB; cada versión citada por un DOI (§9) que no se
poda suma ~60 MB; la V3 congelada (pregunta 2), otro ~60 MB una vez. Total previsible **< 1 GB** el primer año. Se mide con
el primer llenado (paso 12) antes de fijar la poda. El coste en euros depende de la tarifa vigente de R2 (por verificar) y
entra en el mismo presupuesto que el bucket de trabajo: ver pregunta 11.

## 5. P40 a partir de ahora

| Hoy | Después |
|---|---|
| monta el sitio completo (V1-V4, docs, datos) y lo despliega en GitHub Pages | monta **solo el árbol de datos** (y la documentación técnica, pregunta 4) y lo sube a R2 `ddd-web-datos` en `mapas/<territorio>/<version>/` (solo los territorios publicados) y `comunes/<version>/`; verifica cada sha256 leyendo de `datos.diputadodedistrito.es`; reescribe `actual.json` |
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
   paso 5 (es lo esperado: `media.diputadodedistrito.es` ya funciona sobre R2, y R2 pide que el dominio propio esté en Cloudflare — por verificar).
3. Si no aparece: «Add a site» → `diputadodedistrito.es` → plan gratuito (nombre del plan por verificar). Cloudflare copia los registros DNS actuales;
   comprobar que están los que hoy apuntan a GitHub Pages (los `A` y el `CNAME www` que figuren en GoDaddy; direcciones por verificar en la ayuda de GitHub Pages) y `media`.
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
12. P40 en modo nuevo publica la primera versión de todos los territorios, `comunes/` y `actual.json`. Abrir `https://ddd-web.pages.dev/mapa/` y comprobar
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
  (nombres de las opciones de certificado y de modo SSL en el panel: por verificar). Ventana de riesgo: segundos-minutos; hora de poco tráfico.
- **Redirecciones** (`_redirects` de ddd-web, 301 y con la consulta conservada):
  - `/v4/*` → `/:splat` (las URL de la V4 ya compartidas, como hoy hace T-428);
  - `/docs/metodo.html` → `/metodologia.html`;
  - `/v3/*`, `/v2/*`, `/v1/*`, `/nacional/*`, `/congreso/*` → según pregunta 2;
  - `/docs/*` (documentación técnica) → según pregunta 4;
  - `/datos/*` y `/data/*` (descargas enlazadas desde fuera) → `https://datos.diputadodedistrito.es/actual/<ruta de hoy>` (pregunta 5): P40 copia, en cada publicación, los ficheros vigentes también a `actual/` con su ruta de hoy (`actual/datos/INDEX.json`, `actual/datos/nac28/distritos.geojson`…), con caché de 5 min; `actual/` no es inmutable y no se cita en DOI. (Fase posterior; no está en #957.)
  - `www` → raíz.
- **Vuelta atrás** en 1 minuto: quitar el dominio del proyecto Pages y restaurar los registros `A` y `CNAME` de GitHub (cuántos y cuáles: por verificar; quedan
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
- Los datos citados por un DOI apuntan a su carpeta inmutable `mapas/<territorio>/<version>/` (no a `actual.json`): la cita sigue siendo
  reproducible aunque se publiquen datos nuevos; por eso esas carpetas no se borran (excepción a la poda del §4.3).
- Orden: primero el corte, después el próximo depósito en Zenodo con la URL corregida.

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| Un texto pegado de una IA con jerga, enlaces rotos o HTML roto llega al público | pruebas en la construcción de Pages: si fallan, no se publica; vista previa por rama para cambios grandes |
| Sin revisión, un cambio sustantivo (p. ej. reserva legal del pie) se publica sin que nadie lo vea | es decisión del propietario (sin reglas de PR); la historia de git y el «rollback» de Pages (un clic) lo deshacen |
| Fallo de CORS o de sha256 deja Explorar en blanco | ensayo completo en `pages.dev` antes del corte; mensaje visible en Explorar; vuelta atrás de `actual.json` |
| Explorar (código) y formato de datos (P40) evolucionan en repos distintos | `actual.json` lleva `version_formato`; Explorar rechaza formatos que no conoce; los cambios de formato se hacen compatibles hacia atrás o en pareja |
| Límites de tamaño de Pages por fichero y por despliegue (cifras por verificar) | los datos grandes no van a Pages, van a R2 |
| Credencial de Cloudflare con acceso de más | autorizar la app de Cloudflare solo para `ddd-web`; token R2 solo de ese bucket |
| URL viejas compartidas (V3, `/docs/`, `/datos/`) | `_redirects` con lista probada; prueba de rutas estables |
| Pérdida del contador (T-294, sin desplegar) | no depende de dónde se sirva la web; su lista blanca de orígenes ya es el dominio propio |
| Coste y espacio | Pages en plan gratuito (cupo de construcciones al mes por verificar). R2: ver §4.4; el bucket de trabajo ya está en 16,47 GB (164,7 % del presupuesto de 10 GB), así que el bucket web suma a un presupuesto ya superado |
| Dos sitios de verdad durante la transición | la V4 de `visor/v4/` se congela desde que exista ddd-web; se borra del principal tras el corte |

## 11. Preguntas (con recomendación; respondidas en D-186 salvo la 11)

1. **Nombre del repositorio.** `ddd-web`, `diputadodedistrito.es` o `web`. *Recomiendo `ddd-web`* (corto, claro en la URL de vista previa).
2. **Dónde queda la V3.** **Decidido (D-186): (c)**, sin protagonismo (ninguna comprobación cambia la decisión; solo el detalle de la redirección). (a) `/v3/` en ddd-web con su código y datos de R2; (b) subdominio `v3.`; (c) **congelada**: una
   instantánea completa (V1, V2, V3 con sus datos de hoy, sin cambiar un byte) en `datos.diputadodedistrito.es/archivo/v3-2026-11/`
   y `/v3/*` redirige allí. *Recomiendo (c)*: Explorar ya es la V3 completa (D-181); no se mantiene dos veces y las URL
   compartidas siguen funcionando. Requisito a comprobar en el ensayo: R2 no sirve `index.html` de carpeta, así que la
   redirección apunta a `…/v3/index.html` conservando `?consulta` y `#ancla`.
   Detalle que se comprueba en el ensayo: que la redirección conserve la consulta y el ancla. Si no las conserva, la V3
   congelada sigue en (c) y las URL viejas abren la portada de la V3 (sin la consulta); se avisa al propietario antes del corte.
3. **Cabecera y pie: construcción mínima o HTML repetido.** *Recomiendo la construcción mínima* (`construir.py`, < 1 s):
   el menú se edita en un sitio; la alternativa (copia literal en cada página + prueba de igualdad) obliga a editar N
   ficheros por cambio.
4. **Documentación técnica (`/docs/`, salvo Metodología).** (a) P40 la sigue generando y la sube a `datos./docs/`;
   (b) se queda solo en GitHub (enlace al repositorio). *Recomiendo (a)* con `/docs/*` redirigido; comprobar que la
   documentación se genera con URL de fichero (`citar.html`) y no de carpeta, por lo dicho de R2 en la pregunta 2.
   **Depende de esa comprobación** (en el ensayo); si falla, (b).
5. **Enlaces de descarga ya compartidos fuera de la web (`/datos/…`, `/data/…`).** ¿Deben seguir llevando siempre a la
   versión más reciente de los datos? *Recomiendo sí*: esas direcciones redirigen a «la última publicación»; las citas
   científicas, en cambio, apuntan a una publicación fija que no cambia (§9). Detalle técnico para el implementador.
6. **Opción «Solo el sitio» de P40.** *Recomiendo renombrarla «Solo datos comunes»* (sube índices, procedencia y doble
   vuelta sin territorios nuevos); sin parámetros técnicos nuevos (D-130).
7. **GitHub Pages del principal tras el corte.** *Recomiendo desactivarlo* tras 2 semanas sin incidencias: una copia
   vieja en `github.io` confunde y Zenodo dejará de citarla.
8. **Comprobar en el móvil que cada mapa no ha sido alterado.** Comprobarlo tarda un poco más con los mapas grandes.
   *Recomiendo comprobarlo siempre*; si en el ensayo algún mapa tarda demasiado en un móvil, el implementador propone
   una alternativa medida.
9. **¿Prueba también en GitHub Actions?** *Recomiendo no* al principio: la prueba ya bloquea la publicación en Pages;
   añadirla solo si el propietario quiere ver la marca en GitHub.
10. **Edición desde el móvil o por IA con acceso al repo.** *Recomiendo* el editor web de GitHub y, para cambios largos,
    rama + vista previa; una IA con permiso de escritura en ddd-web (no en el principal) es posible más adelante, con el
    mismo bloqueo de pruebas.
11. **Espacio en R2.** El bucket web sumaría < 1 GB previsto (§4.4) a un almacenamiento que ya pasa del presupuesto de
    10 GB (16,47 GB; aun con los ~2,2 GB de la limpieza de D-178 quedarían ~14,3 GB). *Recomiendo* contarlo dentro del
    mismo presupuesto, medirlo en el primer llenado y dejar la decisión sobre el exceso (ampliar el presupuesto o limpiar
    más) donde ya está, en D-176/D-178: el bucket web (~6 % del total) no la cambia de forma apreciable.

## 12. Orden de implementación (aprobado, D-186; PR pequeñas por fase)

1. PR en el principal: P40 con el modo «datos a R2» detrás de una opción interna, sin quitar Pages (ensayo en paralelo).
2. Pasos A-D del propietario; filtrado del historial y commits de reorganización en ddd-web.
3. Primer llenado (Operador, frase del propietario) y ensayo en `pages.dev`.
4. Corte (pasos 13-15), `CITATION.cff`, y PR que retira `visor/v4/` y `preparar_portada_v4.py` del principal.
5. A las 2 semanas: desactivar Pages del principal (pregunta 7).
