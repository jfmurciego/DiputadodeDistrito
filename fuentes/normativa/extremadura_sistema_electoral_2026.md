# Fuente normativa — Extremadura

**Proyecto:** Diputado de Distrito  
**Versión:** 1.0.0  
**Fecha de captura:** 2026-09-11  
**Estado:** fuente externa verificada para parametrización territorial

## Objeto

Fijar el tamaño institucional de la Asamblea de Extremadura y distinguirlo del reparto provincial vigente. En el procedimiento DDD, el tamaño de cámara puede conservarse como K, mientras el reparto territorial de esos K distritos se recalcula con igualdad poblacional y reglas explícitas del proyecto.

## Fuentes

1. BOE — Ley Orgánica 1/2011, de 28 de enero, de reforma del Estatuto de Autonomía de Extremadura. Artículo 17: la Asamblea tendrá un máximo de 65 diputados y la provincia es la circunscripción electoral.
   - https://www.boe.es/buscar/act.php?id=BOE-A-2011-1638
2. BOE — Ley 2/1987, de 16 de marzo, de Elecciones a la Asamblea de Extremadura. Artículo 18: la Asamblea está formada por 65 diputados; cada provincia recibe un mínimo inicial de 20 y los 25 restantes se distribuyen proporcionalmente a la población.
   - https://www.boe.es/buscar/act.php?id=BOE-A-1987-8817

## Datos retenidos

- K institucional: **65**.
- Circunscripciones legales actuales: Badajoz y Cáceres.
- Regla electoral vigente: mínimo inicial 20 por provincia + 25 proporcionales.
- Esta regla vigente **no se adopta automáticamente** como regla DDD; se conserva únicamente como referencia normativa.
- Población DDD 2025 ya certificada por EXT-01: Badajoz 665.155; Cáceres 388.190; total 1.053.345.
- Hamilton puramente poblacional sobre K=65: Badajoz **41**, Cáceres **24**.

## Trazabilidad

Estos datos justifican K=65 para EXT-03. Los coeficientes de tolerancia, suelo, techo y atomicidad municipal no quedan fijados por esta fuente y deben justificarse separadamente mediante pruebas del motor y criterios metodológicos del proyecto.
