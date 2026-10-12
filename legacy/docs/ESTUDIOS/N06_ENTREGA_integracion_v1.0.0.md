# Integración N06 sobre fuentes INE 2025/2025
Versión 1.0.0; fecha 2026-10-12; alcance Congreso; estado candidato sin generación; origen N06 y PR #241.

Base f87445f5d75a53cee17cd3bcc711854318b795ff. Rama aislada codex/n06-integracion-ine2025; trabajo ajeno preservado. Dependencias: fuentes oficiales y contrato compartido con 19 ámbitos autonómicos, cuyos parámetros no se modifican.

Recuperación: bundle N06 verificado/importado, commit 0fc996502d5e4b8c61e16d11ddb030ed3250c47a. Contrato d2e8d806908d1dab8c8bbb6a8978552da0645aaa localizado en Git compartido y /private/tmp/ddd-n06-contrato-20261012. SHA256 de ambos bundles contrastados con SHA256.json: e0bc3c8b4bb4be117dae182f1000140c7661f0f15f21450de8d371b07fff06e5 y f81ad381817a530ad1e7f7fe176a54788a31552e87020c8951c48250b1be6f2c.

Delta justificado respecto de originales:
- Expediente 0fc99650 íntegro, sin repetir sus cálculos. Preflight actualizado en documento nuevo para preservar manifest histórico.
- Migración de código d2e8d806 conservada. JSON reconciliado por delta de campos, preservando sources de #241 íntegramente. Versión de artefacto 0.3.0 porque #241 ya usaba 0.2.0; schema compatible 0.2. Predecesor real en legacy/territorios/congreso/contrato_congreso_2026_pre_n06_integracion.json.
- Nota de referencia actualizada: fuentes acreditadas; otras dimensiones pendientes.
- Regresión migratoria deja de esperar fuentes ausentes. Regresión #241 conserva controles de integridad y decisiones pendientes salvo K/referencia aprobados. Predecesor literal en legacy/tests/test_materializar_fuentes_nacionales_ine_pre_n06.py.
- Pruebas de coexistencia: cuotas desde CSV acreditado, K=407, 52 ámbitos, 36.554 CUSEC, 49.128.297 habitantes, hashes de todos los archivos de fuentes de #241, alias/conflictos y rechazo de admisión productiva. Hashes fijados para checkout CI superficial.

Política: predecesores literales, versiones compatibles, sin run territorial porque no se ejecuta ni altera el motor productivo. diff --check activo PASS; global señala cuatro espacios Markdown históricos de legacy, preservados literalmente.

Pruebas: 90 regresiones PASS en entorno ddd_aragon Python 3.11; cinco pruebas institucionales PASS. Intentos iniciales con Python sin dependencias o 3.10 fueron ambientales, resueltos con entorno existente. Los dictámenes originales son históricos y no aprueban el nuevo HEAD.

N08 BLOCKED: N08_PREFLIGHT.md. generation_authorized=false. Sin piloto, 00, M01–M08 productivos, promoción, merge ni publicación de distritos.
