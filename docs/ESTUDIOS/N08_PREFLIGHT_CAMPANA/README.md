# Preflight diagnóstico nacional M01–M06

**Versión:** 1.0.0 — candidato diagnóstico
**Fecha:** 2026-10-13
**Alcance:** ejecución provincial serial y checkpointed, sin generación ni certificación.
**Origen:** nuevo, sin predecesor.

`herramientas/preflight_campana_congreso.py` reutiliza el preflight provincial
`herramientas/preflight_caceres_n08.py`; no implementa otro motor M01–M06. El
runner provincial está fijado por SHA-256 y solo admite sus resultados M01–M04
diagnósticos, más comprobaciones sintéticas M05/M06. Cualquier cambio del
runner exige revisión explícita y actualizar el anclaje. La versión del informe
provincial también pertenece al contrato de cada runner fijado: el SHA
`1873a261e1b3a85c2ad34b74db2ab0fb61902663173e91aa262cc648093d1455` emite
informes `1.2.0`. Un runner nuevo requiere revisión explícita y una entrada
versionada de contrato; no se acepta una versión de informe arbitraria.

El runner recibe el manifiesto de transición N08 de forma explícita para
revalidar el contrato actual contra el producto topológico histórico. Su SHA
forma parte de la identidad del checkpoint. Los checkpoints provinciales
deben coincidir también en versión y SHA del runner, además de enlazar el hash
del informe.

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

La ejecución real de cobertura se conserva en el expediente de campaña cuando
se completa; el resultado sigue siendo diagnóstico y no certifica una
partición ni autoriza generación.
