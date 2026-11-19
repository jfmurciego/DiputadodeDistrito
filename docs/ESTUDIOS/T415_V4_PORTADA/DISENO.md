# T-415 · V4: portada de Vanesa + mapa con doble vuelta — diseño (solo documento)

VERSIÓN: 1.0.1 · FECHA: 2026-11-19 · ESTADO: propuesto (pendiente de aprobación del propietario) · ANTERIOR: 1.0.0 (misma PR, sin fusionar)

Decisión del propietario (19-11): la V4 (`visor/v4/`) es la versión nueva completa: portada de Vanesa como entrada
(Comprender, Explorar, Investigación, Matrices) y mapa con la doble vuelta de T-413 (D-172). La V3 no se toca y queda para comparar.
Originales en `original/` (PR #908, rama `planificador/t415-v4-originales`; hasta que se fusione no están en `main`). Procedencia: `PROCEDENCIA.md`.
No toca `visor/`, `web/` ni workflows. Nada se publica.

## 1. Rutas de `visor/v4/`

Sitio estático, sin servidor; rutas relativas (funciona bajo `/v4/` y en doble clic).

| Ruta | Contenido | Origen |
|---|---|---|
| `v4/index.html` | Portada: presentación inicial, identidad, introducción, enlaces a las cuatro secciones | `original/index.html` |
| `v4/comprender/` | Tres pestañas de Comprender + sección nueva «La doble vuelta» (§3) | portada + T-413 §4 |
| `v4/mapa/` | Mapa V4: regla de elección, leyenda, ficha de distrito | T-413 sobre base V3 (§2) |
| `v4/investigacion/` | Método P21–P33, fuentes, datos abiertos, limitaciones; selector de territorio | portada |
| `v4/matrices/` | Matriz jurídico-electoral por ámbito (solo lo verificado, §4) | `matriz_juridico_electoral_v1.json` |
| `v4/comun/` | `v4.css` (tokens claro/oscuro), `v4.js` (menú, tema, presentación), fuentes y fixtures | nuevo |
| `v4/datos/` | JSON derivados de la matriz, con sha256 en `MANIFEST.json` | nuevo |

Una página por sección (no una sola página con anclas, como el prototipo): rutas enlazables, foco y título propios, carga más ligera en móvil.
Menú común generado una sola vez en `v4.js`. La raíz del sitio y `/v3/` no cambian; el cambio de la raíz a `/v4/` es decisión aparte (pregunta 1).

## 2. Integración portada ↔ mapa de T-413

- «Explorar» enlaza a `v4/mapa/` (relativo), nunca a `/v3/` ni a una URL absoluta. El prototipo enlazaba a `https://diputadodedistrito.es/v3/`: se sustituye.
- El mapa V4 parte del código de V3 (`v3.js`/`v3.css`, mapa, escenarios, galería) **copiado** a `v4/mapa/`, no compartido: así V3 queda intacta y comparable.
  Sobre esa copia T-413 aplica su diseño tal cual (selector «Tres bloques / Dos bloques / Sin coaliciones / Más votado», colores por bloque, ficha, comparación, tokens oscuros, `?regla=`).
- Cabecera común: marca + menú de las cuatro secciones + «Ver V3» (solo mientras V3 exista) en la portada y el mapa; el mapa ocupa la pantalla, con la cabecera plegada en móvil.
- Los tokens de bloque (T-413 §2) viven en `v4/comun/v4.css` y los usan portada, Comprender y mapa: un solo tema claro/oscuro para toda la V4 (cierra la pregunta 6 de T-413 en V4).
- Datos: el mapa lee lo mismo que V3 (registro `publicaciones_visor.json`, `datos_abiertos/` con sha256) más `kind=doble_vuelta` (T-413 §5). Nada se recalcula en el navegador.
- Contrato entre portada y mapa: enlaces profundos `v4/mapa/?territorio=<id>&regla=tres|dos|base|primero`; la portada puede enlazar a un territorio y regla concretos (p. ej. desde «La doble vuelta»).

## 3. Cambios respecto a los originales

1. **Nomenclatura**: «Método M01–M08» → P de D-165 (01→P21 Base y población, 02→P22 Geometría y adyacencias, 03→P23 Grafo, 04→P24 Solución inicial,
   05→P25 Optimización, 06→P26 Producto certificado, 07→P31 Agregación, 08→P32 Resultados por distrito; auditoría P27; puerta P33). Los datos guardados siguen con nombre viejo hasta T-313:
   el texto público usa solo P y evita ids de ficheros. La V4 no se publica antes de que el texto esté alineado con el estado real de T-313 (pregunta 2).
2. **Sección «La doble vuelta»** en Comprender (cuarta pestaña): texto de T-413 §4 («Cómo funciona»), tres bloques con nombre y color, ejemplo breve de T-409 §7, aviso fijo «simulación sin valor oficial», distinción oficial/simulado (ya pedida en el LEEME), enlace al mapa con la regla por defecto. El texto final lo escribe el propietario (`web/textos.md` es suyo): aquí solo se reserva el lugar y se cita el borrador de T-413.
3. **Enlaces reales**: los genéricos de documentación se sustituyen por rutas existentes verificadas por un test (§6): repositorio público, `datos_abiertos/INDEX.json`, metodología, BOE. Un enlace que no resuelve en el repositorio falla el test; no se enlaza a lo que no esté publicado (se omite la tarjeta).
4. **Presentación inicial**: se conserva (6 s, sin audio, «Saltar», una vez por sesión) con cambios: se muestra solo en `v4/index.html`; **no** se reproduce con `prefers-reduced-motion` (ya) ni si hay `?sinintro`; el contenido se pinta debajo desde el primer instante (la presentación es un velo, no bloquea la carga ni el mapa); `sessionStorage` envuelto en `try/catch`; «Ver presentación inicial» como enlace en el pie, no en la cabecera.
5. **Accesibilidad**: `lang="es"`, enlace «Saltar al contenido», una sola `h1` por página, pestañas con patrón WAI-ARIA (`role=tablist`, flechas, Inicio/Fin), velo con `role=dialog` + `aria-modal`, foco atrapado y devuelto al cerrar y `Esc` cierra; objetivos ≥ 44 px, texto ≥ 16 px (14 px en controles densos), contraste WCAG 2.1 (≥ 4,5 texto, ≥ 3 objetos) en claro y oscuro; el color nunca es el único portador; sin hover obligatorio; barras con texto equivalente.
6. **Estructura**: HTML autónomo de 38 KB → páginas con CSS/JS comunes; sin librerías externas (coherente con `test_visor_sin_terceros`).
7. **Lo que no cambia**: autoría y contenido de Vanesa; jerarquía aprobada (portada → Comprender/Explorar → Investigación verificable → Matrices).

## 4. Matriz jurídico-electoral

Estado de los originales (medido sobre `matriz_juridico_electoral_v1.json`): 19 ámbitos; 190 filas de reglas, **188 «Pendiente de cotejo»**, 2 «Texto cotejado» (art. 2 y art. 26.1);
19 normas, 16 «Enlace BOE comprobado» (el enlace existe; no es verificación del contenido) y 3 «Regulación específica por cotejar». La propia matriz se declara «de trabajo».

Regla de publicación (propuesta): una fila solo sale con estado **«verificada»**: norma con `BOE-A-…`, URL oficial (`boe.es`, boletín autonómico o `congreso.es`) y, si se cita de un documento descargado, su sha256; artículo y vigencia consultada con fecha.
Todo lo demás se muestra como **«pendiente»** (etiqueta visible, sin contenido jurídico) o no se muestra. Nunca se publica la «regla comprobada» ni el «efecto en el visor» de una fila no verificada.

- Datos: `v4/datos/matriz.json` generado por un script (`herramientas/`, tarea de implementación) desde el original, que filtra y marca; el original no se edita (sha256 en `original/SHA256SUMS`).
- Verificación: cada fila verificada se coteja con la fuente oficial (descarga con sha256 en `datos/`, como el BOE de escaños 2023 en CLAUDE.md); nunca de memoria. Quién cota (propietario/Vanesa/asistente) es la pregunta 4.
- Test: ninguna fila publicable sin `ref_boe`/URL oficial y fecha; ningún estado «pendiente» con texto de regla; el JSON publicado coincide con su manifiesto.
- **No se publica sin verificar**: la sección Matrices se entrega con las 19 normas (identificadas, enlace oficial) y «pendiente» en las reglas hasta cotejar; ninguna PR la publica sin permiso del propietario.

## 5. Reparto de trabajo con T-413

T-413 (session_01KQDtFsuAFYY5GqXAJHVAkU) pasa a hacer **el mapa en `visor/v4/mapa/`**, no en V3. Reparto por carpetas, sin solaparse:

| Quién | Territorio |
|---|---|
| T-413 | `v4/mapa/**`, sus tests, `kind=doble_vuelta` (P40/registro: ya previsto en su orden de PR), textos del mapa |
| T-415 | `v4/index.html`, `v4/comprender/`, `v4/investigacion/`, `v4/matrices/`, `v4/comun/`, `v4/datos/`, licencia y PI |

Puntos de contacto: (a) `v4/comun/v4.css` (tokens): lo crea T-415 en su PR 1 con los tokens de T-413 §2; T-413 los consume y no los redefine; (b) menú y cabecera común (`v4.js`): T-415; (c) enlace profundo `?territorio=&regla=` y la sección «La doble vuelta»: T-413 fija el contrato; T-415 enlaza.
Antes de nada, T-413 decide si su PR 5 (selector) parte ya de `v4/mapa/` (copia de V3). Lo ya hecho de T-413 en V3 (diseño #905) se reutiliza; si tocó `visor/v3/`, se revierte en esa PR (V3 intacta). Aviso previo a T-413 y al Planificador: `herramientas/` y workflows son compartidos.

## 6. Móvil, tests y orden de PR

Móvil: gutter 16 px, sin desbordamiento horizontal, menú en hoja (≥ 44 px), pestañas desplazables, presentación a pantalla completa con «Saltar» visible, 360×640 y 390×844 (Playwright), `prefers-color-scheme` y `prefers-reduced-motion`.

Tests (por rebanadas, esperados literales, no recalculados):
1. Rutas: cada página existe, tiene `lang`, `title`, una `h1`; todos los enlaces internos resuelven.
2. Enlaces externos de la portada: solo dominios permitidos (BOE, repositorio, INE); ninguno a `/v3/`; «Explorar» → `mapa/`.
3. Nomenclatura: ningún `M0[1-8]` en el texto público; sí P21–P33 (con tabla de D-165 como fixture literal).
4. Presentación: no se reproduce con movimiento reducido ni en la segunda visita; «Saltar» y `Esc` la cierran; foco devuelto.
5. Pestañas: roles ARIA y teclado (Node, como `test_visor_v3_ui.js`).
6. Contraste de tokens (claro/oscuro) leyendo el CSS.
7. Matriz: ninguna fila publicable sin fuente oficial y fecha; las 188 pendientes salen como «pendiente» sin texto de regla; JSON = manifiesto.
8. Sin terceros ni red externa (`test_visor_sin_terceros`); sin scroll horizontal en 2 tamaños (Playwright).
9. Regresión: `visor/v3/` y `visor/index.html` sin cambios (hash del árbol contra `main`).

Orden de PR (una por capa; ninguna lanza ni publica; el propietario aprueba este diseño antes):
1. Licencia y PI (§7): `LICENSE` 1.2.0, `propiedad_intelectual/`, revisión de metadatos (§7). 2. `v4/comun/` + portada + presentación + menú (tests 1–4, 6, 8). 3. Comprender, con «La doble vuelta» (texto del propietario). 4. Investigación con P y enlaces reales. 5. Matrices: script de filtrado + página (test 7); contenido solo verificado. 6. Integración con `v4/mapa/` de T-413 (enlaces, test 2/9). 7. Publicación: añadir `v4/` al P40 (toca workflow: aviso al Planificador; Operador, frase D-52). 8. Decidir la raíz y el destino de V3.

## 7. Licencia y propiedad intelectual

El material de Vanesa no es obra del titular (LICENSE apartado 1 dice «propiedad del titular» salvo excepciones del 3).
- `LICENSE` 1.2.0 (copia en `legacy/licencias/` con ANTERIOR): en el apartado 3, «Material de terceros», añadir: portada, maquetas y matriz jurídico-electoral de trabajo de Vanesa (`visor/v4/` portada y `v4/datos/matriz*`), con la licencia que acuerden (pregunta 3) y sin ceder el resto.
  Es edición de LICENSE: requiere la autorización expresa del propietario en el chat que ejecuta (CLAUDE.md); no se hace en esta PR.
- `propiedad_intelectual/`: el repositorio ya trae `MANIFEST.json`/`SHA256SUMS` del paquete Deslinde. Para lo de Vanesa se propone una subcarpeta `propiedad_intelectual/terceros/vanesa_20261119/` con los originales (sha256 de `original/SHA256SUMS`), un `MANIFEST.json` propio (autora, fecha de entrega, ficheros, tamaño, sha256) y la cita literal del permiso (PROCEDENCIA.md); `SHA256SUMS` actualizado. Esa carpeta es privada (`exclusion_publicacion.txt`); lo público lleva un `NOTICE.md` en `v4/` con autoría (como `visor/v2/galeria/NOTICE.md`).
- Autoría: «Portada y matriz de trabajo: Vanesa» en `NOTICE.md`, en el pie de la portada y en los metadatos de los ficheros derivados; los cambios de DDD se declaran como adaptación.
- Permiso: resuelto por decisión literal del propietario (19-11, PROCEDENCIA.md, #908@a332bfd): «Vanesa me los ha entregado para que los publique yo, tengo todo su permiso y su intención»; no se exige otro documento. Se cita en el MANIFEST.
- **Revisión previa de metadatos y contenido** (antes de copiar nada a `v4/` o `propiedad_intelectual/`; paso de la PR 1):
  1. `Matriz_juridico_electoral_DDD_v1.xlsx`: leer `docProps/core.xml` y `app.xml` (autor, último modificado por, empresa, fechas), rutas absolutas o de usuario en vínculos externos, nombres de hoja y comentarios, hojas ocultas, macros, enlaces a ficheros locales; limpiar o declarar lo que identifique a personas o equipos distintos de la autora. El xlsx limpio se guarda como derivado; el original no se edita (sha256).
  2. PNG (`preview_*`, `referencia_estructura`): inspección visual de contenido (nombres, rutas, datos personales, marcas de terceros, mapas con fuentes sin licencia) y metadatos EXIF/tEXt/iTXt (`exiftool`/`pngcheck`). Los que no se publiquen quedan solo en `propiedad_intelectual/` (privado); los públicos se regeneran sin metadatos.
  3. `index.html` y JSON: buscar rutas de usuario, correos, URL internas, comentarios.
  Resultado en `v4/NOTICE.md` y en el MANIFEST (qué se publicó, qué se limpió). Test: ningún fichero publicable con `/Users/`, `C:\\`, correos o campos de autor distintos de los declarados.

## 8. Preguntas abiertas (con recomendación)

1. ¿La raíz del sitio pasa a `/v4/` al publicar? **Recomiendo** no: `/v4/` en paralelo hasta comparar; la raíz sigue en `/v3/`.
2. ¿V4 se publica antes o después de T-313 (nomenclatura P en datos)? **Recomiendo** el texto ya en P (D-165) y no enlazar nombres de ficheros; publicar tras T-313 si hay ids visibles.
3. ¿Licencia del material de Vanesa (el permiso de publicar ya está resuelto)? **Recomiendo** CC BY 4.0 para el texto y los datos de la matriz y «todos los derechos reservados al sitio» para el código, con atribución a Vanesa; la decide ella con el propietario.
4. ¿Quién coteja la matriz y con qué criterio? **Recomiendo** Vanesa propone, el asistente comprueba con descarga oficial y sha256, el propietario aprueba; empezar por LOREG y las 17 leyes electorales autonómicas.
5. ¿«Matrices» sale en la primera publicación con solo normas identificadas? **Recomiendo** sí con «pendiente» visible, o ocultarla hasta tener ≥ 1 ámbito completo; prefiero ocultarla.
6. ¿Una página por sección o una sola? **Recomiendo** páginas separadas (§1).
7. ¿Se copia el código de V3 en `v4/mapa/` o se comparte? **Recomiendo** copia, para que V3 no se toque.
8. ¿La presentación de 6 s se mantiene tal cual? **Recomiendo** sí, con «Saltar», una vez por sesión y sin bloquear la carga.
9. ¿«Ver V3» en la cabecera? **Recomiendo** sí hasta decidir su destino.
