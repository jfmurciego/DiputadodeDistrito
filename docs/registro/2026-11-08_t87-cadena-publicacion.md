## 2026-11-08 — T-87 — Cadena de publicación con un solo lanzamiento (D-14)

- Causa: publicar una 00 exigía dos lanzamientos (05 del visor y `publicar-version-mapa.yml`) con datos copiados a mano, y
  la 05 sobre una 00 «Reutilizar» fallaba con `EJECUCION_SOLICITADA_SIN_EVIDENCIA_GENERADA` (T-95 solo nombra el origen).
- Cambio: workflow nuevo `cadena-publicacion.yml` («05 Cadena de Publicación», manual, `modo=simulacion` por defecto). Su job
  `resolver` lee el registro durable de la 00 (`herramientas/resolver_cadena_publicacion.py` 1.0.0): exige 00 SUCCESS y
  puertas 02 y 04 validadas, toma como run a publicar el que generó el M08 (el origen si fue «Reutilizar»), comprueba que
  M08 y M06 no han caducado y que la Release no existe. Con `modo=publicar` llama a la vez a la 05 (3.3.0, entrada
  `source_sha` que debe ser ancestro de `main`) y a `publicar-version-mapa.yml` (1.1.0, ahora también `workflow_call`;
  checkout, LINAJE y Release sobre ese sha), con el mismo run y el mismo sha. No publica sin el lanzamiento del Operador.
- Pruebas: `tests/test_resolver_cadena_publicacion.py` (registros reales de Huesca 42421655965 → 41194447427 y Álava
  41346917857), diseño A, codauto, concurrencia, seguridad y gobernanza en local.
- Riesgo: `publicar-version-mapa` conserva `environment: publicacion`; si tiene revisor, la cadena espera ese clic
  (quitarlo es decisión del propietario).
