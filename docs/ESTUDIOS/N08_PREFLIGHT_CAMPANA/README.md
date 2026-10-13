# Preflight diagnóstico nacional M01–M06

**Versión:** 1.0.0 — candidato diagnóstico
**Fecha:** 2026-10-13
**Alcance:** ejecución provincial serial y checkpointed, sin generación ni certificación.
**Origen:** nuevo, sin predecesor.

`herramientas/preflight_campana_congreso.py` reutiliza el preflight provincial
`herramientas/preflight_caceres_n08.py`; no implementa otro motor M01–M06. El
runner provincial está fijado por SHA-256 y solo admite sus resultados M01–M04
diagnósticos, más comprobaciones sintéticas M05/M06. Cualquier cambio del
runner exige revisión explícita y actualizar el anclaje.

La campaña procesa en orden CPRO `01`–`52`. Guarda cada informe provincial y
checkpoint, más `CHECKPOINT.json` y `CAMPAIGN_PREFLIGHT.json`. Un checkpoint se
reanuda únicamente si coinciden HEAD, contrato, fuentes, manifiesto topológico,
unidades, runner, consumidores M01–M06 y código de campaña. La evidencia ya registrada se vuelve a
verificar por hash. Los fallos quedan registrados y no se repiten al reanudar;
`--retry-failed` habilita un reintento explícito después de cambiar una
condición ambiental.

Primera ejecución:

```sh
python herramientas/preflight_campana_congreso.py \
  --parts-dir inputs/partes \
  --output docs/ESTUDIOS/N08_PREFLIGHT_CAMPANA/run-01
```

Reanudación:

```sh
python herramientas/preflight_campana_congreso.py \
  --parts-dir inputs/partes \
  --output docs/ESTUDIOS/N08_PREFLIGHT_CAMPANA/run-01 \
  --resume
```

Un `DIAGNOSTIC_COVERAGE_COMPLETE` significa que se registraron los 52
diagnósticos; no implica factibilidad, partición construida, certificación ni
autorización. Los informes provinciales conservan sus estados `BLOCKED` y
`SYNTHETIC_CONTRACT_PASS_ONLY`. Todos los artefactos mantienen
`generation_authorized=false`, `real_partition_created=false`,
`districts_generated=0` y `published=false`.

No se ejecutó la campaña de 52 provincias como parte de esta implementación;
las pruebas usan runners y reportes sintéticos.
