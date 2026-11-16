## 2026-11-16 — T-369 — P80 Verificación del motor: la batería en un workflow sin parámetros técnicos

**Causa.** D-129/D-130/D-131/D-132 (paso 3): un workflow por familia, sin parámetros técnicos en el botón.

**Cambio.** Nuevo `.github/workflows/p80-verificacion-motor.yml` 1.0.0 («P80 Verificación del motor»), solo manual, sin programación. Botón:
`alcance` («motor vigente» por defecto = jobs `plan` + `competicion` + `aceptacion` con D8 y 10 cadenas fijadas en el código; «motor base M05» = job
`bateria` con 7.4.4 fijada) y `territorios` (códigos separados por comas; vacío = 71; las comas se pasan a espacios en cada paso antes de llamar a la
herramienta). run-name «P80 · <alcance> · <territorios>». Fuera del botón: `funcion`, `cadenas`, `versiones_m05`. Sustituye a `bateria-motor.yml` 1.3.1
(borrado; copia en `legacy/workflows/bateria-motor_v1.3.1_20261116.yml`). Misma concurrencia (`bateria-motor`, cola `max`), permisos (`contents: read`),
instalaciones, comprobación de `pip freeze`, artefactos y comandos; sin cambios en `herramientas/bateria_motor.py` ni en `ddd_motor2`.
- Se retiran `archivar_almacen_m06` (de un solo uso, hecho en T-302/T-302d; era el único job con `contents: write`) y `archivar_p10`, cubierto por P71
  «paquete de fuentes de un territorio» (P70, T-368): mismos permisos (`contents: read`, `actions: read`), temporizador, pasos de checkout/python/pip,
  credenciales R2 solo en el paso, mismo `gh run download` y mismo comando `bateria_motor.py archivar-p10`; difiere solo que el run lo resuelve
  `p70_resolver.py paquete-p10` (no se teclea) y que la concurrencia pasa de `bateria-motor` al grupo de escritores de R2 `archivar-artefactos-r2`.
- `aceptacion` conserva `always()` (un `needs` saltado deja el job saltado): con «motor base M05» el `plan` se salta y `aceptacion` también.

**Pruebas.** `tests/test_t369_p80_equivalencia.py`: compara los cuatro jobs contra la copia congelada con sha256 (`tests/fixtures/t369_workflows/`;
faltar o cambiar hace FALLAR, sin skipTest): permisos efectivos, concurrencia, entorno (con los tres valores fijos), pasos (única sustitución admitida:
comas a espacios), artefactos, `if`; equivalencia de `archivar_p10` con P71; controles negativos. Actualizados los tests que citaban `bateria-motor.yml`
(`test_bateria_motor`, `test_t298`, `test_t297`, `test_t302_permisos_almacen` —reducido a «P80 no escribe»—, `test_artefactos_ci_cuota`,
`test_codauto_preparation_contract`, `test_design_a_matriz_sintetica`, `test_t368_p70_equivalencia`) y `.claude/rules/motor2.md`.

**Riesgos.** Sin lanzar nada: el primer uso real lo hace el Operador con permiso del propietario. Pérdida de control declarada: el botón ya no permite
otra función, otras cadenas ni otra versión M05 (cambiarlas exige una PR). El cambio de grupo de concurrencia de `archivar_p10` ya lo declaró T-368.
Sin efectos en motor, huellas ni checkpoints.
