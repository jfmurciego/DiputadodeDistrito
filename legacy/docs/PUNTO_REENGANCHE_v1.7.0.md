# Punto de reenganche DDD

Versión: 1.7.0
Fecha: 2026-09-13
Estado: línea base de producción cerrada y certificada; preparada para auditoría.
Anterior: legacy/docs/PUNTO_REENGANCHE_v1.6.0.md

## Fuente operativa

- Estado de máquina: orchestracion/estado_operativo_g10.json
- Estado legible: docs/SALIDAS_CHATGPT/ESTADO_OPERATIVO_G10.md
- Productos públicos declarados: orchestracion/productos_publicos.json
- Control independiente de publicación: .github/workflows/validar-productos-publicos.yml
- Puerta de admisión: herramientas/validar_contrato_territorial.py
- CI de contratos: .github/workflows/validar-contratos-territoriales.yml
- Lista de cierre: docs/CIERRE_INGENIERIA_PRODUCCION.md
- Línea única: .github/workflows/producir-territorio-por-contrato.yml

## Regla de ejecución

Aragón y Castilla y León ya son productos certificados. Extremadura permanece EXPERIMENTAL_BLOCKED. No se repite M01–M06 ni se abre otra comunidad sin cambio material y orden expresa.

## Publicación pendiente

El visor MapLibre y su contrato exhaustivo están verificados. **Validar productos públicos** produce un artefacto estático descargable sin Pages y sin ejecutar M01–M06. GitHub Pages requiere una única habilitación del propietario en Settings > Pages > GitHub Actions; después se relanza Desplegar visor público.

## Reenganche G10

Usar G10 — Operar lote durable sólo tras una huella nueva. Si no cambia contrato, fuente o producto, el resultado esperado es REUSED.

## Siguiente bloque de ingeniería

R035 está certificado en CI: [run 34747763671](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34747763671). No quedan tareas de ingeniería base. Mantener congelada la ejecución territorial. El siguiente trabajo exige una instrucción expresa para incorporar un territorio mediante `Producción territorial por contrato` y su YAML/fuentes.
