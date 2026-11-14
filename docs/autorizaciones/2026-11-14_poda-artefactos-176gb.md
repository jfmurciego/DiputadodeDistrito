# Autorización: poda de artefactos de Actions (T-278)

- Frase literal del propietario (chat del Operador, 2026-11-14): «Autorizo borrar los artefactos marcados BORRAR en la propuesta del 14-11 (176 GB)»
- Alcance: las 2.202 filas BORRAR de `poda_artefactos_2026-11-14/propuesta.tsv` (176,24 GB). Nada más.
- Recálculo previo: `publicaciones_visor.json`, `archivo_r2.json` y el catálogo sin cambios desde el 12-11; ningún paquete BORRAR en el catálogo vigente.
- Ejecución: `DELETE repos/<r>/actions/artifacts/<id>`, uno a uno; resultado por id en `poda_artefactos_2026-11-14/resultado_borrado.tsv`.
- Parada: primer error distinto de 204/404.
