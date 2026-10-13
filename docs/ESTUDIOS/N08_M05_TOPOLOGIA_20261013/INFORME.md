# M05 Congreso: necesidad municipal por topología y cotas

Estado: incremento técnico candidato; diagnóstico únicamente; no se ejecutan distritos ni se autoriza generación.

## Cambio

La política nacional se aplica sólo cuando la llamada obtiene `municipal_policy` del contrato Congreso validado. La política por defecto del reparador permanece `indivisible`, sin cambios para consumidores autonómicos.

La validación final permite una división por CUSEC completas cuando:

1. la cantidad de distritos alcanza el límite aritmético `ceil(P_municipio/cap)`; o
2. si la topología exige más, una búsqueda determinista y exhaustiva no encuentra una asignación del municipio a menos distritos que conserve, con las demás CUSEC fijas, los K distritos, conectividad inducida y cotas poblacionales duras.

La segunda prueba se limita a 100.000 estados de búsqueda. Si se agota el presupuesto, el validador rechaza la acreditación (`MUNICIPAL_MINIMALITY_SEARCH_EXHAUSTED`); nunca transforma la falta de resultado en imposibilidad demostrada. El certificado declara expresamente que la minimalidad se prueba **dada la asignación del resto de CUSEC**. No prueba el óptimo global permitiendo reubicar simultáneamente otras CUSEC. El reparador prioriza menos fragmentación durante su búsqueda y el validador final vuelve a exigir el certificado.

M06 reutiliza el mismo validador para impedir discrepancias entre optimización y auditoría sintética. No se ha integrado ni ejecutado una ruta M04–M06 productiva del Congreso.

## Regresión requerida

El fixture contiene cuatro CUSEC en cadena, población 40 cada una y dos distritos contiguos con población 80. El municipio `39001` contiene las dos secciones de los extremos, por lo que suma 80 (`P_municipio <= cap=80`). Mantenerlo unido obliga a incluir la sección intermedia de 40 en el mismo distrito y exceder el techo, o deja una sección o distrito desconectado o bajo suelo. El validador admite la división entre distritos con certificado reproducible; el reparador y el auditor M06 conservan esa decisión. Un fixture adicional demuestra que se rechaza una división cuando una colocación municipal íntegra sí cabe.

## Invariantes y alcance

- Cada nodo sigue siendo una CUSEC oficial completa, con CPRO/CUMUN coherentes.
- No se inventan aristas; los distritos deben ser conexos en el grafo recibido.
- No cambian K, el conjunto de distritos ni los límites poblacionales.
- Las divisiones quedan registradas con CUSEC, población, cantidad mínima aritmética y certificado topológico.
- `generation_authorized=false` y los bloqueos institucionales permanecen activos.
- La búsqueda certifica necesidad dentro del estado de asignación recibido, no factibilidad o optimalidad global del plan provincial.

## Reproducción

Pruebas dirigidas: `tests/test_m05_population_repair.py` y `tests/test_congreso_preflight_adapter.py`. Reproducción de evidencia histórica: `python docs/ESTUDIOS/N08_CIERRE_NACIONAL_20261013/verificar_evidencia.py`.

