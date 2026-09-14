# G10 — checkpoints semánticos y reenganche seguro

**Versión:** 1.0.0  
**Propósito:** reducir cómputo sin convertir una ejecución histórica en una salida nueva.

## Regla operativa

Un checkpoint es reutilizable únicamente si tiene:

1. etapa semántica conocida;
2. manifiesto de productos en ruta canónica;
3. estado `CANONICAL_VERIFIED_LEGACY` o `CERTIFIED`;
4. posición estrictamente anterior a la etapa modificada.

Ante un cambio en una etapa, G10 reinicia desde el último checkpoint canónico anterior. No salta huecos y no reconstruye una etapa para “ver si sigue ahí”.

| Cambio | Reanuda como máximo desde |
|---|---|
| Preparar unidades | Ninguno |
| Establecer vecindades | Preparar unidades |
| Construir grafo | Establecer vecindades |
| Formar distritos | Construir grafo |
| Equilibrar y reparar | Formar distritos |
| Certificar | Equilibrar y reparar |

## Inventario histórico

`orchestracion/checkpoints_fase1.json` es un índice de referencias, no una copia de evidencia. Aragón aporta M01–M06. Castilla y León tiene M03, M05 y M06; sus huecos se declaran. Extremadura mantiene M03–M06 bloqueados experimentalmente y, por diseño, no es origen de reanudación.

## Próxima integración

La siguiente modificación del procedimiento deberá aceptar un intervalo semántico y un directorio de checkpoint. Antes de ejecutarlo, G10 resolverá esta decisión; después de cada etapa, el procedimiento emitirá un manifiesto nuevo. Así el ahorro aparece en el runner, no como una promesa documental.
