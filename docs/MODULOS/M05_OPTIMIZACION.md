# M05 — Optimizar distritos

## Propósito
M05 modifica fronteras de la solución M04 para satisfacer restricciones duras y mejorar equilibrio poblacional sin romper contigüidad.

## Prioridades vigentes
1. eliminar distritos bajo suelo o sobre techo; 2. minimizar magnitud de violaciones; 3. minimizar máximo desvío respecto del target; 4. reducir error cuadrático global. Un movimiento solo es válido si el donante permanece conectado y el receptor es adyacente.

## Entradas
Grafo M03, asignación M04, población, suelo 0,80×target, techo 1,75×target, iteraciones y semilla.

## Productos
`aragon_2025_m05_distritos_optimizados.geojson.zip`: asignación geográfica completa. `M05/asignacion_optimizada.csv`: las 1.463 secciones con distrito optimizado y contexto administrativo. `aragon_2025_m05_informe.json`: función objetivo inicial/final, violaciones, movimientos aceptados, máximo desvío, iteraciones y semilla.

## Auditoría exigida
Debe ser posible comparar M04 y M05 sección por sección, identificar qué unidades cambiaron de distrito y comprobar que ninguna transferencia rompió conectividad. El informe no sustituye a la asignación completa.

## Estado actual
Run #4 consiguió 0 violaciones de suelo/techo y `max_rel_dev≈0,3382`. El siguiente objetivo algorítmico es aproximarse a ±12% preservando todos los criterios duros ya satisfechos.
