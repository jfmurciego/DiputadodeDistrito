# Punto de reenganche DDD

Versión: 1.22.0
Fecha: 2026-09-13
Estado: C-07 implementado; pendiente certificación CI antes de C-06.
Anterior: legacy/docs/PUNTO_REENGANCHE_v1.21.0.md

## Fuente operativa

- Estado de máquina: orchestracion/estado_operativo_g10.json
- Estado legible: docs/SALIDAS_CHATGPT/ESTADO_OPERATIVO_G10.md
- Productos públicos declarados: orchestracion/productos_publicos.json
- Control independiente de publicación: .github/workflows/validar-productos-publicos.yml
- Puerta de admisión: herramientas/validar_contrato_territorial.py
- CI de contratos: .github/workflows/validar-contratos-territoriales.yml
- Lista de cierre: docs/CIERRE_INGENIERIA_PRODUCCION.md
- Línea única: .github/workflows/producir-territorio-por-contrato.yml
- Migración al nuevo hilo: docs/CONTINUIDAD_AUDITORIA_PLATAFORMA.md
- Prompt breve: docs/SALIDAS_CHATGPT/PROMPT_CORTO_AUDITORIA_PLATAFORMA.md

## Regla de ejecución

Aragón y Castilla y León ya son productos certificados. Extremadura permanece EXPERIMENTAL_BLOCKED. No se repite M01–M06 ni se abre otra comunidad sin cambio material y orden expresa.

## Publicación pendiente

El visor MapLibre y su contrato exhaustivo están verificados. **Validar productos públicos** produce un artefacto estático descargable sin Pages y sin ejecutar el motor. GitHub Pages requiere una única habilitación del propietario en Settings > Pages > GitHub Actions; después se relanza Desplegar visor público.

## Reenganche G10

Usar G10 — Operar lote durable sólo tras una huella nueva. Si no cambia contrato, fuente o producto, el resultado esperado es REUSED.

## Siguiente bloque de ingeniería

C-07 incorpora un caso sintético adversarial de cuatro secciones con población
60/40/30/70 y solución óptima única 100/100. Ejecuta M01–M06 solo sobre datos
temporales sintéticos, exige la asignación exacta y demuestra que el oráculo
rechaza una partición plausible pero errónea. Tras CI, continuar por C-06,
verificador independiente. No tocar C-01. R038–R040 y la expansión siguen
suspendidos.
