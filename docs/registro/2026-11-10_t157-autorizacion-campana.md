## 2026-11-10 — T-157 — Diseño de la autorización por campaña (D-41), sin aplicar

Causa: decisión D-41 del propietario vía Planificador: una frase en el chat del Operador autoriza una campaña definida.
Cambio: solo propuesta en `docs/ESTUDIOS/T157_AUTORIZACION_CAMPANA/` (ficha de campaña, plantilla de registro en `docs/autorizaciones/`, regla para CLAUDE.md compactada a 100 líneas y parches para las skills operador, lanzar-00, lanzar-campana y publicar-visor). No se edita CLAUDE.md ni ninguna skill.
Pruebas: `git apply --check` de los cinco parches sobre `main`; CLAUDE.md resultante = 100 líneas.
Efectos: ninguno en motor, huellas, workflows, visor ni datos; PR en borrador con `no-automerge` (amplía autoridad: aplicar solo con orden del propietario).
Actualización (D-46, petición del Coordinador): la ficha incluye el gasto semanal acumulado y el previsto de la campaña (tope 15.000 min/semana, aviso al 70 %, sin corte automático); plantilla, README y parche de la skill operador actualizados.
