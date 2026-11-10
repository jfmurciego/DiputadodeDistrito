## 2026-11-10 — T-149 — Los tres escritores de main pasan a jobs de «Pruebas de la Plataforma»

Causa: Catálogo de procedencia, Resultados ligeros y Numeración del Registro eran tres workflows sueltos que solo escriben en main.
Cambio: `pruebas-plataforma.yml` 1.8.0 los incorpora como jobs `catalogo`, `resultados` y `numeracion`: solo push a main, mismas rutas
(las calcula el job `cambios`, sin el disparo por el propio fichero), credencial de registro tras el checkout, concurrencia propia
sin cancelar (`queue: max`) y `continue-on-error` para que un fallo de un escritor no tiña de rojo el run de la batería. No dependen
de la suite ni entran en `pruebas`; no cambia qué se comprueba ni cuándo. Los tres antiguos dejan su última versión en
`legacy/workflows/`; reglas de `.claude/rules/` actualizadas.
No incluye las medidas de ahorro de CI (cancelación en main, solo guardián en pushes de robots, nocturna): quedan pendientes de la
autorización del propietario en el chat que ejecuta.
Pruebas: seguridad de workflows, credencial de registro, catálogo/matriz de diseño, contrato de preparación, agentes en CI,
fusión automática y gobernanza en verde. Prueba real: el primer push a main que toque cada ruta tras fusionar.
Riesgos: un push a main de un escritor ahora comparte workflow con la batería (un run por push); `queue: max` a nivel de job sin validar
en GitHub hasta el primer disparo.
