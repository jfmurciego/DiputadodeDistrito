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
  - `configuracion/espejos_fuentes_oficiales.json` 1.2.0: `descubrir` en aut08.
  - P10 1.0.5: en `p13_espejo`, el paso «Buscar la fuente en los portales (solo lectura)» corre solo si falla «Bajar y medir». No lleva
    secretos y deja una tabla de candidatas en el resumen. El job sigue en rojo.
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
