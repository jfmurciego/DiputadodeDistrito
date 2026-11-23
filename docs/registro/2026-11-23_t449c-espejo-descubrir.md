## 2026-11-23 — T-449 — Espejo oficial: descubrir en solo lectura dónde está ahora el fichero de la Junta

- Causa: el espejo de aut08 volvió a salir rechazado (run 45170670366, main@5d2211e). Las dos distribuciones de datos.gob.es
  (`Resultados_CLM_2023.xlsx` y `.csv` en `datosabiertos.castillalamancha.es/sites/…/files/`) hacen 301 a `/system/404`: el portal de la
  Junta cambió de plataforma. Ni la nube ni el propio catálogo dan la URL nueva, y no se adivina.
- Cambio:
  - `herramientas/espejo_fuente_oficial.py` 1.2.0: nuevo modo `descubrir`, de solo lectura y sin secretos.
    - Sondea las páginas declaradas: portal nuevo, API CKAN si la hay, catálogo del publicador en datos.gob.es y web de elecciones.
    - Anota cada redirección y solo sigue las https dentro de los sufijos `castillalamancha.es` y `datos.gob.es`.
    - Extrae los enlaces a ficheros de datos que citan el año o las autonómicas, incluidos los escapados en JSON.
    - Mide como mucho 10: estado, URL final, bytes, sha256 y si es HTML.
    - Escribe `descubrimiento.json` e imprime `ESPEJO_DESCUBRIR`. No sube nada.
  - `configuracion/espejos_fuentes_oficiales.json` 1.2.0: `descubrir` en aut08, con semillas de elecciones2023.castillalamancha.es (descargas por municipio, sitemap) y de las fichas del portal nuevo; ese host, también en `hosts_permitidos`.
  - P10 1.0.5: en `p13_espejo`, el paso «Buscar la fuente en los portales (solo lectura)» corre solo si falla «Bajar y medir». No lleva
    secretos y deja una tabla de candidatas en el resumen. El job sigue en rojo.
- Ampliación (propietario 23-11, vía Planificador: «probar todos los sitios»):
  - `espejar` busca en la Wayback Machine (API CDX) una copia archivada de cada URL oficial cuando ninguna candidata del catálogo es un fichero,
    y lo mismo para el PDF de verificación. Baja la copia íntegra (`id_`), exige que su SHA-1 en base32 sea el `digest` de la captura y la
    declara en el manifiesto con `oficial: false`, `tipo: copia_archivada`, `origen`, `url_original` y `captura`. Si la captura no trae
    digest, falla cerrado.
  - La subida de la copia queda detrás de `copias_archivadas_destino`, a la espera de la decisión del propietario:
    - `no_subir`, por defecto: se mide y no se sube;
    - `fuentes-archivadas`: todo el conjunto va a esa raíz;
    - `fuentes`: la mezclaría con los originales de D-198.
    `subir` rechaza un manifiesto que dé por oficial una copia.
  - `descubrir` lee respuestas CDX (prefijos del portal antiguo y del sitio de elecciones) y sondea medios (Público, elDiario.es, El Español,
    RTVE, CMM, El País). Los medios se marcan NO oficiales, guardan la huella y las filas de tabla de cada página, y nunca se suben solos.
  - Orden de las semillas: Wayback, elecciones2023, portal nuevo, otras oficiales y medios. Topes de `descubrir`: 40 páginas y 10 candidatas.
  - El cuadre con los totales del PDF oficial no se automatiza en el runner (formato de los ficheros desconocido): va con test en la PR que
    fija la fuente en el calendario, antes de usarla.
- La URL buena entra después por PR, en el modo URL directa de T-448, con `sha256_esperado` y `bytes_esperados` medidos en el log.
  Si no aparece ningún fichero oficial, queda el último recurso autorizado: un medio, declarado fuente NO oficial y cuadrado con los totales
  oficiales.
- Pruebas: `tests/test_t449_espejo_fuente_oficial.py` 1.0.2 con portal simulado:
  - saltos 301→404 anotados;
  - enlace fuera de los sufijos que ni se pide;
  - portada HTML detectada tras un 302;
  - fichero bueno medido;
  - enlaces escapados en JSON;
  - sufijo exacto;
  - paso del job sin secretos y condicionado al fallo.
  Vistas de P10 regeneradas.
