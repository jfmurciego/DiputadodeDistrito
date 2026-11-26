## 2026-11-24 — Auditoría — Auditoría integral del proyecto: veredicto, benchmark, web y dirección

- **Causa:** encargo del propietario (24-11): veredicto en un fichero, evolución del proyecto, comparación con proyectos existentes, valoración de la web y auditoría de la dirección.
- **Cambio:** `docs/AUDITORIAS/AUDITORIA_INTEGRAL_2026-11-24.md` 1.0.0 (fichero nuevo). Solo documento: no cambia código, contratos, workflows, plan ni decisiones.
- **Método:** solo lectura sobre `main` en `f52c298d`; cifras de desvío de población calculadas sobre `datos/composicion/runs/` (último run de cada uno de los 71 territorios) y `visor/v2/datos/provincias.json`; contraste externo por búsqueda, con los enlaces en el §14 del informe. No se ha ejecutado el motor ni se ha lanzado o publicado nada.
- **Pruebas:** `python herramientas/comprobar_guardian_main.py registro` y `marcas`.
- **25-11:** auditoría 1.0.1 (corrige el dato del depósito con DOI) y `docs/AUDITORIAS/PLAN_MEJORA_2026-11-25.md` 1.0.0: propuesta de plan de mejora para aprobar (36 tareas provisionales T-463 a T-498 por olas, metas medibles por ámbito, 10 preguntas con recomendación). No toca `docs/PLAN.md`; no implementa ni lanza nada.
- **25-11 (tarde):** `PLAN_MEJORA_2026-11-25.md` 2.0.0, reescrito a petición del propietario como informe para decidir: 13 bloques con lo que pasa hoy, por qué importa, qué se haría, qué se recibe y qué pasa si no se hace; coste dentro del plan semanal, sin gasto adicional; sin olas con fecha; decisión por bloques. Sigue siendo propuesta: nada autorizado.
- **25-11 (noche):** `docs/traspasos/2026-11-25_auditoria.md`: estado, aprobaciones (ninguna), acuerdo de coordinación con el Planificador vivo y lecciones. Sin chat sucesor.
- **PR/run:** PR de la rama `claude/dreamy-maxwell-mezgob`, abierta el 26-11 por orden del propietario (vía Planificador). Solo documentación, con `no-automerge`; sin runs.
