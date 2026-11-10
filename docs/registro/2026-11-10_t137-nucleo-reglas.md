## 2026-11-10 — T-137 — Núcleo único de reglas: inventario y diseño

- Causa: «plan válido» está definido en seis sitios (validador, canónico M05, reparadores, dos GerryChain) con
  diferencias reales (tolerancia dura solo en el ensemble, provincia única por defecto False en el validador,
  mixtos fijos a 1, normalización distinta de particiones y cuotas).
- Cambio: `docs/ESTUDIOS/T137_NUCLEO_REGLAS/INVENTARIO_DIVERGENCIAS.md` (líneas exactas y ejemplos) y
  `docs/ARQUITECTURA/NUCLEO_REGLAS.md` (API pura `ddd_motor2/reglas/`, migración en sombra, riesgos y opciones
  de criterio para el propietario). Sin código de producción; huellas intactas.
- Pruebas: solo documentación.
