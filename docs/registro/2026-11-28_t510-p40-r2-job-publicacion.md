## 2026-11-28 — T-510 — P40: la subida a R2 de la web, en un job con el entorno `publicacion` (solución B)

- Causa: en P40 1.7.0 los pasos «Datos de la web en R2 (T-430)» y «Web en R2 (T-430)» iban dentro del job de Pages (`publicar`, entorno
  `github-pages`, D-162). El propietario puso R2_WEB_*, R2_SITIO_*, R2_WEB_BUCKET y R2_SITIO_BUCKET en el entorno `publicacion`, así que no
  llegaban: run 45900288067, «[datos_web] sin R2_WEB_BUCKET: no se sube nada» y «[sitio_r2] sin R2_SITIO_BUCKET: no se sube nada», 0 objetos.
- Cambio (P40 1.8.0, copia de la 1.7.0 en `legacy/workflows/p40-publicacion_v1.7.0_20261127.yml`): job nuevo `subir_r2` con
  `environment: publicacion`, `needs: [preparar, publicar]`, solo desde main y solo si `publicar` persistió el registro tras el despliegue
  (salida `registro_persistido`, paso con `id: persistir`). Recibe el artefacto `github-pages-<intento>` que ya subió `publicar` (salida
  `artefacto_pages`; es lo que sirve Pages) y lo desempaqueta, sin reconstruir nada; luego los dos pasos de R2, con sus secretos en el env del
  paso. Concurrencia propia `ddd-r2-web-prod` (en cola, sin cancelar). Un fallo no toca Pages: pasos con `continue-on-error` y un paso final
  «Resumen de la subida a R2 (T-510)» que da `::error::R2_SUBIDA_FALLIDA` (o `::warning::R2_SIN_BUCKET`) en el log y en el resumen del run.
  El job de Pages (entorno, `ddd-pages-prod`, deploy-pages, registro y promoción a `mapas/`) no cambia de comportamiento.
- Pruebas: `tests/test_t510_p40_r2_publicacion.py` (todo paso con secrets/vars R2_WEB_*/R2_SITIO_* en un job con `publicacion`; secretos R2 en
  el env del paso; deshecho T-510 con `tests/_t510.py`, P40 igual a la 1.7.0 congelada con sha256; resumen y desempaquetado ejecutados bajo
  `bash -eo pipefail`; controles negativos). Ajustados sin debilitar: test_t372, test_t377, test_t379_2a (`subir_r2` admitido sin app ni push),
  test_t430_datos_web y test_t430_sitio_r2 (los pasos, en `subir_r2`).
- Riesgos: R2 recibe ahora exactamente el tar de Pages (sin ficheros ocultos, que Pages tampoco sirve). Si `publicacion` tiene revisores o
  limita ramas, el job esperará o fallará sin tocar Pages. P90 `publicar_web` usa R2_SITIO_* sin entorno: mismo problema, fuera de esta tarea.
