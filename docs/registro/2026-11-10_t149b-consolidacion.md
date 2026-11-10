## 2026-11-10 — T-149 — «Pruebas de la Plataforma» absorbe las puertas automáticas por rutas

Causa: tres puertas automáticas sueltas (contratos, documentación pública, productos públicos) además de «Pruebas de la Plataforma».
Cambio: `pruebas-plataforma.yml` 1.7.0 las incorpora como jobs (`contratos`, `docs`, `productos`); un job `cambios` decide por
rutas (las mismas de cada workflow retirado más el propio fichero) cuáles corren; `docs` conserva su concurrencia propia.
`pruebas` sigue siendo el check de la batería: exige `guardian`, `suite` y `cambios` en success; las tres puertas por rutas
pueden quedar en skipped y, si corren, deben pasar. Los tres workflows retirados dejan su última versión en `legacy/workflows/`.
El Revisor de PR NO se absorbe: el ruleset activo exige el check `veredicto`, así que `revisor-pr.yml` (1.0.2) solo se renombra
a «Revisor de PR» (sin «_Interno — »), con jobs y `veredicto` intactos; qué hacer con él lo decide el propietario.
Pruebas: seguridad de workflows, catálogo, matriz, fusión automática y gobernanza en verde; el job `cambios` se probó en un
repositorio temporal (docs/contratos/productos, sin rutas, sin base comparable). La CI de la propia PR es la prueba real.
Riesgos: ninguno para fusión automática ni para el Revisor; sin efecto en huellas ni en lanzamientos productivos.
