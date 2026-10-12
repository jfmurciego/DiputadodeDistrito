# Contrato aditivo de fuente territorial independiente F10

Versión 1.0.0 — 2026-10-12; estado: candidato.

## Alcance

El registro `independent_source_evidence` permite que el consumidor #179 valide un
receipt territorial nuevo sin reemplazar `preparation_evidence`, que puede seguir
respaldando un producto histórico. El campo acepta el receipt `ddd.territorial-source-receipt/1.0`
y los mismos fingerprints que exige el contrato vigente.

La admisión requiere exactamente:

- `status: AUTHENTIC_EVIDENCE_ONLY_HISTORICAL_PRODUCT_LINEAGE_PRESERVED`;
- `promoted: false`;
- una ruta `receipt_path` versionada;
- identidad territorial, edición, años, run, artifact, hashes de paquete, reporte e
  identidad que coincidan con el receipt.

El consumidor falla cerrado si el campo está malformado, promovido o sin clasificar.
Cuando no existe, sigue consumiendo el receipt histórico de `preparation_evidence`.

## Límites del contrato

La lectura de este receipt no promueve ni modifica `territorial_product`,
`last_valid_checkpoint`, el source run histórico o su producto certificado. No autoriza
la sustitución ni ejecución productiva. La admisibilidad de temporalidad, cobertura,
población y geometría se comprueba por las puertas propias del territorio; la presencia
del receipt por sí sola no es un PASS F10.

## Trazabilidad de implementación

Predecesor funcional conservado:
`legacy/herramientas/consumir_par_fuentes_legislatura_v1.0.1_pre_independent_receipt_20261012.py`.
La regresión automatizada positiva y negativa está en
`tests/test_independent_source_receipt.py`.
