# Punto de reenganche DDD

Versión: 1.31.2
Fecha: 2026-09-14
Estado: R039 cerrado y certificado; R040 congelado hasta orden expresa.
Anterior: legacy/docs/PUNTO_REENGANCHE_v1.31.1.md

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

R039 sustituye la configuración artesanal de M07 por el contrato común
`ddd-election` 1.0.0. La fuente se verifica por SHA-256 antes de leerse, el
adaptador y el diccionario de partidos están fuera del código y M08 exige
cobertura distrital exacta. La validación usa pruebas sintéticas y el input
electoral ya materializado; no ejecuta M01–M08. El primer CI `34832589193`
detectó únicamente que `inputs/` no existe dentro de la imagen. La prueba ahora
verifica bytes fuera y coherencia contrato–manifiesto dentro, sin introducir un
bypass en M07. El commit `6e8162b` supera la suite general `34833051502`.
R039 queda cerrado. R040 y toda ejecución territorial permanecen congelados
hasta orden expresa.
