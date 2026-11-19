# T-415 · V4: portada final de la autora + mapa con doble vuelta — diseño (solo documento)

VERSIÓN: 2.0.3 · FECHA: 2026-11-19 · ESTADO: aprobado (D-174, 19-11: «sí a todo» a las 9 recomendaciones; relayado por el Planificador, entra en el plan 1.0.69); LICENSE sigue necesitando autorización expresa · ANTERIOR: 2.0.2 (#909, fusionada); 2.0.3 solo alinea redacción (3 menores del revisor), sin cambiar el fondo

Decisión del propietario (19-11): `visor/v4/` es la versión nueva completa: portada de entrada y mapa con la doble vuelta de T-413 (D-172). V3 no se toca.
Base de este diseño: la **versión final** de la autora, rama `planificador/t415-v4-final`, `docs/ESTUDIOS/T415_V4_PORTADA/final/` (`LEEME_PARA_JESUS.md`, `web/`, `COMPROBACIONES.json`, `SHA256SUMS`; notas en `PROCEDENCIA.md`).
La primera entrega (`original/`) queda solo como histórico; su matriz jurídica no está en la versión final (§4). No toca `visor/`, `web/` ni workflows. Nada se publica.

## 1. Qué trae la versión final (hechos)

- Dos formatos del mismo diseño: `DDD_portada_autonoma.html` (340 KB, un solo fichero con data URI) y `web/` (3 HTML + `styles.css` + `app.js` + `catalogo-mapas.js` + 3 WebP + manifiesto de imágenes + generador del catálogo).
- Páginas: `index.html` (portada: «Comprender», «Explorar», franja «Investigación», franja de autoría), `comprender.html` (Sistema y distritos; Publicaciones y datos), `auditoria-registro.html` (catálogo DOI por mapa, procedencia de recursos, sobre el autor, protección jurídica).
- Sin Matrices, sin pestañas de método, sin presentación animada (el prototipo de «6 segundos» desaparece), sin recursos externos salvo enlaces (V3, ORCID, LinkedIn). Diseño: fondo carbón, marfil, naranja, granate; foco visible, salto al contenido, `prefers-reduced-motion`, 320–1440 px comprobados por la autora.
- Explorar enlaza hoy a `https://diputadodedistrito.es/v3/`; `catalogo-mapas.js` está vacío (`window.DDD_MAPS = []`) a propósito: no hay DOI reales.

## 2. Decisión de formato: `web/` por ficheros

Se usa `web/` (HTML/CSS/JS modular, rutas relativas, sirve desde raíz o subcarpeta), no la autónoma: encaja con el publicador (copia de ficheros, P40), se revisa en diff, el navegador cachea CSS/JS/imágenes y los tests leen el HTML. La autónoma (data URI) pesa 340 KB por página vista, no cachea y duplica el código. Solo se conserva como entrega de revisión para quien no tenga servidor; no se publica. `generar_portada_autonoma.py` no entra en `visor/`.

## 3. Rutas de `visor/v4/`

| Ruta | Contenido | Origen |
|---|---|---|
| `v4/index.html` | Portada | `final/web/index.html` |
| `v4/comprender.html` | Comprender + sección nueva «La doble vuelta» (§5.2) | final + T-413 §4 |
| `v4/auditoria-registro.html` | Catálogo DOI (vacío «pendiente»), procedencia, autor, protección jurídica (textos jurídicos «de trabajo hasta su revisión») | final |
| `v4/mapa/` | Mapa V4 con doble vuelta | T-413 (#910) |
| `v4/styles.css`, `v4/app.js`, `v4/catalogo-mapas.js`, `v4/assets/` | Estilos, menú/búsqueda, catálogo, 3 WebP | final |
| `v4/NOTICE.md`, `v4/assets-manifest.json` | Autoría y procedencia (sin URL privadas, §7) | final saneado |
| `v4/video.json` (o constante en `app.js`) | URL configurable del vídeo (§6) | nuevo |

Se respetan los nombres y rutas relativas de la autora: la hoja de estilos es la referencia de medidas y el LEEME lista los destinos que deben conservarse. Se mantiene `index.html#investigacion`, `auditoria-registro.html#sobre-autor` y `#juridica`. La raíz del sitio y `/v3/` no cambian (pregunta 1).

## 4. Integración con el mapa de T-413

- **«Explorar» → `mapa/`** (relativo), no `/v3/`. En la portada y en Comprender. El único cambio de enlace respecto a la final es ese; ORCID y LinkedIn se conservan.
- El mapa vive en `visor/v4/mapa/` (T-413, #910; copia de V3, V3 intacta). Contrato de enlace profundo (ya aceptado por T-413): `mapa/?territorio=<id>&regla=tres|dos|base|primero`; sin `regla`, «tres»; si el territorio no tiene doble vuelta, «primero» con aviso.
- Estilo compartido: `v4/styles.css` (paleta de la autora) y tokens de bloque de T-413 §2 (Izquierdas, Nacionalistas, Patriotas, Sin bloque, claro/oscuro) en un fichero aparte `v4/tokens-bloques.css` que crea T-415 en su PR 1 y T-413 consume sin redefinir. La portada es oscura por diseño; el mapa sigue T-413 (claro por defecto, tokens oscuros); no se fuerza un tema único (pregunta 6).
- Cabecera: se mantiene la de la autora (marca, navegación, «Auditoría y registro»); «Consultar el visor» apunta a `mapa/`. El mapa lleva su cabecera mínima con vuelta a la portada.
- Datos del mapa: lo de T-413 §5 (registro, `datos_abiertos/` con sha256); la portada no lee datos del visor.

## 5. Qué se cambia de la versión final

1. **Nomenclatura P (D-165)**: la final no usa M01–M08 en la portada (comprobado: `comprender.html` sin `M0x`); se revisa el texto de «Investigación» y «Comprender» y se usa P21–P32 donde se cite un paso (P21 Base y población, P22 Geometría y adyacencias, P23 Grafo, P24 Solución inicial, P25 Optimización, P26 Producto certificado, P31 Agregación, P32 Resultados por distrito; P27 auditoría, P33 puerta). Test: ningún `M0[1-8]` en el texto público.
2. **Sección «La doble vuelta»** en `comprender.html` (tercera sección, mismo estilo): texto «Cómo funciona» de T-413 §4, tres bloques con nombre y color (texto siempre escrito), ejemplo breve de T-409 §7, aviso «simulación sin valor oficial», distinción oficial/simulado, y enlace a `mapa/?regla=tres`. El texto final lo escribe el propietario; aquí se reserva el lugar y el borrador.
3. **Enlaces reales**: «Publicaciones y datos» y «Investigación» enlazan a rutas existentes (repositorio público, `datos_abiertos/INDEX.json`, metodología publicada); test de resolución; lo no publicado se omite (el LEEME de la autora ya evita simular un repositorio documental).
4. **Catálogo DOI**: se queda «pendiente» (`DDD_MAPS = []`, estado vacío veraz) hasta Zenodo. Se conservan CSV y `generar_catalogo.py` (decidido (pregunta 7, D-174): se quedan en el estudio hasta Zenodo y entonces pasan a `herramientas/`). Test: ningún DOI inventado; cada fila futura exige `doi`, `sha256` y versión.
5. **Presentación inicial**: la final no la tiene; no se añade. La sustituye el hueco de vídeo (§6).
6. **Accesibilidad**: se parte de lo de la autora (salto al contenido, foco, `aria-expanded` del menú, Escape, movimiento reducido) y se completa: `lang="es"`, una `h1` por página, `alt` real en las imágenes con contenido (hoy `alt=""` por decorativas: se mantiene si lo son), contraste ≥ 4,5 (muestra: marfil sobre carbón y naranja `#ef762b` sobre carbón: calcular y registrar), objetivos ≥ 44 px, sin hover obligatorio. Lo declara la autora: no equivale a certificación; el diseño tampoco lo afirma.

## 6. Vídeo de presentación (≈ 150 MB, fuera del repositorio)

- Hueco en la portada, bajo el título: bloque «Presentación» con póster estático (primera imagen o el WebP del Congreso), botón «Ver el vídeo» y enlace de texto equivalente.
- **URL configurable**: un solo valor (`video.json` o constante) que el propietario edita; vacío = el bloque no se pinta (nada roto). Si la URL es de un servicio de terceros, el vídeo se abre en pestaña nueva o se incrusta solo tras pulsar (sin cargar el reproductor ni cookies de terceros al abrir la página; coherente con `test_visor_sin_terceros` y D-104). Sin autoplay ni sonido automático.
- Accesibilidad: subtítulos y transcripción enlazados (los pone el propietario con el vídeo); `prefers-reduced-motion`: sin reproducción automática (ya no la hay).
- Alojamiento (decisión del propietario, 19-11): vídeo ya subido a R2, en la carpeta nueva de vídeos, con póster y subtítulos. **Búsqueda en el repositorio** (workflows, `configuracion/`, `docs/`, `visor/`): R2 solo se usa por la API S3 con credenciales (`https://<R2_ACCOUNT_ID>.r2.cloudflarestorage.com`, `R2_BUCKET`; `p70-archivo.yml`); no hay dominio propio, URL `r2.dev`, CDN ni cabeceras/CSP de medios documentados. Conclusión: **no consta que el bucket se sirva en público**, y esa URL privada no sirve para el visor. Opciones en la pregunta 5. La URL del vídeo y la de póster/subtítulos quedan configurables.

## 7. Origen y licencia de las 3 imágenes WebP

El manifiesto de la autora declara: ilustraciones generadas, «recurso aportado y seleccionado por Nessa», licencia = «autorización específica para esta entrega, sin licencia abierta ni cesión general», `rights_status: verified` limitado a ese cotejo. Es decir: origen documentado como generado con una herramienta de IA; **titularidad y licencia sin resolver**.
Problemas concretos: (a) `source_url` apunta a una biblioteca privada de ChatGPT con `account_id=personal`: **no debe publicarse** (se sustituye por «generada con herramienta de IA, fecha, aportada por Nessa»); (b) el LEEME dice «Nessa» mientras PROCEDENCIA dice «Vanesa»: **confirmado por el propietario (19-11): Nessa es Vanesa**; se declara «Vanesa»; (c) el logotipo («distintivo español») y el mapa decorativo pueden contener símbolos oficiales o fronteras: el LEEME ya avisa de que no acreditan delimitaciones electorales; (d) los derechos del contenido generado (originalidad y derechos de terceros): **el propietario asume el uso de las imágenes con nota de origen** (D-173/D-174); la nota no es un dictamen jurídico ni una licencia abierta.
Mientras no se resuelva, en `NOTICE.md` y en «Procedencia de los recursos» se dice solo lo que se sabe. Pregunta 3.

## 8. Licencia y propiedad intelectual

- Permiso: decisión literal del propietario (PROCEDENCIA.md): «Vanesa me los ha entregado para que los publique yo, tengo todo su permiso y su intención»; no se exige otro documento.
- La final pone el pie «© 2026 Jesús Francisco Murciego Vidal. Todos los derechos reservados.» (declaración del propietario; los textos jurídicos de la portada y de «Protección jurídica» son **de trabajo hasta su revisión**), coherente con `LICENSE` (apartado 1/3: visor y sitio, todos los derechos reservados). Para el material de la autora y las imágenes (terceros respecto al titular) se propone: `LICENSE` 1.2.0 (copia en `legacy/licencias/`, ANTERIOR) con una línea en el apartado 3 «Material de terceros» (portada, ilustraciones y catálogo de la autora: autoría conservada, publicados con permiso del propietario) — **edición de LICENSE solo con la autorización expresa del propietario en el chat que ejecuta**; no se hace aquí.
- `propiedad_intelectual/terceros/portada_v4_20261119/` (privada, `exclusion_publicacion.txt`): originales (primera entrega y final con `SHA256SUMS`), `MANIFEST.json` propio (autora, fechas, ficheros, tamaño, sha256, cita del permiso) y actualización de `SHA256SUMS`. Lo público lleva `v4/NOTICE.md` con autoría de la autora (como `visor/v2/galeria/NOTICE.md`) y declara las adaptaciones de DDD.
- **Revisión previa de metadatos y contenido** (antes de copiar a `v4/` o a `propiedad_intelectual/`; paso de la PR 1): xlsx de la primera entrega (autor, último modificado por, rutas, hojas ocultas, macros, enlaces locales; limpiar y guardar derivado, el original no se edita); WebP/JPG de la final (EXIF/XMP, texto, contenido visual: nombres, rutas, datos personales, marcas de terceros); `index.html`/JSON/CSV (rutas de usuario, correos, URL internas: ya se ve la `source_url` privada de §7). Test: ningún fichero publicable con `/Users/`, `C:\`, `chatgpt.com/library` ni correos o autores no declarados.

## 9. Matriz jurídico-electoral

La versión final **no incluye** Matrices. La primera entrega (190 reglas, 188 «Pendiente de cotejo», 19 normas con «Enlace BOE comprobado» en 16) no entra en la V4 inicial. Si se retoma: solo filas verificadas (BOE-A con id, URL oficial y sha256 o fecha de consulta); el resto «pendiente» sin contenido; nunca se publica sin verificar. Pregunta 4.

## 10. Reparto con T-413

T-413 (session_01KQDtFsuAFYY5GqXAJHVAkU) hace `v4/mapa/**` (#910) y `kind=doble_vuelta`; T-415 hace portada, Comprender, Auditoría y registro, estilos comunes, NOTICE/PI y el hueco de vídeo. Puntos de contacto: `v4/tokens-bloques.css` (T-415 crea, T-413 consume), el contrato `?territorio=&regla=` (T-413 fija, T-415 enlaza) y el texto de «La doble vuelta» (borrador T-413 §4, definitivo del propietario). Compartidos: `herramientas/`, workflows (aviso al Planificador).

## 11. Móvil, tests y orden de PR

Móvil: la autora comprobó 320/390/768/1440 px sin desbordamiento (`COMPROBACIONES.json`: método iframe, no hardware móvil). T-415 repite con Playwright (360×640, 390×844), menú desplegable ≤ 1000 px, Escape, `aria-expanded`, franja de autoría ≥ 82 px.

Tests (por rebanadas, esperados literales): 1) enlaces y anclas locales resuelven; 2) «Explorar» y «Consultar el visor» → `mapa/`, ninguno a `/v3/`; 3) sin `M0[1-8]`, con P21–P33 (tabla de D-165 como fixture); 4) catálogo vacío y sin DOI inventado; 5) menú: roles/teclado (Node); 6) contraste de los pares de color (leyendo el CSS); 7) sin recursos externos (`test_visor_sin_terceros`), vídeo no cargado sin URL ni sin pulsar; 8) sin `/Users/`, `chatgpt.com/library`, correos; `sha256` de los WebP = manifiesto; 9) sin scroll horizontal (Playwright, 2 tamaños); 10) regresión: `visor/v3/` e `index.html` de `visor/` sin cambios.

Orden de PR (una por capa; ninguna lanza ni publica; el propietario aprueba este diseño antes): 1) revisión de metadatos, `NOTICE.md`, `propiedad_intelectual/`, `LICENSE` (con su autorización); 2) `v4/` portada + estilos + `tokens-bloques.css` + vídeo configurable (tests 1–2, 6–9); 3) Comprender + «La doble vuelta» (texto del propietario, test 3); 4) Auditoría y registro + catálogo vacío (test 4); 5) enlaces cruzados con `v4/mapa/` (test 2, 10); 6) publicación: `v4/` en P40 (toca workflow: aviso al Planificador; Operador con frase D-52); 7) decidir raíz y destino de V3.

## 12. Preguntas — DECIDIDAS (D-174, 19-11): se adopta la recomendación en las 9

1. ¿La raíz pasa a `/v4/`? **Recomiendo** no: `/v4/` en paralelo hasta comparar con V3.
2. ¿`web/` o autónoma? **Recomiendo** `web/` (§2); la autónoma solo como copia de revisión.
3. ¿Origen y licencia de las 3 imágenes WebP? Hoy: generadas con IA, aportadas por Vanesa, sin licencia abierta ni cesión; el propietario asume el uso con nota de origen (D-173/D-174). **Recomiendo** que el propietario confirme (a) quién las generó y con qué herramienta, (b) que asume el uso, (c) ~~el nombre correcto de la autora~~ (resuelto: Nessa = Vanesa); publicar con `NOTICE.md` sin la URL privada; si hay dudas, sustituir el logotipo y el mapa por ilustraciones propias o CC0 y dejar el Congreso para después.
4. ¿La matriz jurídica de la primera entrega se retoma? **Recomiendo** no en la V4 inicial; retomarla como tarea aparte con cotejo oficial.
5. ¿Cómo se sirve en público el vídeo de R2 (póster y subtítulos incluidos)? Hoy no consta ninguna URL pública. Opciones: (a) **dominio propio** enlazado al bucket (p. ej. `media.diputadodedistrito.es`), con HTTPS, caché y rangos de bytes para el vídeo; (b) URL pública `r2.dev` activada en el bucket, sin dominio ni caché, limitada y no pensada para producción. **Recomiendo (a)**, con un bucket o prefijo solo de lectura pública para `videos/` (el resto del bucket, de archivo, sigue privado), y comprobar que `Content-Type` y `Accept-Ranges` son correctos. Mientras tanto, la URL queda vacía y el bloque no se pinta. El propietario confirma bucket, carpeta y nombre del dominio; implementarlo toca Cloudflare, no el repositorio.
6. ¿Un solo tema o portada oscura + mapa T-413 claro/oscuro? **Recomiendo** no forzar: portada oscura de la autora, mapa según T-413.
7. ¿Se mueven `generar_catalogo.py` y la plantilla CSV a `herramientas/`? **Recomiendo** sí cuando haya DOI reales (Zenodo); hasta entonces quedan en el estudio.
8. ¿Qué se enlaza como «metodología» publicada? **Recomiendo** solo lo ya publicado en el repositorio; si no hay página, omitir la tarjeta.
9. ¿Subtítulos y transcripción del vídeo? **Recomiendo** obligatorios para publicarlo (accesibilidad), a cargo del propietario.

Precisión de la 5 (D-174): bucket R2 **aparte**, público solo para vídeos, con subdominio propio; el bucket de trabajo sigue privado; los pasos de Cloudflare los da el Coordinador. La URL del vídeo queda vacía y configurable en el repositorio. Siguen fuera de esta decisión: la edición de `LICENSE` (autorización expresa del propietario) y cualquier publicación.
