# Diputado de Distrito: diseño aplicado y recursos integrados

## Qué se entrega

La portada aplica la composición española elegida por Nessa: Congreso con león y bandera, mapa decorativo de España, distintivo español, fondo carbón, tipografía marfil, acento naranja y franjas granates. Conserva los mensajes «Contra el sistema de partidos», «Tu representante» y «Abstención consciente».

El HTML anterior dependía de una hoja de estilos y de imágenes en una carpeta separada. Abrir únicamente ese archivo no transportaba todos sus recursos. Esta entrega ofrece dos formatos del mismo diseño:

- `DDD_portada_autonoma.html`: presentación en un solo archivo, con imágenes, estilos, catálogo y JavaScript incorporados. Sirve para abrirla, revisarla y enviarla sin separar los recursos. Su navegación entre Inicio, Comprender y Auditoría y registro funciona dentro del propio archivo.
- `web/`: implementación modular en HTML, CSS y JavaScript, preparada para incorporar al alojamiento del proyecto. Deben conservarse sus carpetas y rutas relativas.

El visor permanece enlazado en `https://diputadodedistrito.es/v3/`. Esta entrega no cambia su código, datos, geometrías ni comportamiento, y no acredita una modificación de la web pública.

## Archivos de implementación

| Archivo | Función |
|---|---|
| `web/index.html` | Portada con imágenes españolas, accesos principales, investigación y autoría compacta. |
| `web/comprender.html` | Introducción a los conceptos del proyecto y accesos al visor y a las publicaciones. |
| `web/auditoria-registro.html` | Catálogo por mapa, autor, procedencia de imágenes y reserva de derechos. |
| `web/styles.css` | Paleta, composición, reglas adaptativas, foco visible y movimiento reducido. |
| `web/app.js` | Menú móvil y búsqueda del catálogo; expone `window.DDDInit` para la presentación autónoma. |
| `web/catalogo-mapas.js` | Datos de los mapas publicados. Se entrega vacío porque no se han proporcionado DOI individuales para incorporar. |
| `web/plantilla_doi_por_mapa.csv` | Columnas de entrada del catálogo, sin registros inventados. |
| `web/generar_catalogo.py` | Conversión del CSV revisado a `catalogo-mapas.js`. |
| `web/assets/` | Los tres WebP efectivamente utilizados, incluidos en la entrega. |
| `web/assets-manifest.json` | Procedencia, alcance de la autorización, dimensiones y SHA-256 de cada WebP. |
| `generar_portada_autonoma.py` | Genera la presentación de un solo archivo a partir de `web/`. |

Las capturas finales y el resultado de las comprobaciones de navegador acompañan la entrega como evidencias separadas. No forman parte de los recursos que necesita cargar la web.

## Composición que debe conservarse

| Componente | Regla de implementación |
|---|---|
| Cabecera | Marca «Diputado de Distrito», navegación y botón «Auditoría y registro». Sin botón Método. |
| Imagen de apertura | Congreso, león y bandera a la izquierda; texto y mapa decorativo a la derecha. Las imágenes son elementos `img` con dimensiones reservadas. |
| Mensaje | «DIPUTADO DE DISTRITO», «Contra el sistema de partidos», «TU REPRESENTANTE» y «ABSTENCIÓN CONSCIENTE». Sin voz, sonido ni reproducción automática. |
| Acciones principales | Dos accesos marfil: Comprender y Explorar. El primero abre la página local; el segundo abre el visor existente. |
| Investigación | Franja granate con enlace a «Publicaciones y procedencia». El enlace conduce al registro, sin simular un repositorio documental ya completado. |
| Auditoría y autoría | Franja compacta, de 82 px de altura mínima en escritorio. El detalle se concentra en su página propia. |
| Pie | Copyright y reserva de acciones, con enlaces a Protección jurídica y Sobre el autor. |

La hoja de estilos es la referencia de medidas. La anchura máxima del contenido es 1360 px. Los márgenes laterales pasan de 40 px en escritorio a 24 px y después a 16 px en móvil. A partir de 1000 px hacia abajo aparece el menú desplegable; por debajo de 600 px las tarjetas principales y la franja de autoría se apilan. La composición móvil mantiene el Congreso y el mapa visibles, en lugar de ocultarlos mediante opacidad.

### Colores y tipografía

| Variable | Valor | Uso |
|---|---|---|
| `--coal` | `#0b0d0e` | Fondo principal. |
| `--cream` / `--white` | `#f5f1e8` | Texto y superficies claras. |
| `--orange` | `#ef762b` | Distrito, abstención, iconos y acentos. |
| `--rust` | `#c2410c` | Acento auxiliar. |
| `--wine` | `#65151e` | Identidad granate. |
| `--muted` | `#cbbfb1` | Información secundaria. |
| `--border` | `#76573f` | Separaciones. |

Los títulos usan Georgia, con Times New Roman como alternativa; la navegación y los controles usan Arial, Segoe UI y la fuente del sistema. No se necesita descargar una fuente externa.

El código incorpora un enlace para saltar al contenido, foco visible, cierre del menú con Escape y reglas para `prefers-reduced-motion`. Estos mecanismos no equivalen por sí solos a una certificación de accesibilidad.

## Rutas y conexión con el visor

En la versión modular, conservar estos destinos:

| Acción | Destino |
|---|---|
| Inicio | `index.html` |
| Comprender | `comprender.html` |
| Explorar / Consultar el visor | `https://diputadodedistrito.es/v3/` |
| Investigación | `index.html#investigacion` |
| Auditoría y registro | `auditoria-registro.html` |
| Sobre el autor | `auditoria-registro.html#sobre-autor` |
| Protección jurídica | `auditoria-registro.html#juridica` |

En el HTML autónomo, esas rutas se convierten en `#inicio`, `#comprender` y `#registro`, con subanclas como `#inicio/investigacion` o `#registro/sobre-autor`. El enrutador conserva el historial del navegador y solo activa una plantilla cada vez. El enlace al visor y los perfiles externos siguen abriéndose en sus destinos reales; el contenido remoto requiere conexión.

Para integrar la portada, copiar el contenido de `web/` a la carpeta de destino manteniendo juntos los HTML, `styles.css`, los dos archivos JavaScript y `assets/`. No copiar solo `index.html`. Las rutas relativas permiten servir el conjunto desde la raíz del dominio o desde una subcarpeta sin modificar los recursos. No es necesario instalar paquetes, compilar ni incorporar un framework.

Antes de sustituir una portada publicada, conservar la versión anterior y comprobar el conjunto en el alojamiento de pruebas. Excluir archivos temporales de comprobación como `__qa.html`, así como copias autónomas utilizadas únicamente durante las pruebas. No sobrescribir la carpeta `/v3/`. Si el proyecto real emplea otra arquitectura, trasladar los componentes conservando los destinos y las rutas de recursos; esa adaptación no se presupone realizada aquí.

## Imágenes elegidas y alcance de uso

Los tres WebP se conservan de la referencia elegida por Nessa. No se han sustituido por imágenes de archivo diferentes:

| Recurso | Dimensiones | Función |
|---|---:|---|
| `assets/congreso.webp` | 1016 × 598 | Ilustración de apertura con Congreso, león y bandera. |
| `assets/mapa_espana.webp` | 738 × 774 | Imagen decorativa de España en la cabecera. |
| `assets/logotipo_espana.webp` | 210 × 165 | Distintivo junto al nombre del proyecto. |

Son ilustraciones generadas aportadas y elegidas para este trabajo, cuya integración en esta entrega y su implementación por Jesús ha sido expresamente solicitada. Esa autorización concreta es el fundamento registrado en el manifiesto. No se declara una licencia abierta, una cesión general de derechos ni una autoría exclusiva sobre cada componente visual.

Las ilustraciones no se presentan como fotografías documentales. El mapa de cabecera no acredita fronteras administrativas ni delimitaciones electorales: la cartografía consultable pertenece al visor. La página de Auditoría y registro explica esta procedencia al visitante. El uso decorativo se refleja en `alt=""`; el distintivo se acompaña del nombre escrito del proyecto.

`rights_status: verified` significa que se ha cotejado la autorización expresa de la usuaria para este encargo y la correspondencia de los archivos con los recursos entregados. No es un dictamen jurídico, una certificación de exclusividad ni una garantía sobre eventuales derechos de terceros. El validador comprueba estructura, rutas y huellas; no decide cuestiones de titularidad.

## Autor y derechos

Los datos incorporados son los facilitados para el proyecto:

- Jesús Francisco Murciego Vidal.
- ORCID: `0009-0002-4434-959X`.
- Perfil ORCID: `https://orcid.org/0009-0002-4434-959X`.
- LinkedIn: `https://www.linkedin.com/in/jesusmurciego/`.

El pie muestra:

> © 2026 Jesús Francisco Murciego Vidal. Todos los derechos reservados.
>
> El autor se reserva el ejercicio de las acciones legales que correspondan frente al plagio, la reproducción no autorizada y la falsa atribución de autoría.

La página de detalle delimita esa reserva a los contenidos originales sobre los que el autor ostente derechos y mantiene los derechos de terceros. Los enlaces al ORCID y al DOI cumplen funciones distintas: identifican al investigador y a las publicaciones, respectivamente. Su inclusión no se presenta como prueba automática de titularidad de todos los materiales.

## DOI individual de cada mapa

`catalogo-mapas.js` contiene `window.DDD_MAPS = [];`. La interfaz muestra un estado vacío veraz. No hay un DOI general aplicado indiscriminadamente a los mapas, identificadores de demostración ni publicaciones simuladas.

La entrada CSV usa las columnas `id,nombre,territorio,nivel,version,fecha,sha256,doi`. Para incorporar publicaciones, completar el CSV con el identificador estable de cada mapa y los datos de su depósito real. Comprobar documentalmente que cada DOI corresponde al mapa, ámbito y versión indicados. El generador valida formatos y duplicidades; no resuelve por sí mismo los DOI ni acredita la correspondencia documental.

Desde la carpeta de la entrega:

```bash
python3 web/generar_catalogo.py web/plantilla_doi_por_mapa.csv
```

El comando escribe `web/catalogo-mapas.js`. El campo `sha256`, cuando se aporte, debe contener la huella del archivo concreto de la publicación. No debe confundirse con las huellas de las imágenes decorativas registradas en `assets-manifest.json`.

## Regenerar la presentación autónoma

Después de cualquier cambio en HTML, CSS, JavaScript, catálogo o recursos, ejecutar desde la carpeta de la entrega:

```bash
python3 generar_portada_autonoma.py --source web --output DDD_portada_autonoma.html
```

El generador requiere Python 3.10 o posterior y solo utiliza su biblioteca estándar. No modifica los originales. Incorpora las imágenes en URI de datos, genera plantillas inertes para las tres páginas y adapta sus enlaces. Rechaza recursos ausentes o externos para que una dependencia de imagen no pase inadvertida. La salida autónoma es una copia generada; las modificaciones deben hacerse en `web/` y regenerarse después.

`app.js` expone `window.DDDInit(root)`. El enrutador lo llama tras insertar la vista activa. El inicializador cancela los manejadores anteriores antes de registrar los nuevos, de modo que el menú y la búsqueda no acumulen eventos al recorrer la presentación.

## Comprobación y estado de entrega

Los tres WebP se han abierto para verificar formato y dimensiones; sus huellas SHA-256 están recogidas en el manifiesto. La revisión de recursos se ejecuta con el validador de la habilidad DDD en modo `--release`. Su ámbito es limitado: archivos existentes, metadatos declarados y correspondencia de huellas.

Los resultados de carga, navegación y adaptación en navegador se incorporan con las capturas finales y el informe de comprobación de la entrega. No se presupone que las verificaciones locales acrediten el funcionamiento del visor remoto ni el comportamiento de un alojamiento en el que todavía no se ha instalado este código.

**Estado:** implementación estática preparada para integrar. El catálogo de publicaciones está pendiente de recibir los DOI reales de cada mapa. La incorporación al repositorio y al alojamiento de producción corresponde al paso de integración de Jesús.

## Resultados observados el 19/11/2026

En Chrome se han comprobado las tres imágenes cargadas, tanto en la portada modular como en el HTML autónomo. La presentación autónoma contiene los tres WebP y no carga hojas CSS ni scripts separados. Se ha recorrido Inicio → Comprender → Auditoría y registro y se ha comprobado el regreso con el historial. El menú móvil abre y cierra con Escape.

Se han inspeccionado los anchos CSS de 320, 390, 768 y 1440 px, sin desbordamiento horizontal. La franja de autoría mide 83 px en la vista de escritorio. Las capturas de `vistas/` proceden de este código; el escalado y recorte de encuadre se describen en `COMPROBACIONES.json`. El catálogo mantiene su estado vacío y los enlaces de autor coinciden con los facilitados. Los enlaces locales y sus anclas existen; la sintaxis de `app.js` y el manifiesto de recursos superan sus comprobaciones.

Estas comprobaciones cubren la presentación entregada. El visor remoto, los perfiles externos y el comportamiento tras instalarla en producción quedan fuera de lo observado.
