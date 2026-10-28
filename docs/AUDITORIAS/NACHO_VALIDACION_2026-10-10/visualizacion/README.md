# Validación3: selección y visualización

Versión1.0.0; fecha2026-10-10; alcance: investigación aislada en `/private/tmp/ddd-nacho-validacion3-20261010/`. Baseline DDD `42163cd8cebd120db9ab9fd1329c32ccdd87cf36`, rama `codex/distritos-autonomicos`. Aplicadas skills `ddd-implementador` y `ddd-economia`. Ningún cambio productivo, oficial, contractual, A2/A3 o Nacional. Sin commits/push/PR/workflows/territorios/publicación/red/instalaciones.

Se reutilizan exactamente los candidatos A/B/C de `docs/AUDITORIAS/NACHO_2026-10-10/experimentos/results.json`, matriz/assignments congelados y sus hashes; no se repiten benchmarks de ranking/generación. `provenance.json` registra SHA de fuentes y configuración exacta. Los report originales se copian a `copied_reports/` y se enriquecen con assets, campos de visualización/elongación/comarcas divididas y ledger diagnóstico; **no se altera ningún objetivo**, hard gate o assignment. Las dos alternativas siguen siendo las existentes, y C conserva sus incumplimientos.

## Reproducir

```sh
/private/tmp/madrid-gerrychain-venv/bin/python /private/tmp/ddd-nacho-validacion3-20261010/validate.py
/private/tmp/madrid-gerrychain-venv/bin/python /private/tmp/ddd-nacho-validacion3-20261010/run_js.py
```

`validate.py` ejecuta `assemble` y `build_gallery` reales, conserva las fuentes y genera diagnóstico/assets/copias. La versión final conserva el bloqueo documentado del primer intento Chrome y no reintenta arrancarlo. Python mide≈44MiB RSS y finaliza<1s. `run_js.py` ejecuta el `app.js` real producido en JavaScriptCore instalado, con DOM y MapLibre simulados; timeout60s, CPU55s y límite DATA640MiB. Sólo intercepta la llamada final `load()` para capturar su Promise; las funciones de la galería mantienen su código exacto. El motor JS no accede a red y sólo lee los assets locales. `js_execution.json` acredita tiempo/RSS del subprocess.

Artefactos principales: `diagnostico.html` (abrir directamente, SVG inline), `comparison.csv`, `ESPECIFICACION.md`, `validation_results.json`, `dom_simulation_results.json`, `provenance.json`, `source_unchanged.json`, `gallery/` original generado, `assets_metric/` y `assets_web/`. El `index.html` de la galería original todavía referencia CDN MapLibre; no se cargó la dependencia externa. No hay captura/render real de navegador. El diagnóstico HTML funciona sin CDN.

CRS: plano original sintético cartesiano0–4 para cálculo; embedding ilustrativo de1metre por unidad, anclado explícitamente en lon−3,7/lat40,4 en EPSG3857 y transformado a4326 para GeoJSON web. Este punto no identifica una fuente, sección o resultado real de Madrid. La geometría web no participa en métricas ni certificación. El original `LOCAL:CARTESIAN_FIXTURE` se conserva como metadata local, no CRS EPSG ficticio.

Conclusión: **MEJORA_DEMOSTRADA exclusivamente de información diagnóstica** (tablas/límites/causas/explicación/procedencia). La selección/Pareto DDD ya funcionan y permanecen idénticos. No se ha demostrado mejora algorítmica, render WebGL, usabilidad ni beneficio territorial. C no tiene opción de selección o asset promocionable en la galería; su tabla de rechazo es evidencia diagnóstica.

`manifest.json` cubre SHA256 de scripts, resultados, copias y assets. `source_unchanged.json` comprueba mismos hashes antes/después de archivos fuente acreditados, galerías/motor e informes previos. Estado del worktree preservado; revisión independiente pendiente.
