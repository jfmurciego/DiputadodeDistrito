---
name: presupuesto
description: Control de gasto de DDD. Úsala antes de proponer o lanzar ejecuciones, abrir chats o subagentes, y cuando el propietario pida métricas de coste o el balance semanal.
---

# Presupuesto

Regla rectora: lo más pequeño que funcione. Mecánico → CI o script; procedimiento → skill; acotado → subagente de
solo lectura; largo y con decisiones → chat con rol.

Antes de gastar:
- ¿Hay evidencia local? Ninguna 00 sin el motor probado en local (M04+M05 ~15 s).
- ¿Es un lote? Primero un territorio de prueba.
- ¿Es un reintento? Como mucho dos ciclos de reparación por causa; nunca relanzar «para ver qué pasa».
- ¿Hace falta un agente? Si no hay juicio, no.
- Modelo: Sonnet por defecto; Opus solo para el motor (M04, M05, GerryChain).
- Sin esperas activas ni vigilancia de runs; sin avisos intermedios.

Libro de costes (una línea por ejecución de agente, run o chat cerrado, en el cierre de la tarea):
`fecha · rol/tarea · tokens o minutos (si se conocen) · PR · resultado · ¿a la primera?`
Topes por chat: ver `docs/ARQUITECTURA/FICHAS_AGENTES.md` §1; al llegar al tope, parar y cerrar con la evidencia.

Métricas (FRAMEWORK §8): coste por provincia cerrada; % de 00 que pasan a la primera (al 02-11 ~20 %, objetivo
> 60 %); causas raíz cerradas por día. Tope de gasto semanal: el que fije el propietario; al acercarse, parar y avisar.
