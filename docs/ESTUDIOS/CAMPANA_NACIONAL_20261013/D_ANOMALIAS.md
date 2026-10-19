# Registro nominal de incidencias topológicas N08

`REGISTRO_NOMINAL_D.csv` contiene 6.370 filas derivadas del producto N08: 498 pares de solapamiento intraprovincial, 5.750 contactos exclusivamente puntuales, 115 CUSEC multiparte sin población atribuida por parte y 7 pares de solapamiento interprovincial.

Los nueve pares intraprovinciales entre componentes distintos quedan identificados por sus dos componentes. Ninguno de los 498 solapamientos, 5.750 puntos ni siete pares interprovinciales figura como arista aceptada. Los contactos se enumeran a nivel CUSEC: el campo de partes recoge el inventario completo de cada sección y no afirma qué par de partes poligonales se tocó.

Las 115 filas multipartes conservan la población oficial total de sección. Cada parte tiene el estado `NOT_EVIDENCED`; no hay reparto por superficie, proximidad ni imputación. Las causas de solapamientos y puntos permanecen sin clasificar. Las excepciones nominales siguen sin decisión del propietario.

La herramienta valida el `MANIFEST_ENTREGA.json`, el SHA del manifiesto topológico y el CSV `COMPONENTES_POBLACION.csv`; también verifica los hashes de los 52 paquetes de unidad y del producto interprovincial antes de exportar. Artefactos históricos sin modificación:

- `MANIFEST_ENTREGA.json`: SHA-256 `0744fcaed562b5ff9b0c22acbeebebea238ec84416b5dc54733624f2202b6e33`.
- `producto/manifest.json`: SHA-256 `3d34d38396f8921a0916568d17919324a6409c37c49c514f3db54743150b176f`.
- `COMPONENTES_POBLACION.csv`: SHA-256 `e6bedd04fda5d44de270ee5cea9dc767e65478180a0c4c068f15de1017a1a482`.
- CSV derivado: SHA-256 `5f8d86f8da0c9a2584e6c5d7198235155ee66f826f19df070b049b33417e0af6`.

Reproducción: `python3 herramientas/registrar_anomalias_n08.py --product docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto --components docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/COMPONENTES_POBLACION.csv --output <salida.csv>`. Pruebas: `tests/test_registrar_anomalias_n08.py`. Estado de generación: `false`.
