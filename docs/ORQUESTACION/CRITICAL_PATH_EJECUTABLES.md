# Critical path de ejecutables DDD

**Versión:** 1.0.0  
**Fecha:** 2026-09-20  
**Estado:** vigente

## Objetivo

Mantener una lista corta y explícita de los workflows que deben poder ejecutarse desde cero cuando se reconstruya un entorno o se promueva la solución entre entornos.

La lista describe el **critical path operativo**. No sustituye las puertas automáticas de CI ni implica que la separación completa Dev/Test/Prod esté ya implementada en el repositorio.

## Critical path manual

1. **Preparación de Datos Territoriales**  
   Workflow: `.github/workflows/preparacion-fuentes.yml`  
   Materializa y valida las fuentes territoriales reutilizables.

2. **Preparación de Resultados Electorales**  
   Workflow: `.github/workflows/preparacion-resultados-electorales.yml`  
   Materializa de forma independiente las fuentes electorales oficiales.

3. **Generación de Distritos Autonómicos**  
   Workflow: `.github/workflows/produccion-distritos.yml`  
   Ejecuta la cadena territorial M01–M06 y produce el resultado territorial.

4. **Incorporación de Resultados Electorales**  
   Workflow: `.github/workflows/incorporacion-resultados-electorales.yml`  
   Ejecuta M07–M08 sobre un M06 válido cuando se quiera publicar el producto territorial-electoral.

5. **Publicar Sitio Web**  
   Workflow: `.github/workflows/desplegar-visor-publico.yml`  
   Publica GitHub Pages sin recalcular distritos. Expone selector humano de página:
   - `Sitio completo`
   - `Visor territorial`
   - `Dashboard operativo`

## Regla de publicación de Pages

GitHub Pages despliega un artefacto de sitio completo, no una ruta aislada. Por tanto, el selector **Página a publicar** identifica la página objetivo del run, pero el workflow empaqueta siempre todas las páginas activas para evitar que publicar una ruta elimine las demás.

Actualmente:

- raíz de Pages → visor territorial;
- `/dashboard/` → dashboard operativo.

Las páginas futuras se añadirán al mismo selector y al mismo paquete de sitio.

## Promoción entre entornos

Cuando la separación DTAP esté materializada, este mismo critical path debe ser reproducible en cada transición:

- fin de **Dev** → reconstrucción/validación en **Test**;
- fin de **Test** → reconstrucción/publicación en **Prod**.

Las puertas automáticas de plataforma, contratos y productos públicos deben estar verdes antes de promover. La publicación web es el último ejecutable del critical path y no puede disparar cálculo territorial.
