# Reproducción independiente focalizada y contraste de resultados

Versión: 1.0.0. Nombre: reproducción independiente Cantabria N08. Fecha: 2026-10-12. Alcance: cuatro productos diagnósticos de Cantabria; no se reproducen los 55 artefactos nacionales. Estado: PASS_REPRODUCIBILIDAD, GO_ACOTADO_DATOS. Cambios: informe nuevo. Motivo: reproducción en ejecución distinta del implementador. Origen: agente separado de evidencia documental; sin predecesor.

Se leyó la herramienta `herramientas/acreditar_cantabria_n08.py` versión 1.0.0, SHA-256 `814fdd7ade38865eb095fe3ca8fdee3ce2b3b4231d40b0d20d58166ba4317d8e`, y se ejecutó una vez con los originales protegidos y los mismos recibos externos. La reproducción usa otra carpeta y proceso. No cambia inputs, geometrías, población, grafo, contrato o productos anteriores. No constituye implementación independiente del algoritmo ni revisión funcional final de todo el incremento; ésta se solicita separadamente.

Comando ejecutado desde `/Users/macbookpro/Desarrollo/DDD-n08-cantabria`:

```sh
/usr/local/Caskroom/miniforge/base/envs/ddd_aragon/bin/python herramientas/acreditar_cantabria_n08.py --parts-dir /Users/macbookpro/Desarrollo/DiputadodeDistrito/inputs/partes --output /Users/macbookpro/Desarrollo/DDD-control/planes/N08_CANTABRIA_ACREDITACION_20261012/reproduccion_independiente
```

Resultado: exit 0; 458 secciones, 102 municipios, 593623 habitantes, K=5 / K=407, 1208 aristas previas preservadas, cinco componentes de partes, siete partes nominales extraídas, 28 vacíos y 30 solapamientos. `physical_edges_created=0`, `generation_authorized=false`, sin distritos. La carga verifica cobertura, CUSEC, población y hash de geometría frente al producto 39 de #251; reprodujo sus 28 límites de vacíos y 30 áreas de solapamiento. No hubo reintentos.

Comparación independiente por bytes entre carpeta candidata y carpeta de reproducción:

| Archivo | Bytes | SHA-256 coincidente | Resultado |
|---|---:|---|---|
| RESULTADOS.json | 76085 | `9e824e4868aaa1512588f007a94ea96010eebe5f21baefd593ddc1d02f0689d8` | PASS |
| GEOMETRIAS.json.gz | 36936 | `d1aec0208b4fc70ffa31d6c5176dc3a2980a52ab3db23861b12ce467b7fb1396` | PASS |
| VACIOS_28.csv | 14839 | `99e9d8cb109d65a510636ae941eb9b8c74701102410b5e0260c120bc2687fb81` | PASS |
| SOLAPAMIENTOS_30.csv | 9634 | `1385af167b3e60705133730419323e42c6dd107d724acefadd041d577e3f12d5` | PASS |

Entorno: Python 3.11.14; Shapely 2.1.2; GEOS 3.14.1; GeoPandas 1.1.2; pyproj 3.7.2. Compresión gzip usa mtime=0. Geometrías originales EPSG:25830; fuentes externas CRS84 reproyectadas con always_xy. Los snapshots externos no se equiparan a identidad administrativa exacta de 2025.

El contraste factual de los resultados confirma:

- Gran vacío comunal `V39-1ea675806a11cc3a`: 68700278,18543337 m², recinto IGN Comunidad de Campoo y Cabuérniga cubre 99,365327%; BOC 2017 acredita condominio administrativo y BOE 2013 divisoria. La diferencia restante no se borra. Población particular continúa null/NOT_EVIDENCED; no se presupone cero ni identidad exacta de 2025.
- Vacíos palentinos `V39-473a25113f91abea` y `V39-e8e4bbf4269d759e`: 5036682,542030586 y 1689797,1286148496 m²; Pomar de Valdivia cubre 97,826510% y 97,789563%. Contienen puntos oficiales IGN Lastrilla y Cezura, respectivamente; el ayuntamiento corrobora naturaleza de enclave. Las pequeñas discrepancias de dominio no se convierten en cambios de frontera.
- 25 microvacíos: área total 0,03050041366338098m². 23 quedan completamente cubiertos en el análisis de grilla 0,0001m; persisten `V39-3ae3594e4c6f86ee` con área residual 0,0009697140391897595m² y `V39-fe0d85e63f1177e5` con 0,006677501189154043m². La sensibilidad no demuestra origen ni autoriza reparación: clasificación MICROVACIO_ANALISIS_PRECISION, estado DIAGNOSTIC_ORIGEN_NO_ACREDITADO coherentes. Los análisis de precisión no alimentan aristas físicas.
- Parte Laredo `3903503001:p0000`: ninguna relación de contacto, ningún punto nominal original interior, ningún recinto municipal externo coincidente; población null. La imagen PNOA 2023 conservada separadamente aporta contexto litoral/intermareal, sin acreditar clasificación jurídica exacta ni conexión. No se fabrica arista por proximidad.
- Parte Ribamontán `3906101003:p0000`: punto IGN Isla de Santa Marina interior a la geometría original, cobertura municipal externa 74,451756%; sin contacto y población null. BOE 2008 aporta pertenencia municipal de la isla, no residentes 2025 ni identidad íntegra del polígono.
- Parte Santander `3907504011:p0000`: no contiene directamente el punto nominal IGN. La parte del municipio externo que cubre 99,592425% del original contiene el punto Isla de la Torre. Esta evidencia se registra como correspondencia con parte externa, no falsa inclusión del punto en el polígono INE ni identidad exacta de 2025. Sin contactos, población null.
- Valle de Villaverde tiene población 249 por sección única, sin contactos a otras secciones cántabras. Corroboración independiente Nomenclátor 2025=249, sumas de entidades conciliadas. Pertenencia Cantabria y enclave se acreditan documentalmente; excepción institucional continúa pendiente.

Dictamen de datos: GO_ACOTADO. Los cuatro artefactos reproducen exactamente los bytes; los estados de desconocimiento y las discrepancias temporales/geométricas se preservan, sin población imputada ni conexiones falsas. No demuestra partición viable, autoriza excepciones, modifica tolerancias o habilita generación. Los hallazgos y límites se enviaron al implementador; no se corrigió código durante esta reproducción.

### Verificación adicional de la implementación final

Tras corregir los rechazos de hash y aislar las pruebas negativas, el revisor independiente `/root/n08_revision` ejecutó una única reproducción focalizada adicional con el mismo comando, salida externa `DDD-control/planes/N08_CANTABRIA_ACREDITACION_20261012/reproduccion_revision_final`. Código final SHA-256 `36a0ea5164611cb15d630bffdfd508a37575801c4acfe9037c198b12798ee92b`; exit0. Los cuatro archivos coinciden byte a byte y mantienen los cuatro hashes de la tabla anterior. La primera huella de herramienta documenta la versión preliminar efectivamente ejecutada, no se atribuye retrospectivamente a la implementación final. Ninguna de las dos ejecuciones reconstruye los55 artefactos nacionales.
