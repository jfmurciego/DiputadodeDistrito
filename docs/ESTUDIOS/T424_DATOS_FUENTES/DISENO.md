# T-424 · «Datos» y «Fuentes» en la V4 — diseño (solo documento)

VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ESTADO: propuesta, a la espera del propietario · ANTERIOR: ninguna (fichero nuevo)

No toca `visor/`, workflows ni datos. Nada se implementa hasta que el propietario apruebe este detalle (CLAUDE.md, 16-11).

## 1. Qué había en la V3 y por qué no servía

La V3 enlazaba `docs/datos-abiertos.html` y `docs/fuentes.html` desde su menú (`visor/v3/index.html:18`). Su texto sobrevive en
`legacy/documentacion_publica/docs/datos-abiertos_pre_t423_20261119.md`. Problemas comprobados:

| Defecto | Dónde se ve |
|---|---|
| Jerga y códigos internos: «producto territorial M06», `blob_sha`, «run de origen», `sha256sum`, «CRS84» | datos-abiertos_pre_t423 |
| Lista de ficheros sin decir qué es cada uno ni qué hacer con él (GeoJSON, CSV) | ídem |
| «Verificación» = una línea («el `sha256sum` debe coincidir») sin explicar qué es ni cómo se hace en Windows/Mac/móvil | ídem |
| No dice que solo consta el ganador por distrito (ni votos por partido) salvo en una viñeta; nada de la doble vuelta | ídem + `datos_abiertos/README.md` |
| Fuentes: solo una frase («INE, Interior, BOE conservan sus condiciones»); sin fecha, sin enlace, sin qué se hizo | ídem |
| Documentación técnica (R2, runs, huellas) mezclada con la pública | `archivo-r2_pre_t423` |
| Enlaces al menú ya rotos tras T-423 (D-181 los sacó del menú) | `index_v1.1.0_20261119` |

Conclusión: escritas para quien mantiene el proyecto, no para quien lo visita. La V4 las rehace desde cero con el tono de Comprender y «Cómo se hace este mapa».

## 2. Inventario real (nada de memoria)

**Paquete descargable** (`datos_abiertos/INDEX.json`, esquema `ddd.datos-abiertos/1.1`, generado por `herramientas/generar_datos_abiertos.py` en P40):
- 52 provincias (`nac01`…`nac52`), **407 distritos** (suma de `n_distritos` de las 52 entradas de `INDEX.json`; nac22 = Huesca, comprobado ahí), elecciones generales 2023 (Congreso).
- Por provincia: `distritos.geojson` (límites), `resultados.csv` (columnas `distrito, poblacion, votos_totales, ganador, votos_ganador, porcentaje_ganador`; **solo el ganador**), `distrito-<n>.html` (ficha), y sha256 de cada uno en `INDEX.json`.
- Licencia: **CC BY 4.0**, atribución «Diputado de Distrito (https://github.com/jfmurciego/DiputadodeDistrito)»; las fuentes oficiales mantienen sus condiciones.
- Los GeoJSON no se versionan en git; el publicador los reconstruye verificando sha256 (CLAUDE.md, «Los 49 GeoJSON M06»). Hay que confirmar qué queda realmente servido en `/datos/` (pregunta 1).

**Doble vuelta**: `configuracion/doble_vuelta_publicada.json` (elección 2023-07, informe con sha256) y datos en `mapa/datos/` con su `INDEX.json` (p40-publicacion.yml). No están en `datos_abiertos/` ni tienen licencia declarada (pregunta 2).

**Fuentes** (de `configuracion/` y `fuentes/`):

| Fuente | Qué se usa | Dónde consta |
|---|---|---|
| INE | Secciones censales (límites, colección anual 2010-2026, API OGC `www.ine.es/geoserver/ogc/features/v1/`); población por sexo y edad (tabla 65034); códigos territoriales (descargados el 10-11-2026, `fuentes/ine_codigos_territoriales_2026-11-10/SHA256SUMS`) | `fuentes/catalogo_oficial.yaml` 1.2.0, `orchestracion/fuentes_r2.json` |
| Ministerio del Interior (Infoelectoral) | Resultados por mesa de las generales (p. ej. 23-07-2023: `02202307_MESA.zip`, sha256 y bytes en el contrato; según el contrato, cuadra con la Resolución de la JEC de 30-08-2023 menos el CERA: por verificar por esta tarea) | `configuracion/contratos_infoelectoral.yaml` 1.2.3 |
| BOE | Escaños y resultados oficiales de la Junta Electoral Central: 2011-11 (BOE-A-2011-19391, 10-12-2011), 2015-12 (BOE-A-2016-867), 2016-06 (BOE-A-2016-7133), 2019-04 (BOE-A-2019-8070), 2019-11 (BOE-A-2019-18147, corrección) y 2023 (BOE-A-2023-18907) | `configuracion/identificadores_boe_resultados_congreso.json`, `resultados_oficiales_congreso_*.json` |
| Portales autonómicos | 17 comunidades, 79 elecciones autonómicas 2008-2026 (calendario): Junta de Andalucía (SIEL), Aragón Open Data, SADEI (Asturias), IBESTAT, Parlamento de Canarias, Castilla y León, Castilla-La Mancha, Generalitat de Catalunya, Generalitat Valenciana, Xunta de Galicia, Comunidad de Madrid, CREM (Murcia), Navarra, Gobierno Vasco, La Rioja, Junta Electoral de Extremadura. Cantabria sin URL. | `configuracion/calendario_autonomicas.csv` |

Nota de honradez: en el calendario autonómico la columna `fuente_calendario` es el Observatorio Electoral de las Naciones (Euskadi), un tercero; la página debe decir que el calendario se contrastó con él, no que sea fuente oficial. Y que parte de lo autonómico aún no se muestra en el mapa (T-421, autonómicas sin datos): la página no promete lo que Explorar no enseña.

La fecha por fuente sale de ficheros con sha256 (fecha de descarga o de publicación en BOE). Las que no tengan fecha en el repositorio se mostrarán sin fecha, nunca inventada.

## 3. Estructura propuesta

Ficheros nuevos (futuros, tras aprobar): `visor/v4/datos.html` y `visor/v4/fuentes.html`, con la cabecera única (`cabecera.html`, menú: Inicio · Comprender · Explorar · **Datos · Fuentes** · Metodología) y el pie único; estilos de `styles.css`. La portada gana dos cajas `route` junto a Comprender y Explorar. Sin JavaScript propio salvo, quizá, la calculadora de huella (pregunta 4).

**Datos** (de arriba abajo):
1. Qué puedes descargar (tarjetas: «Distritos de cada provincia», «Quién gana en cada distrito», «Doble vuelta»).
2. Cómo se abren: un mapa en GeoJSON (se abre en QGIS o geojson.io), una tabla en CSV (Excel, Calc), una ficha en página web. Una frase por formato.
3. Cómo comprobar que no ha cambiado («huella digital»): 3 pasos con ejemplo de una provincia; la huella de `INDEX.json` es el «DNI» del fichero.
4. Licencia en dos líneas: la de DDD es CC BY 4.0 (consta en `INDEX.json`); lo oficial conserva sus condiciones. «También con fines comerciales» y las condiciones de INE, Interior y BOE: **por verificar** antes de afirmarlo.
5. Lo que NO hay: votos por partido en cada distrito; secciones censales.

**Fuentes** (por fuente): quién es, qué dato, fecha, enlace oficial, y «qué hicimos» en una frase (p. ej. «sumamos las secciones censales hasta formar distritos»; «no cambiamos ni un voto»). Al final, «cómo se comprobó» (cuadre con el BOE) en una línea.

Reglas de lenguaje: sin «M0x», `run`, `blob`, `sha256` suelto (se dice «huella digital»), `P40`, `CRS`; test que lo vigile igual que en Comprender (D-181). Topónimos en español.

Generación: las cifras (52, 407) y la tabla de fuentes se leerán de `INDEX.json`, `catalogo_oficial.yaml` y `identificadores_boe…json` con un generador + test de coherencia, no a mano (regla de datos oficiales). Esto añade una herramienta; por eso se pregunta (pregunta 5).

## 4. Maquetas (HTML estático, esquemáticas)

### 4.1 Caja en la portada

```html
<a class="route" href="datos.html"><span class="route-ico" aria-hidden="true">⬇</span>
  <span><h2>DATOS</h2><p>Descarga los distritos y los resultados, y comprueba que son los originales.</p></span></a>
<a class="route" href="fuentes.html"><span class="route-ico" aria-hidden="true">🔗</span>
  <span><h2>FUENTES</h2><p>De dónde sale cada dato: INE, Interior, BOE y portales autonómicos.</p></span></a>
```

### 4.2 Página «Datos»

```html
<main class="wrap"><h1>Datos</h1>
<p>Todo lo que ves en el mapa lo puedes descargar, usar y compartir.</p>
<section><h2>Qué puedes descargar</h2>
 <article class="card"><h3>Distritos de cada provincia</h3>
  <p>El dibujo de los 407 distritos. Formato GeoJSON: se abre en programas de mapas gratuitos (QGIS, geojson.io).</p>
  <a href="datos/nac22/distritos.geojson">Ejemplo: Huesca</a> · <a href="datos/">Las 52 provincias</a></article>
 <article class="card"><h3>Quién gana en cada distrito</h3>
  <p>Una tabla (CSV, se abre con Excel): población, votos y ganador de las generales de 2023. Solo el ganador, no todos los partidos.</p></article>
 <article class="card"><h3>Doble vuelta</h3><p>El resultado simulado con tres bloques…</p></article></section>
<section><h2>Comprueba que no ha cambiado</h2>
 <ol><li>Descarga el fichero y el índice <code>INDEX.json</code>.</li>
     <li>Calcula su huella digital (una cadena de 64 letras y números): <a href="#">cómo, en Windows, Mac o móvil</a>.</li>
     <li>Si coincide con la del índice, es exactamente el mismo fichero. Si cambia una coma, la huella cambia entera.</li></ol></section>
<section><h2>Licencia</h2><p>CC BY 4.0 (datos de DDD): úsalo citando «Diputado de Distrito». <!-- por verificar: usos comerciales y condiciones de INE/Interior/BOE --></p></section></main>
```

### 4.3 Página «Fuentes»

```html
<main class="wrap"><h1>Fuentes</h1>
<p>Estos son los datos en los que nos basamos, de dónde salen y qué hicimos con ellos. <!-- por verificar: «solo oficiales», el calendario autonómico cita un tercero --></p>
<table><thead><tr><th>Quién</th><th>Qué dato</th><th>Fecha</th><th>Qué hicimos</th></tr></thead><tbody>
<tr><td><a href="https://www.ine.es">INE</a></td><td>Secciones censales y población</td><td>2026 (colección anual)</td><td>Agrupamos secciones en distritos de población parecida.</td></tr>
<tr><td><a href="https://infoelectoral.interior.gob.es">Ministerio del Interior</a></td><td>Votos por mesa, 23-07-2023</td><td>23-07-2023</td><td>Sumamos los votos de cada distrito. <!-- «sin cambiar ninguno»: por verificar con el cuadre de totales --></td></tr>
<tr><td><a href="https://www.boe.es/diario_boe/xml.php?id=BOE-A-2023-18907">BOE</a></td><td>Escaños oficiales 2023</td><td>BOE-A-2023-18907</td><td>Comprobamos que nuestros totales cuadran con los oficiales.</td></tr>
<tr><td>Portales autonómicos (17 comunidades)</td><td>Autonómicas 2008-2026</td><td>según comunidad</td><td>Enlace a cada portal en la lista de abajo.</td></tr>
</tbody></table></main>
```

## 5. Preguntas abiertas (para el propietario)

1. **¿Dónde se descarga?** Recomiendo enlaces directos a `/datos/` (por verificar que estén servidos hoy) y un único ZIP por provincia solo si lo pides. No he podido ver desde aquí qué hay servido: por verificar antes de implementar.
2. **Doble vuelta: ¿se ofrece y con qué licencia?** Recomiendo sí, mismo CC BY 4.0, añadiendo la tabla al paquete `datos_abiertos/` (cambio de `generar_datos_abiertos.py`, tarea aparte). Si no, la tarjeta se retira y se dice «próximamente»… o simplemente no se pone (prefiero lo segundo).
3. **¿Autonómicas en «Fuentes»?** Recomiendo listarlas solo para las comunidades que Explorar ya muestre, para no prometer datos que no hay (T-421); el resto, una línea general.
4. **¿Herramienta de huella en la página?** Recomiendo solo instrucciones (3 pasos, Windows/Mac), sin JavaScript: menos mantenimiento y sin cargar ficheros pesados.
5. **¿Generador + test para cifras y tabla?** Recomiendo sí (evita cifras a mano y mantiene coherencia con `INDEX.json`); alternativa: texto fijo con test que compare las cifras clave.
6. **Orden del menú:** Inicio · Comprender · Explorar · Datos · Fuentes · Metodología (recomendado). Metodología queda al final como «cómo se hace».
7. **Enlaces oficiales:** ¿pongo enlace a cada ficha del BOE y del portal, o solo a la portada de cada organismo? Recomiendo ficha exacta (verificable), comprobando que responde antes de publicar.
8. **Tiempo de las fechas:** ¿«fecha» = de publicación oficial o de nuestra descarga? Recomiendo ambas cuando existan (columnas separadas).

9. **DECISIÓN 9 — ¿Apruebas este detalle para implementarlo?** Recomiendo sí, con las respuestas 1-8 incorporadas. Sin tu «sí» no se implementa nada.

## 6. Tamaño y siguiente paso

Implementación estimada (tras aprobar): 2 HTML + 2 cajas en portada + menú único (`cabecera.html` y copias) + tests de jerga y de menú; sin tocar motor, workflows ni datos. Una PR. Efectos de huellas: ninguno; la publicación de la V4 la lanza el Operador con permiso.
