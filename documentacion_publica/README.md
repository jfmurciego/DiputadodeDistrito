# DDD — Portal Zensical

**Versión 1.0.0 · 3 de noviembre de 2026 · Archivo nuevo.**

Portal inicial documentado contra `main` **11f0ba2b775a889f2316e31ebdbd859cbc50ab13**.
No modifica el motor, catálogos operativos ni el publicador del visor. El workflow nuevo solo construye y valida documentación.

Desde la raíz del repositorio:

```bash
python3 -m venv .venv-docs
.venv-docs/bin/python -m pip install -r documentacion_publica/requirements.lock
.venv-docs/bin/zensical serve -f documentacion_publica/zensical.toml
```

Abrir `http://127.0.0.1:8000`. En Windows, sustituir `.venv-docs/bin/` por `.venv-docs/Scripts/`.

Construcción verificable:

```bash
.venv-docs/bin/zensical build --strict --clean -f documentacion_publica/zensical.toml
```

El HTML se genera en `documentacion_publica/site/`. Las dependencias tienen versiones fijadas; este lock no contiene hashes de distribución ni congela Python y el sistema operativo. La configuración utiliza páginas `.html` y fuentes del sistema para facilitar su consulta local. Para utilizar búsqueda y evitar restricciones de `file://`, servir el sitio mediante HTTP.

La auditoría es estructural con una muestra material de Cantabria M05: se han contrastado los bytes del checkpoint y los 50 candidatos, sin repetir la optimización ni la auditoría geográfica completa. Ver `docs/auditoria.md` y `evidencias/`.

El plan R2 todavía no está conectado a una cuenta ni a la 00. La publicación de este portal en producción queda para una PR posterior que integre su salida en el único publicador de Pages, o para otro repositorio con su propio Pages.
