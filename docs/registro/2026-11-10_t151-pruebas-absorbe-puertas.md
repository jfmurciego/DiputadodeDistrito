## 2026-11-10 — T-151 — «Pruebas de la Plataforma» absorbe las puertas automáticas y el Revisor

Causa: la lista de Actions tenía cuatro workflows automáticos sueltos (puerta de contratos, documentación pública,
productos públicos y Revisor de PR) además de «Pruebas de la Plataforma».
Cambio: `pruebas-plataforma.yml` 1.7.0 incorpora esos cuatro como jobs (`contratos`, `docs`, `productos`,
`comprobar`/`revisar`/`veredicto`); un job `cambios` decide por rutas (las mismas de cada workflow retirado más el propio
fichero) cuáles corren. `pruebas` sigue siendo el check obligatorio y exige `guardian`, `suite` y `cambios` en success;
las tres puertas por rutas pueden quedar en skipped y, si corren, deben pasar; el Revisor no entra en `pruebas`.
Los cuatro workflows retirados dejan su última versión en `legacy/workflows/`. Tests ajustados a los nombres de fichero.
Pruebas: tests de seguridad de workflows, agentes en CI, catálogo, matriz, fusión automática y gobernanza en verde;
el job `cambios` se probó en un repositorio temporal (docs/contratos/productos, sin rutas, sin base comparable).
Riesgos: al pasar el Revisor a este workflow, marcar una PR como lista (`ready_for_review`) vuelve a lanzar la batería
completa; el Revisor comparte el grupo de concurrencia de la PR. Sin efecto en huellas ni en lanzamientos productivos.
