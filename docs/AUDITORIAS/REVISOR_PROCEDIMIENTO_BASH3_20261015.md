# Revisión independiente — compatibilidad Bash 3 del procedimiento

Fecha: 2026-10-15  
Dictamen: **GO_ACOTADO**  
Alcance: `procedimiento.sh` v2.9.2 y su regresión de encadenamiento.

La revisión independiente no encontró defectos en el alcance. El predecesor archivado `legacy/procedimiento/procedimiento_v2.9.1.sh` coincide byte por byte con el contenido de `HEAD` previo al cambio (SHA-256 `15760024420f21ba8963bb75f94ac8a6663012cfcc9b7a5d5b62947a21711cb4`). La sustitución de `readarray` conserva la resolución de las dos rutas del contrato y falla de forma cerrada cuando faltan líneas o aparecen sobrantes.

Comprobaciones comunicadas por el revisor:

- `/bin/bash` GNU 3.2.57; `bash -n procedimiento.sh`: PASS.
- `tests/test_procedimiento_encadenado.py`: 2/2 PASS con PyYAML disponible en `PATH`.
- Sin el `PATH` Miniforge, la primera prueba no podía importar `yaml`; se clasificó como problema de entorno de pruebas.
- Cabeceras de versión y changelog con predecesor conservado.

El dictamen cubre solo esta corrección y no el worktree completo ni su integración. Base/HEAD Git `42163cd8cebd120db9ab9fd1329c32ccdd87cf36`; cambios locales sin commit.
