# F05–F08 — referencias reproducibles

Versión1.0.0; fecha2026-10-10; estado candidato para revisión. Origen: commit0e09de5f8db6e739f7bd3e00e26fffd865440a59, árbol835f5b09c077c638b991da714faece6f83304310. Sin predecesor documental.

Único cambio funcional:47 referencias activas en acreditar_identidades.py(1), verificar_offline.py(2), identity-alignment.json(2), offline-results.json(14), matriz-19-final.json(28) pasan a continuacion/evidencia-previa-reutilizada.json. JSON original no rastreado y copia versionada idénticos byte a byte y semánticamente; SHA25608ee87ca4e904075d3b229964b61a184ab64a63d83bae7b879383fb39651dac6.

Scripts y documentos incrementan sólo PATCH; predecesores conservados en legacy/docs/AUDITORIAS/F04_F10_20261009/continuacion/. Resultados,19 identidades/ediciones,14 históricos,5 bloqueos canónicos, criterios y dependencias permanecen iguales. Los cuatro REVIEW_PASS emitidos por sesión separada sobre0e09de5f se conservan como dictámenes históricos: esta subsanación requiere nueva revisión y no hereda aprobación automática.

Referencias al JSON original en logs, diffs gzip y predecesores se conservan como historial inmutable; no son dependencias activas. MANIFEST-final.json anterior describe el árbol certificado original; el manifiesto de subsanación complementa esa instantánea con hashes nuevos sin reescribir la evidencia anterior.

Regresión dirigida test_referencias.py:checkout limpio sin JSON no rastreado; ejecución real del script de metadatos F06 y del segmento de agregación histórica F07, excluyendo consumidores/pruebas iniciales ya acreditadas; equivalencia exacta de salidas y semántica anterior salvo ruta/versión; estadoGit limpio tras las pruebas. Sin adquisición, consumo de14 paquetes, promoción, generación ni cambiosF01–F03. CI/integración no ejecutadas; esta orden sólo prepara candidato local.

Solicitud de revisión:sesión independiente ddd-revisor, nuevoHEAD final, limitada al incremento de rutas/PATCH/predecesores y prueba de checkout limpio, reutilizando cuatroREVIEW_PASS previos. No repetir adquisiciones,14 consumos ni ejecuciones territoriales.
