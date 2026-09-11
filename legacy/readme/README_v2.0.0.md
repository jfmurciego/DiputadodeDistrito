# Diputado de Distrito

**Versión del documento:** 2.0.0 — Procedimiento modular reproducible  
**Fecha:** 2026-09-11

Procedimiento reproducible y auditable para construir distritos uninominales a partir de unidades censales oficiales.

## Ejecución de referencia

En GitHub: **Actions → Procedimiento DDD — Aragón → Run workflow**.  
Modos: `completo` reconstruye la base desde las fuentes; `iterativo` reutiliza los módulos 01-03 si la caché es válida.

## Organización

El procedimiento consta de ocho **módulos** documentados en `docs/MODULOS.md`. Cada cambio conserva su versión anterior en `legacy/`, incrementa versión interna y se registra en `docs/BITACORA.md`.

Una versión solo se considera validada cuando el mismo commit ejecuta de extremo a extremo en GitHub Actions y supera `herramientas/validar_ejecucion.py`.
