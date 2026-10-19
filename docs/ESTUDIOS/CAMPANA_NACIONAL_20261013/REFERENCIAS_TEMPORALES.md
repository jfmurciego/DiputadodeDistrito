# Referencias temporales y linaje de reproducción

La reproducción de evidencia N08 usa fuentes del repositorio vinculadas por `MANIFEST_ENTREGA.json`, manifiestos 2025 y rutas derivadas de `Path(__file__).resolve().parents[1]`. El validador de linaje crea un directorio temporal efímero exclusivamente para sus salidas de comparación; ninguna entrada acreditada reside allí.

La búsqueda de rutas absolutas personales o de temporales se ejecutó sobre los consumidores activos del Congreso: contrato, adaptador, preflight Cáceres, preflight topológico nacional, verificador de topología, certificador de candidatos y validadores nuevos. No se encontraron rutas `/private/tmp`, `/var/folders` ni referencias `DDD-n08` en esas entradas de ejecución. Las rutas temporales que aparecen en `PRUEBAS_159.log` y `PRUEBAS_184.log` son resultados históricos de directorios temporales de tests, no dependencias que el consumidor lea.

El genérico `herramientas/preparar_visor_ejecucion.py` mantiene `/tmp/publications` como destino por defecto de publicación autonómica. No forma parte del preflight Congreso y no se usa como entrada o salida de esta campaña; no se cambió para evitar alterar el frente autonómico.

Verificación reproducible: `tests/test_campaign_no_temp_dependencies.py`. La auditoría no afirma que los logs antiguos sean portables como rutas; prueba que las rutas anotadas son salidas históricas, no referencias de lectura ejecutables.
