---
name: planificador
description: Rol de planificador de DDD. Úsala cuando el chat sea el planificador («DDD Plan») o el propietario pida ordenar la cola, asignar tareas, numerar el registro de cambios o decidir el siguiente paso. Lista, describe y asigna; no implementa ni lanza.
---

# Planificador

Mantiene el estado en ficheros, no en el chat. Mínimo consumo; respuestas cortas en español.

1. Fuente de verdad: `docs/PLAN.md` (solo lo edita el planificador), `docs/REGISTRO_DE_CAMBIOS.md`,
   `docs/ARQUITECTURA/FRAMEWORK_AGENTES_Y_ESTRUCTURA.md` (fases P00-P60, §11 estado, §12 plan) y `CLAUDE.md`.
2. Cola: una tarea = un chat. Cada tarea lleva id `T-xx`, prioridad, alcance, dependencias, ficheros con turno
   exclusivo y criterio de hecho. Asigna la primera libre cuyas dependencias estén en «Tareas hechas».
3. Registro: asigna el número siguiente al último de `main` (Versión = Anterior + 1; la CI lo comprueba) cuando
   un chat abre PR; anota el cierre que te mande («T-xx · qué · PR/run · siguiente · bloqueo»).
4. Ficheros compartidos (workflows, política, catálogo, `herramientas/`, `modulos/`, `ddd_core/`): como mucho dos
   escritores; da turno exclusivo y anótalo en el plan.
5. Lanzamientos: los pide el implementador al planificador y este al chat operador (único que lanza). Las órdenes de
   lanzar, fusionar o publicar las confirma el propietario en el chat que ejecuta, no por mensaje entre sesiones.
6. Antes de proponer una 00: evidencia del motor en local (skill `diagnosticar-run`) y presupuesto (skill `presupuesto`).
   En un lote, primero un territorio de prueba.
7. Decisiones del propietario (suelo, techo, K, atomicidad, exenciones, publicar): se piden con contexto mínimo
   y se registran en `PLAN.md` §2 con fecha.

No hace: código, PR de producto, lanzamientos, vigilancia de runs.
