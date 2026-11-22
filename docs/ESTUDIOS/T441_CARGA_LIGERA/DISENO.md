# T-441 · Carga ligera para el móvil — diseño (solo documento)

VERSIÓN: 1.1.0 · FECHA: 2026-11-22 · ESTADO: aprobado (D-192, 22-11: «sí a todo» a las 6 preguntas) · ANTERIOR: 1.0.0 (#971@d27f60d); 1.1.0 anota las respuestas del propietario

Encargo del propietario (22-11, vía Planificador): con las cifras de T-440 y el peso real de cada fichero de la V4, decir qué se
descarga hoy al abrir la portada y el mapa, proponer una primera vista ligera (móvil y visita rápida) con carga diferida, caché y
compresión, cuánto se ganaría y cómo encaja con ddd-web y R2 (D-186, D-188). Nada se implementa sin aprobación.

**Fuente de las cifras.** Pesos medidos sobre los ficheros de `main` (22-11): tamaño en disco y tamaño con gzip -9 (aproximación de lo
que viaja comprimido). Los ficheros que P40 genera al publicar (registro del visor, procedencia, vista territorial, índices de secciones y
doble vuelta) no están en el repositorio: sus cifras, y los tiempos reales, saldrán de T-440 (#970) y se añadirán en la tabla §1.3
antes de aprobar. Hasta entonces, «por medir».

## 1. Qué se descarga hoy

### 1.1 Portada (`/`)

| Fichero | Peso | Comprimido | Cuándo |
|---|---:|---:|---|
| `index.html` | 5,1 KB | 2,0 KB | al abrir |
| `styles.css` | 17,4 KB | 5,0 KB | al abrir |
| `app.js` | 5,9 KB | 2,2 KB | al abrir (diferido) |
| `assets/congreso.webp` (foto principal, 1016×598) | 156,3 KB | 156,3 KB | al abrir, prioridad alta |
| `assets/mapa_espana.webp` (738×774) | 65,4 KB | 65,4 KB | al abrir |
| `assets/logotipo_espana.webp` | 2,8 KB | 2,8 KB | al abrir |
| `video.json` | 0,1 KB | 0,1 KB | al abrir |
| vídeo (`media.diputadodedistrito.es/Video_DDD.mp4`) | por medir | — | al abrir se piden sus **metadatos** (`preload="metadata"`); el vídeo, al pulsar |
| **Total** | **≈ 253 KB** + metadatos del vídeo | **≈ 234 KB** | |

Las imágenes son el 89 % y no se comprimen más (WebP ya lo está). En el móvil se descarga la misma foto de 1016 px que en el ordenador.

### 1.2 Mapa (`/mapa/`, Explorar)

| Fichero | Peso | Comprimido | Cuándo |
|---|---:|---:|---|
| `mapa/index.html` | 14,5 KB | 5,2 KB | al abrir |
| `styles.css`, `tokens-bloques.css`, `explorar.css` | 36,4 KB | 10,6 KB | al abrir |
| `maplibre-gl.css` | 69,4 KB | 10,0 KB | al abrir |
| **`maplibre-gl.js`** (librería del mapa) | **939,4 KB** | **247,2 KB** | al abrir (diferido) |
| `explorar.js`, `dv.js`, `galeria.js`, `app.js` | 81,0 KB | 27,2 KB | al abrir (diferido) |
| `v2/datos/provincias.json` | 358,1 KB | 102,7 KB | al abrir |
| `v2/datos/comunidades.json` | 161,3 KB | 46,5 KB | al abrir |
| `datos/INDEX.json` | 105,1 KB | 20,6 KB | al abrir |
| `calendario.json` | 2,9 KB | 0,4 KB | al abrir |
| registro del visor, procedencia, vista territorial, índice de secciones, índice de la doble vuelta | por medir | por medir | al abrir (los cinco, en paralelo) |
| distritos del territorio elegido (`datos/<territorio>/distritos.geojson`) | por medir | por medir | al elegir territorio |
| secciones censales de la provincia | por medir | por medir | al acercarse |
| **Total conocido al abrir** | **≈ 1,77 MB** | **≈ 470 KB** | + los cinco «por medir» |

Lo que más pesa es la librería del mapa (más de la mitad de lo comprimido) y la geometría completa de provincias y comunidades,
que se baja entera aunque la persona solo mire un momento.

### 1.3 Cifras de T-440 (se rellena con el run del Operador)

| Página o fichero | Primer byte (ms) | Total (ms) | Bytes con / sin compresión |
|---|---:|---:|---:|
| (pendiente del run de `medir-web`) | | | |

Lo que se confirmará con ellas: si GitHub Pages comprime hoy JSON y GeoJSON (y con qué), el tiempo hasta el primer byte desde
fuera y el peso de los cinco ficheros «por medir».

## 2. Propuesta: primera vista ligera

Principio: **la primera vista enseña algo útil con poco, y lo pesado llega solo si la persona lo pide.** Sin cambiar lo que se ve en el
ordenador salvo que el propietario lo decida (pregunta 2).

### 2.1 Portada

1. **Fotos a la medida de la pantalla**: dos tamaños de cada imagen (ancho de móvil ≈ 480 px y el actual), y el navegador elige.
   La foto principal pasaría de 156 KB a unos 35-45 KB en el móvil (estimación por medir al generarla).
2. **El mapa de España de la portada, cuando se vea**: carga diferida (`loading="lazy"`): no se baja si la persona no baja la página.
3. **Vídeo sin metadatos al abrir**: `preload="none"` y póster ligero; el vídeo se pide solo al pulsar «reproducir».
4. Resultado estimado en el móvil: **≈ 234 KB → ≈ 50-60 KB** al abrir.

### 2.2 Mapa (Explorar)

1. **Vista rápida al abrir** (en el móvil siempre; en el ordenador, pregunta 2): una imagen ligera de España por distritos con el
   color de cada bloque y la lista de territorios, hecha con la geometría simplificada (§2.3) y pintada sin la librería del mapa
   (SVG, como ya hace `geo.js` de T-415). Botón «Abrir el mapa interactivo» para lo demás.
2. **La librería del mapa, solo al pedirlo**: `maplibre-gl.js` y su CSS se cargan al pulsar el botón, al elegir un territorio o al
   acercarse. Ahorra ≈ 257 KB comprimidos en la primera vista.
3. **Datos a demanda**: al abrir solo `actual.json`, el índice y la geometría simplificada; el registro del visor, la procedencia,
   la vista territorial, el calendario y el índice de secciones se piden cuando se abre el panel que los usa.
4. **Geometría en dos niveles**: provincias y comunidades simplificadas para la vista de España (P40 las genera con tolerancia fija,
   como ya hace con la doble vuelta: Douglas-Peucker, `publicar_doble_vuelta.py`); la geometría completa solo al acercarse.
   Estimación: 149 KB comprimidos → 20-30 KB (por medir al generarla).
5. **Aviso honesto**: si algo tarda, el texto dice qué se está cargando, en llano («Cargando el mapa de Madrid…»).
6. Resultado estimado en el móvil: **≈ 470 KB + cinco «por medir» → ≈ 60-90 KB** en la primera vista; el resto, solo si se usa.

### 2.3 Compresión

- **Textos (HTML, CSS, JS)**: Cloudflare Pages los comprime solo (gzip o brotli; por verificar en el ensayo de T-430).
- **Datos en R2 (`datos.diputadodedistrito.es`)**: Cloudflare comprime algunos tipos y otros no según el `Content-Type`
  (por verificar; `application/geo+json` puede quedar fuera). Opción segura: P40 sube los JSON y GeoJSON **ya comprimidos** con
  `Content-Encoding: gzip` y la web los recibe igual (pregunta 4). El sha256 de `actual.json` se calcula sobre el contenido sin comprimir,
  que es lo que comprueba el navegador.

### 2.4 Caché

- **Datos (R2, D-188)**: solo la vigente, caché 60 s. Con `ETag`, la segunda visita revalida y recibe «sin cambios» (unos cientos de
  bytes) en vez de volver a bajar todo (por verificar que R2 da `ETag` por su dominio propio).
- **Código y estilos (ddd-web)**: `construir.py` (T-430 §6) añade a cada enlace de CSS/JS/imagen una marca del contenido
  (`styles.css?v=<8 cifras>`): así pueden guardarse un año en el navegador y un cambio de texto se ve al momento porque cambia la marca.
  Las páginas HTML, sin caché larga.
- **Librería del mapa**: misma marca; es lo más pesado y casi nunca cambia: se baja una vez por visitante.

## 3. Cuánto se ganaría (estimación; se confirma con T-440 y con el primer ensayo)

| Primera vista en el móvil | Hoy (comprimido) | Propuesta | Ahorro |
|---|---:|---:|---:|
| Portada | ≈ 234 KB | ≈ 50-60 KB | ≈ 75 % |
| Mapa | ≈ 470 KB + 5 por medir | ≈ 60-90 KB | ≥ 80 % |
| Segunda visita (todo igual) | casi todo otra vez | revalidación (≈ KB) | ≈ 95 % |

En una conexión móvil lenta (por ejemplo 1,5 Mbit/s reales), 470 KB son ≈ 2,5 s solo de descarga; 80 KB, ≈ 0,4 s.

## 4. Encaje con ddd-web y R2 (D-186, D-188)

- **ddd-web**: todo lo de §2.1, §2.2 (1, 2, 3, 5) y la marca de caché de §2.4 son cambios de la web: van al repositorio nuevo, se
  prueban en la vista previa por rama y no tocan el motor. Las pruebas de segundos de ddd-web (T-430 §6) suman una: «el peso de la
  primera vista no pasa de N KB» (pregunta 5).
- **R2 / P40**: la geometría simplificada (§2.2.4) y, si se aprueba, la compresión previa (§2.3) las genera P40 en `web/actual/`,
  dentro de la misma publicación de solo la vigente (D-188), con su sha256 en `actual.json`. Ningún dato nuevo en git.
- **Orden**: después del corte de T-430 (no se rehace dos veces en GitHub Pages). Lo de la portada (§2.1) podría ir antes en `visor/v4/`
  si el propietario lo quiere ya (pregunta 6).

## 5. Riesgos

| Riesgo | Mitigación |
|---|---|
| La vista rápida simplifica fronteras y alguien lo confunde con el mapa exacto | aviso visible «vista simplificada; abre el mapa para el detalle» y el mapa completo a un toque |
| Dos caminos de pintado (SVG y librería) que divergen en colores | los dos leen la misma tabla de colores (`tokens-bloques.css`) y una prueba compara la lista de distritos y colores |
| Compresión previa mal declarada (doble compresión) | prueba en P40 que baja un fichero por el dominio público y compara el sha256 con `actual.json` |
| Detectar «móvil» falla | se decide por el ancho de pantalla, no por el navegador; en caso de duda, vista rápida (es la que menos pesa) |
| Cifras de esta propuesta sin medir | §1.3 se rellena con T-440 antes de aprobar; ninguna cifra de ahorro se publica hasta medirla en el ensayo |

## 6. Preguntas al propietario (con recomendación)

**Respuestas (D-192, 22-11, propietario vía Planificador): sí a todo.** (1) Vista rápida del mapa con el botón «Abrir el mapa
interactivo». (2) Solo en el móvil al principio. (3) Fotos en dos tamaños y vídeo solo al pulsar. (4) Compresión previa en R2: se decide
con las cifras de T-440. (5) Prueba de tope de 100 KB comprimidos para la primera vista en el móvil. (6) Todo después del corte de
ddd-web, salvo la portada (§2.1), que va ya en `visor/v4/` en una PR pequeña (T-442).


1. **¿Vista rápida en el mapa con botón «Abrir el mapa interactivo»?** *Recomiendo sí*: es el mayor ahorro (la librería del mapa es
   más de la mitad de lo que se baja).
2. **¿Solo en el móvil o también en el ordenador?** *Recomiendo solo en el móvil al principio*; en el ordenador el mapa completo abre
   como hoy. Se revisa con datos de uso.
3. **¿Fotos en dos tamaños y vídeo que se pide solo al pulsar?** *Recomiendo sí*: no cambia lo que se ve y ahorra ≈ 75 % en la portada.
4. **¿P40 sube los datos ya comprimidos a R2?** *Recomiendo decidirlo con T-440 y el ensayo*: si Cloudflare ya los comprime por su
   dominio, no hace falta; si no, sí.
5. **¿Una prueba de peso máximo de la primera vista en ddd-web?** *Recomiendo sí*, con tope de 100 KB comprimidos en el móvil, para
   que una imagen pegada sin reducir no lo eche a perder sin que nadie lo note.
6. **¿Cuándo?** *Recomiendo después del corte de T-430* (en ddd-web), salvo la portada (§2.1), que puede ir antes en `visor/v4/` en
   una PR pequeña si se quiere ganar ya.
