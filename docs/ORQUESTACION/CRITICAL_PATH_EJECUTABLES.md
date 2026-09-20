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
   Interfaz humana exclusivamente manual. No se invoca desde la producción territorial. Expone selector:
   - `Dashboard operativo`
   - `Visor territorial`
   - `Sitio completo`

El despliegue técnico común vive en `.github/workflows/_reutilizable-publicar-sitio.yml` y no tiene botón manual. La producción territorial lo usa únicamente para actualizar el visor y siempre conserva el último snapshot de dashboard promovido explícitamente.

## Regla de publicación de Pages

GitHub Pages despliega un artefacto de sitio completo, no una ruta aislada. Por tanto, el selector **Página a publicar** identifica la página objetivo del run, pero el workflow empaqueta siempre todas las páginas activas para evitar que publicar una ruta elimine las demás.

Actualmente:

- raíz de Pages → visor territorial;
- `/dashboard/` → dashboard operativo.

Las páginas futuras se añadirán al mismo selector y al mismo paquete de sitio. Cada página no territorial mantiene un snapshot en `publicado/`; cambiar su código fuente no la promueve. El dashboard sólo actualiza `publicado/dashboard/` cuando el usuario ejecuta `Publicar Sitio Web` con `Dashboard operativo` o `Sitio completo`.

## Promoción entre entornos

Cuando la separación DTAP esté materializada, este mismo critical path debe ser reproducible en cada transición:

- fin de **Dev** → reconstrucción/validación en **Test**;
- fin de **Test** → reconstrucción/publicación en **Prod**.

Las puertas automáticas de plataforma, contratos y productos públicos deben estar verdes antes de promover. La publicación web es el último ejecutable del critical path y no puede disparar cálculo territorial.

## Sincronización del dashboard

El estado del dashboard no se mantiene a mano. `herramientas/generar_estado_dashboard.py` deriva `status.json` desde `configuracion/catalogo_preparacion.yaml` y sus evidencias. La generación territorial puede actualizar el catálogo y sus receipts sin publicar el dashboard. La siguiente publicación manual del dashboard toma ese estado actualizado, crea un commit de promoción en `publicado/dashboard/` y sólo entonces lo despliega.
