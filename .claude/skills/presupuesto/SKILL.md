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
- Modelo y esfuerzo: los de la tabla de `configuracion/presupuesto_ventana.json` (Sonnet por defecto; Opus en el motor y en el
  Planificador). Al crear una sesión, `model` y `effort` van siempre explícitos; Fable o más esfuerzo que la tabla, solo con la frase del propietario.
- Sin esperas activas ni vigilancia de runs; sin avisos intermedios.

Libro de costes (una línea por ejecución de agente, run o chat cerrado, en el cierre de la tarea):
`fecha · rol/tarea · tokens o minutos (si se conocen) · PR · resultado · ¿a la primera?`
Topes por chat: ver `docs/ARQUITECTURA/FICHAS_AGENTES.md` §1; al llegar al tope, parar y cerrar con la evidencia.

Métricas (FRAMEWORK §8): coste por provincia cerrada; % de 00 que pasan a la primera (al 02-11 ~20 %, objetivo
> 60 %); causas raíz cerradas por día. Tope de gasto semanal: el que fije el propietario; al acercarse, parar y avisar.

## Ventana de 5 horas (T-511, D-217)
El tope real es la ventana de 5 horas, no el semanal. `configuracion/presupuesto_ventana.json` fija (el propietario lo cambia, sin tocar
código) 90 USD de equivalencia por ventana, repartidos 30 % reserva del propietario, 15 % coordinación y 55 % trabajo, la tabla de
modelo y esfuerzo por rol y el coste estimado por sesión. Antes de abrir una flota o una ola de chats, escribe el plan en JSON y
pásalo: `python herramientas/presupuesto_ventana.py --plan <flota.json>`; si sale ≠ 0, no abras los chats: reduce la ola o
pártela en dos ventanas. Formato y reglas en la cabecera de la herramienta.
