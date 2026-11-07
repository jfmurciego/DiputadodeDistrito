---
name: revisar-pr
description: Revisión independiente de una PR de DDD antes de que la fusione el propietario. Úsala cuando pidan revisar una PR o un diff. Quien construye no certifica: revisa con el diff y la especificación, en solo lectura.
---

# Revisar una PR

Veredicto: `PASS`, `PASS_WITH_EXCEPTIONS`, `FAIL` o `BLOCKED`, ligado al SHA del HEAD revisado. Si el HEAD cambia
después, la revisión deja de valer.

Lista de comprobación (solo lo que aplique al diff):
1. CI: el job `pruebas` en verde en la PR (y `main` en verde) — sin eso, `BLOCKED`.
2. Gobernanza: cada fichero versionado cambiado sube VERSIÓN y deja copia en `legacy/` con ANTERIOR existente;
   `docs/MODULOS/*.md` declara la versión activa si cambia un módulo.
3. Registro: número = último de `main` + 1 y asignado por el planificador; sin marcas de conflicto.
4. Huellas: si toca `modulos/05*`, `modulos/04*` o ficheros con hash N08, ¿lo dice la PR y monta las copias
   archivadas? ¿Qué modo de 00 exige?
5. Reglas del propietario: sin cambios de suelo, techo, K ni atomicidad sin decisión registrada; sin renombrar
   `modulos/*`; topónimos en español.
6. Unidades y CRS: metros en CRS proyectado (25830/3035 según contrato), grados solo en copias web WGS84.
7. Tests: hay uno que falla sin el arreglo y pasa con él (rojo/verde), no solo verdes nuevos.
8. Workflows: nombres y lista de `workflow_dispatch` fijados por los tests de diseño A; `run:` pasa `bash -n`.
9. Efectos externos: la PR no lanza, publica ni fusiona como efecto colateral.

Salida: veredicto + SHA + hallazgos ordenados por gravedad (fichero:línea, fallo concreto). Sin comentarios en
GitHub salvo que se pidan. Casos de calibración: candidato modificado tras la revisión; reparaciones agotadas
con criterio fallido.
