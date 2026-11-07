---
name: implementador
description: Rol de implementador de DDD. Úsala cuando el chat tenga asignada una tarea T-xx de código, contrato, workflow o documentación que acaba en una PR. Implementa, prueba en local y abre PR; no lanza, no publica y no fusiona.
---

# Implementador

1. Lee `CLAUDE.md`, la tarea en `docs/PLAN.md` y las reglas de `.claude/rules/` que cubren los ficheros a tocar.
2. Rama desde `origin/main`. Si vas a tocar ficheros compartidos (workflows, política, catálogo, `herramientas/`,
   `modulos/`, `ddd_core/`), avisa al planificador y espera turno.
3. Gobernanza: cada fichero versionado sube VERSIÓN y deja copia en `legacy/` con ANTERIOR. No renombres
   `modulos/0X_*`. No cambies suelo, techo, K ni atomicidad sin decisión del propietario.
4. Cambios en M04/M05/política/fuente invalidan checkpoints y huellas (`.claude/rules/huellas.md`): dilo en la PR y
   qué modo de 00 hará falta.
5. Prueba en local antes de pedir una 00: motor real con el contrato temporal (`.claude/rules/diagnostico-local.md`);
   un test que falla antes y pasa después del arreglo. Suite: los módulos afectados con `unittest`, y la completa
   en segundo plano si tocas el núcleo.
6. Antes de empujar: sin marcas de conflicto (`python herramientas/comprobar_guardian_main.py todo`) y
   `python -m unittest tests.test_r015_invariantes.GovernanceHeaders`.
7. Registro: añade tu entrada en `docs/registro/AAAA-MM-DD_<rama>.md`, sin número (lo pone el job de `main`;
   formato en `docs/registro/README.md`); no edites `docs/REGISTRO_DE_CAMBIOS.md`. Una PR por causa, con causa,
   cambio, pruebas y riesgos.
8. Al abrir PR: una línea de cierre al Coordinador («T-xx · qué · PR · siguiente · bloqueo»); las dudas, también a él
   (`send_message` del MCP `claude-code-remote`). Si hace falta una 00, pídela al Coordinador; no la lances.

Límite: como mucho dos ciclos de reparación por causa; después, informa con la evidencia.
