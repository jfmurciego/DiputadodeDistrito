# Fixture congelada de T-349

Estado de los registros (catálogo, recibos electorales y de fuentes, par, M06, M08, datos y registro del visor) en el commit base
`25dd77724e649257a6d2dfdfe65d40c9fd12a5ec`: id viejo en 71 recibos electorales y en los demás objetos de la tabla. Se generó con
`_generar_fixture.py`. Los tests de T-349 usan esta raíz, nunca el estado vivo, para no romperse cuando la Activación registre
recibos canónicos. `inventario_esperado.json` es la salida del generador sobre esta raíz (sin Activación).
