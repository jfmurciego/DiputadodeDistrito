# T-458 · Diseño al detalle del mapa de la V4 (Explorar)

VERSIÓN: 1.3.0 · FECHA: 2026-11-25 · ESTADO: propuesta para aprobación del propietario
CAMBIOS 1.3.0: corrección de rumbo del propietario (25-11): nuestro mapa, sin copiar otra web; colores firmes como la capa de
  resultados; panel con los datos arriba; clic en distrito con ventana emergente y sin bajar a secciones. Fuera por ahora: nivel de
  sección, producto de votos por sección, fondo oscuro y paleta ajena. Preguntas reducidas a las imprescindibles.
CAMBIOS 1.2.0 y 1.1.0 (commits 8baaf19 y a0bb74c de esta PR): versión sobre la web de referencia y puntos 5-7; sustituidas.
MOTIVO: comentarios del propietario vía Coordinador.
ANTERIOR: 1.2.0 en el commit 8baaf19 de esta misma PR (documento sin fusionar; sin copia en `legacy/`)

Objeto: `visor/v4/mapa/` (`index.html` 1.3.0, `explorar.js`, `explorar.css`). Solo diseño; ningún cambio de código de producto
hasta que el propietario apruebe. Capturas: `antes_visor_actual.png` (nuestro visor servido en local) y las láminas de
`maqueta.html` (`colores.png`, `panel.png`, `distrito.png`; datos de ejemplo).

## 1. Mapa: mismo mapa, colores firmes y sin pérdida de nitidez

### Por qué la vista mayoritaria (doble vuelta) se ve en azul difuso
La capa «Partido más votado» (la vista de resultados) pinta con la `PALETA` de partidos (`PP #1d6fb8`, `PSOE #d32b2b`, …),
opacidad 0,88 y sin mezclas: es la referencia de firmeza. La doble vuelta no:
1. `bloques()` toma los tokens de `tokens-bloques.css`; con el sistema en tema oscuro son pasteles pensados para texto sobre
   fondo oscuro: Patriotas `#7fb2ff`, Izquierdas `#ff8a80`, Nacionalistas `#4fd1c5`, Sin bloque `#a8b0bb`.
2. `aclarar()` los mezcla un 55 % con blanco cuando la ventaja es < 5 puntos (Patriotas pasa a `#c5dcff`).
3. Encima, la opacidad 0,88 deja ver el fondo azulado `#eef3f7`.

### Nitidez: revisado
- **Geometría de distritos del mapa** (`datos/<territorio>/distritos.geojson`, `herramientas/generar_datos_abiertos.py`): sin
  simplificación ni redondeo. No pierde resolución.
- **Geometría pública de la doble vuelta** (`herramientas/publicar_doble_vuelta.py`): Douglas-Peucker por anillo, 0,0005°
  (≈ 55 m), 5 decimales. Hoy el mapa no la dibuja (pinta la de `datos/`); si algún día la usara, simplificar por anillo
  deja huecos y solapes entre distritos vecinos: no usarla para dibujar.
- **Pérdida real de nitidez: los colores**, no la geometría (los tres puntos de arriba). La opacidad 0,88 es la misma que en la
  capa de partidos y se mantiene igual en las dos.

### Propuesta
- Bloques con tonos firmes de la familia de la capa de partidos, fijos en tema claro y oscuro (el mapa no cambia de tema):

| Bloque | Hoy en tema oscuro | Propuesta |
|---|---|---|
| Izquierdas | `#ff8a80` | `#d32b2b` (el de PSOE en la capa de partidos) |
| Patriotas | `#7fb2ff` | `#1d6fb8` (el de PP) |
| Nacionalistas | `#4fd1c5` | `#0f7a52` (el de EH Bildu) |
| Sin bloque | `#a8b0bb` | `#5b6470` |

- Sin aclarado: la ventaja ajustada (< 5 puntos) se dice en la ventana emergente y en el panel, no con un color lavado.
- Opacidad y bordes iguales a la capa de partidos (0,88; blanco 0,8 px).

![Colores: antes y después](colores.png)

## 2. Panel derecho (prioritario)

Hoy, de arriba abajo: cabecera, «Conoce el territorio» (foto, descripción, autor, licencia, cambios, créditos), tarjetas 407/350 y,
al final, los datos.

Propuesta, de arriba abajo:
1. Cabecera: nivel y elección, nombre, ruta (España › Huesca › Distrito 2).
2. **Cuatro cifras de lo seleccionado** (ver tabla).
3. Bloque de resultados de ese nivel (lo que hoy está abajo: escaños por partido en la provincia; 1.ª y 2.ª vuelta en el distrito).
4. «Resultados en tabla» y «De dónde sale este mapa».

Fuera: foto, «Conoce el territorio», pie, licencia, créditos y «407 / 350». Sin foto la licencia no obliga a nada.

| Selección | Cuatro cifras |
|---|---|
| España | escaños 2023 (350), distritos DDD, bloques ganadores con la regla elegida, población |
| Provincia | escaños 2023, distritos DDD, bloques ganadores con la regla, población |
| Distrito | bloque ganador y vuelta decisiva, 2.ª vuelta (% – %), más votado en 1.ª vuelta, población y desviación |

Las cifras salen de lo que ya carga el visor (escaños oficiales, composición, CSV de doble vuelta); no hacen falta datos nuevos.

![Panel: antes y después](panel.png)

## 3. Clic en un distrito: ventana emergente, sin bajar a secciones

Hoy (`explorar.js`): el clic hace `focus()` hasta zoom 12; al terminar el zoom, `zoomend` (≥ 7,2, casilla «Detalle de secciones al
acercar») cambia solo a «Sección censal» y `prepareArea` oculta los distritos. No hay resaltado del distrito elegido.

Propuesta:
- Clic en un distrito: ventana emergente de MapLibre junto al punto con nombre, provincia, bloque ganador y vuelta, 2.ª vuelta,
  más votado en 1.ª vuelta, población y desviación; el panel se actualiza con la ficha completa del distrito.
- El mapa no se acerca al distrito ni cambia de nivel; el distrito elegido lleva borde grueso (resaltado con `feature-state`).
  Otro clic cambia la ventana y el resaltado; clic fuera o `Esc` la cierra.
- Se retiran el salto automático a secciones (`zoomend`), la casilla «Detalle de secciones al acercar» y las opciones
  «Municipio (secciones)» y «Sección censal» del selector de nivel.

![Clic en un distrito: antes y después](distrito.png)

## 4. Ficheros que tocaría la implementación
`visor/v4/mapa/index.html`, `explorar.js`, `explorar.css` y `visor/v4/tokens-bloques.css` (o tokens propios del mapa). Sin
herramientas, workflows ni datos nuevos. Cada fichero sube VERSIÓN con copia en `legacy/`.

## 5. Preguntas

1. **Colores de los bloques:** `#d32b2b`, `#1d6fb8`, `#0f7a52`, `#5b6470`, fijos en los dos temas. Recomendación: sí.
2. **Ventaja ajustada (< 5 puntos):** ¿sin color propio (solo en texto) o con un tono algo más claro? Recomendación: solo en texto.
3. **Cuatro cifras del panel** según la tabla del §2. Recomendación: sí.
4. **Nivel de sección:** ¿se retira del selector y del zoom (no solo del clic)? Recomendación: sí, hasta que exista el producto
   por sección.
