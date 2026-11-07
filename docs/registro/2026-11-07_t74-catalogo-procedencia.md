## 2026-11-07 — T-74 — Catálogo de procedencia único

- Causa: la procedencia de cada producto estaba repartida en cinco registros (visor, archivo R2, datos abiertos,
  productos públicos y catálogos de fuentes/preparación) sin un índice común.
- Cambio: `herramientas/catalogo_procedencia.py` (1.0.0) genera `orchestracion/catalogo_procedencia.json`, derivado y
  en solo lectura de esos registros (más los MANIFEST de `datos/composicion` y `datos/resultados` y el DOI de
  `configuracion/publicaciones.yaml`): por territorio, fuente territorial y electoral, y cada producto (M06, M08,
  estático, ensemble, composición, resultados, datos abiertos) con sha256, run, blob git, copias R2, publicación y DOI.
  Las incoherencias se listan en el catálogo (ERROR: publicado sin sha256 o sin copia; AVISO: el resto). No se
  migran los escritores ni cambian los formatos.
- Check: `tests/test_catalogo_procedencia.py` (suite `pruebas`): catálogo versionado = regenerado y 0 errores.
- Informe actual: 66 territorios, 288 productos, 0 errores, 113 avisos: 51 M06 y 51 M08 vigentes solo con copia git
  (sin `ddd-state-<run>-M0x` en R2) y 11 artefactos R2 de `illes_balears` sin producto en el visor.
- Pruebas: test sintético (completo, ERROR por sha256 ausente, desfase detectado, determinismo), guardián y
  cabeceras de gobernanza.
- Workflow nuevo `catalogo-procedencia.yml` 1.0.0 (solo push a `main`, sin botón): cuando cambia cualquiera de las
  entradas, regenera el catálogo y lo empuja con la app de registro (credencial tras el checkout, `queue: max`). Cubre a
  todos los escritores (visor, archivista R2, resultados, composición, preparación) sin tocarlos.
- Riesgo: el run de `pruebas` del commit del robot que cambia una entrada sale rojo hasta que entra el commit de
  regeneración (segundos después), que deja `main` en verde.
