# Pruebas y conservación
Versión 1.0.0; fecha 2026-10-12; alcance diagnóstico Cantabria; estado candidato; cambio: validación y conservación; motivo: trazabilidad; origen: nueva evidencia N08, sin predecesor.

La suite relevante nacional y autonómica termina con **144 pruebas PASS** en `regresiones_completas.log`, incluidas diez nuevas de Cantabria. Cubre contratos Congreso, alias N06, fuentes INE 2025, N07, topología, factibilidad, adaptador preflight, catálogo de los 19 ámbitos y contratos de pasarelas. Las ejecuciones M02 de esos tests son sintéticas y temporales; no se ha ejecutado el pipeline productivo.

Comando ejecutado desde la raíz (Python3.11.14 del entorno ddd_aragon):

```sh
python -m unittest tests.test_acreditar_cantabria_n08 tests.test_congreso_contract tests.test_congreso_origin_migration tests.test_n06_ine_coexistence tests.test_congreso_topology tests.test_congreso_feasibility tests.test_congreso_preflight_adapter tests.test_crosswalk_nacional tests.test_evidencia_continuidad_nacional tests.test_materializar_fuentes_nacionales_ine tests.test_catalogo_territorios_espana tests.test_topology_preflight tests.test_politica_topologica tests.test_topology_bridge_contracts -v
```

Los dos primeros recorridos presentaron un error ambiental en la misma prueba de continuidad: el checkout disperso no contenía el geoJSON histórico y después el modelo histórico requerido. Se materializaron esos archivos existentes de Git, sin modificarlos ni relajar tests. La prueba aislada y la suite completa posterior pasan. Los logs anteriores se conservan para evitar ocultar esos intentos.

Nuevas pruebas: cobertura/identidad/población rechazadas con fixtures válidos; hash de fuente ajena; hash de vacío ajeno incluso con prefijo nominal conocido; los 28 vacíos conservan identidades y áreas originales;25 microvacíos tienen contraste y sensibilidad individual;30 solapamientos conservados; ausencia de contactos de las cuatro partes aisladas; población parcialnull; correspondencia nominal de la Torre registrada mediante polígono externo sin fingir punto dentro del original; invariantes458/593623/K=5/407 y generación false.

CONSERVACION_BASE.json demuestra igualdad byte a byte con base29502ea de60 archivos protegidos:55 productos nacionales y cinco archivos del paquete Congreso (contrato, fuentes y procedencia). No se reconstruyen ni modifican. No hay cambios del motor común ni producción autonómica.

Reproducción independiente: dos agentes externos a la implementación revisaron respectivamente datos y delta funcional. La primera reproducción precedió los endurecimientos de rechazo sugeridos por revisión. La segunda ejecutó la implementación final, SHA-256 `36a0ea5164611cb15d630bffdfd508a37575801c4acfe9037c198b12798ee92b`, y obtuvo los mismos cuatro artefactos por bytes. No se reutilizó el caché original del implementador: se leyó de nuevo el ZIP protegido mediante loader y se extrajo sólo Cantabria. Los hashes están en REPRODUCCION_INDEPENDIENTE.md y MANIFEST.json.

La CI debe consultarse sobre el HEAD exacto de la PR; un PASS de pruebas o CI no autoriza el piloto. Su resultado remoto se entrega con el SHA y enlace al cierre, sin reescribir evidencias sólo para promocionar estado.
