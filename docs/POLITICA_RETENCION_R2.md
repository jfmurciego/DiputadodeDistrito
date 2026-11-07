# Política de retención de R2 (T-76)

Decisión del propietario (07-11): no pagar R2 sin motivo; capa gratuita de 10 GB. Techo operativo: **9 GB**.

1. **Qué se conserva por territorio**: el run vigente y solo su producto final: el estado M08 (con electoral) o, sin
   electoral, el de la etapa más avanzada (M06). Run vigente = el de `orchestracion/publicaciones_visor.json`
   (prioriza el `canonical_m08` y el run mayor) si está archivado; si no, el run archivado más avanzado y reciente.
   Si existe un run archivado más nuevo y al menos igual de completo que aún no se ha publicado, también se conserva
   (no se pierde un producto que solo está en R2).
2. **Acumulativos**: los zip `ddd-state-<run>-M0x` crecen de etapa en etapa (M08 ≥ M07 ≥ … ≥ M06 en todos los runs),
   así que se asume que cada uno contiene los anteriores. Si no lo fueran, se usa `--conservar-m06`
   (también en el workflow) y el archivo final sigue < 9 GB.
3. **Auditorías** (`ddd-audit-*`, < 1 MB): se conservan siempre. Las etapas M03U no se cuentan como producto.
4. **Herramienta**: `herramientas/podar_r2.py`. Simula por defecto, escribe la lista (`--salida`) con su sha256.
   El borrado real exige `--borrar --lista <fichero> --sha256 <huella>`; rechaza claves fuera del manifiesto o que la
   política actual conserve.
5. **Proceso**: la lista aprobada vive en `orchestracion/poda_r2_lista.json`. El propietario aprueba la lista y su huella;
   el Operador lanza `podar-r2.yml` con `borrar=true` y la huella; el job usa `environment: produccion` (clic del
   propietario) y retira lo borrado de `orchestracion/archivo_r2.json`. Si el manifiesto cambia antes, se regenera la lista.
6. **Límite**: `limite-r2.yml` falla cuando cambia el manifiesto y suma > 9 GB (aviso, no check obligatorio).
