# Critical path de ejecutables DDD

**Versión:** 1.1.0  
**Fecha:** 2026-09-21  
**Estado:** vigente

## Objetivo

Mantener una cadena corta, explícita y reproducible de procesos de negocio para reconstruir un territorio desde cero o reanudarlo desde evidencia durable.

La interfaz principal es **00 · Ejecución Completa del Proyecto**. Los procesos 01–05 permanecen ejecutables de forma independiente, pero el recorrido completo se gobierna desde 00.

## Cadena completa

1. **01 · Preparación de Datos Territoriales**  
   Workflow: `.github/workflows/preparacion-fuentes.yml`  
   Materializa o reutiliza fuentes territoriales oficiales y produce un paquete identificado por run, artefacto y digest.

   **Puerta de validación territorial**  
   Comprueba identidad, edición, integridad y aptitud del paquete antes de permitir 02.

2. **02 · Generación de Distritos Autonómicos**  
   Workflow: `.github/workflows/produccion-distritos.yml`  
   Ejecuta la cadena territorial hasta M06 con la estrategia seleccionada y conserva certificación geométrica.

   **Puerta de validación de generación**  
   Comprueba el artefacto M06, su digest, la certificación territorial y su reutilización segura antes de permitir 03.

3. **03 · Preparación de Resultados Electorales**  
   Workflow: `.github/workflows/preparacion-resultados-electorales.yml`  
   Resuelve la convocatoria vigente y prepara de forma independiente el paquete electoral oficial.

   **Puerta de validación electoral**  
   Comprueba identidad, edición, hash contractual y aptitud del paquete antes de permitir 04.

4. **04 · Incorporación de Resultados Electorales**  
   Workflow: `.github/workflows/incorporacion-resultados-electorales.yml`  
   Aplica los resultados electorales sobre un producto territorial previamente certificado.

   **Puerta de validación del producto**  
   Comprueba el producto M08, el informe de incorporación y la certificación preservada antes de considerarlo consumible o publicable.

5. **05 · Publicación del Visor**  
   Workflow: `.github/workflows/desplegar-visor-publico.yml`  
   Despliega el producto ya validado. Nunca calcula distritos ni modifica el resultado territorial.

Las puertas de validación usan el workflow interno `.github/workflows/_reutilizable-puerta-validacion.yml` y emiten siempre el mismo contrato: `VALIDADO` o `BLOQUEADO`, run, artefacto, digest y evidencia durable.

## Reanudación y ejecución desde el principio

**Reutilizar progreso existente** sólo omite una fase cuando existe evidencia durable suficiente: run, artefacto, digest y estado semánticamente válido. Un flag de catálogo sin procedencia completa no basta.

**Ejecutar desde el principio** programa las cuatro fases funcionales de cálculo. Las fuentes oficiales congeladas pueden reutilizarse como materia prima idéntica; lo que no se reutiliza es el resultado calculado de la cadena territorial/electoral.

La selección de una estrategia alternativa en 02 —por ejemplo GerryChain— obliga a ejecutar la generación aunque exista un producto canónico reutilizable.

## Estado operativo único

La fuente de verdad de presentación no es el README ni el dashboard por separado.

`herramientas/estado_operativo.py` deriva un único estado estructurado desde `configuracion/catalogo_preparacion.yaml` y las evidencias durables. `herramientas/actualizar_estado_operativo.py` materializa simultáneamente:

- `publicado/estado_operativo.json`, snapshot canónico;
- `publicado/dashboard/status.json`, consumido por el dashboard;
- el bloque gestionado automáticamente de `README.md`.

Después de que las cuatro puertas de validación estén verdes, 00 ejecuta **Sincronizar estado operativo** incluso cuando `Publicar = No`. Por tanto, una ejecución productiva completa actualiza README y dashboard aunque el despliegue web se deje para más tarde.

Cuando `Publicar = Sí`, 05 sólo se ejecuta después de esa sincronización. El sitio publicado recibe así el estado actualizado de la misma ejecución.

La ejecución manual de 05 vuelve a ejecutar el mismo generador antes de desplegar, evitando publicar un snapshot obsoleto.

## Regla de publicación de Pages

GitHub Pages despliega un artefacto de sitio completo, no una ruta aislada. La publicación empaqueta siempre:

- raíz de Pages → visor territorial;
- `/dashboard/` → dashboard operativo.

La publicación es una operación de despliegue, no un quinto indicador territorial. El dashboard muestra el estado funcional FT / FE / G / RE; si los cuatro están completos, la cadena territorial-electoral está completa aunque todavía no se haya solicitado un nuevo despliegue.

## Persistencia

En `pull_request`:

- no se muta el catálogo;
- no se actualiza README ni snapshots durables en `main`;
- no se publica Pages;
- sí se ejecutan las validaciones necesarias para comprobar la arquitectura.

En producción sobre `main`:

- cada fase persiste su evidencia durable cuando corresponde;
- las puertas conservan evidencia durante 90 días;
- el estado operativo se sincroniza después de una cadena validada;
- el manifiesto de ejecución completa conserva run, artefacto, digest y decisión por fase.

## Promoción entre entornos

Cuando la separación DTAP esté materializada, este mismo critical path debe ser reproducible en cada transición:

- fin de **Dev** → reconstrucción/validación en **Test**;
- fin de **Test** → reconstrucción/publicación en **Prod**.

Ninguna fase posterior debe consumir una salida que no haya superado su puerta de validación.
