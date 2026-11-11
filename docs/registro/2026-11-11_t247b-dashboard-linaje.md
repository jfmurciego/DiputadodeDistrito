## 2026-11-11 — T-247 — El test del dashboard sigue la regla de linaje del M08

- Causa (suite 2 de #713, #716 y #717; reproducido en `origin/main` ca3f3c5): `test_dashboard_pages…test_dashboard_se_genera_desde_catalogo`
  esperaba «re» en verde para Galicia solo con `electoral_product_available`. Los commits del bot `388d3611` (M06 nuevo,
  run 43045478748) y `2f2a7285` dejaron el M08 del run 41044499258, de otro linaje, mientras la cadena hace la 04. El
  generador (`generar_estado_operativo.py`, regla #354) da «yellow», que es lo correcto. No es un derivado versionado
  desfasado: el test calcula el payload desde el catálogo vivo.
- Cambio (solo el test): «re» esperado = disponible y el M08 es del run del M06 o su manifiesto acredita la 02 con ese
  M06 y la 04 en success (invariante de #354, leído de los manifiestos).
- Mutación: generador sin la comprobación de linaje → el test falla con el estado actual.
- Límite: el test sigue sobre el estado vivo de Galicia; cuando la cadena termine, ejercerá la rama verde.
