# Punto de reenganche DDD

Versión: 1.28.1
Fecha: 2026-09-13
Estado: C-13 cerrado y certificado; C-12 es el siguiente hito.
Anterior: legacy/docs/PUNTO_REENGANCHE_v1.28.0.md

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

C-13 convierte P07 en un alcance supra-municipal medible y neutral ex ante. Las
rutas comarcales existentes están desactivadas y Extremadura no declara fuente:
los tres territorios quedan `NOT_EVALUABLE`, por tanto bloqueados para publicación.
No se modifican límites ni se ejecuta M01–M06. El commit `5a4a884` supera la
suite general `34786528440`, único workflow activado. Continuar por C-12. No
tocar C-01. R038–R040 y la expansión siguen suspendidos.
