# Empezar hoy

Zensical transforma archivos Markdown en un sitio estático. Se utiliza desde el repositorio: no requiere una cuenta Zensical ni una suscripción.

## Leer y editar

Desde la raíz del repositorio, con Python 3.12:

```bash
python3 -m venv .venv-docs
.venv-docs/bin/python -m pip install -r documentacion_publica/requirements.lock
.venv-docs/bin/zensical serve -f documentacion_publica/zensical.toml
```

Abre `http://127.0.0.1:8000`. Edita las páginas de `documentacion_publica/docs/`: la vista se actualiza. En Windows, usa `.venv-docs/Scripts/`.

## Proponer una mejora

1. Crea una rama desde `main` y modifica la página correspondiente.
2. Cita el código, contrato, fuente o ejecución que sostiene la afirmación.
3. Ejecuta la construcción estricta y abre una PR.
4. Distingue capacidad implementada, evidencia verificada y propuesta pendiente.

```bash
.venv-docs/bin/zensical build --strict --clean -f documentacion_publica/zensical.toml
```

## Qué se puede usar ya

GitHub aloja las fuentes del portal y permite revisarlas; Zensical genera la documentación. El [archivo R2](archivo-r2.md) tiene un plan concreto de activación, pendiente de cuenta y conexión. El [plan de trabajo](plan.md) separa esos hitos.

No pegues claves de almacenamiento en documentos, issues o chats. Las credenciales de la integración se configuran en el proveedor y en los secretos del entorno de CI.

*Versión 1.0.0 · 2026-11-03 · Archivo nuevo.*
