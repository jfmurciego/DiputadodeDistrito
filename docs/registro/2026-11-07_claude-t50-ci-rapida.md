## 2026-11-07 — T-50 — CI más rápida: suite en cinco grupos paralelos

Causa: el job `pruebas` tardaba ~13-15 min; la suite unittest (2.168 tests, ~660 s, run 42387178092) corría en un
solo proceso tras construir la imagen. Cambio: `pruebas-plataforma.yml` 1.6.0 separa un job rápido `guardian`
(guardián, R015 y pruebas sobre Git real) y una matriz `suite` de 5 grupos equilibrados por tiempo, cada uno con su
contenedor; el grupo 1 hace además el descubrimiento, GerryChain y los pasos N08 condicionales. El check obligatorio
sigue siendo `pruebas`: job final que depende de todos y falla si alguno no termina en success.
`herramientas/repartir_tests.py` 1.0.0 descubre lo mismo que `unittest discover` (mismo cargador, todos los imports)
y reparte los ficheros con LPT según `tests/tiempos_ci.json` (medido en el log del run citado). No se quita ningún
test. Pruebas: `tests/test_repartir_tests.py` (4); tests de workflows y R015 en verde; duraciones y prueba de rojo
en la PR.
