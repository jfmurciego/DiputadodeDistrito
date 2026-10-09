# Materialización G10 de checkpoints

El componente `g10_materializar_checkpoints.py` convierte evidencia permitida en entradas verificadas para un runner.

Para cada tramo calcula sus dependencias runtime, valida los SHA-256 del origen y materializa solo esos productos en el directorio de caché o del run nuevo. El informe resultante se marca `REUSED_MATERIALIZED`: no es una nueva certificación territorial.

Ejemplo importante: comenzar en **Equilibrar y reparar** requiere el grafo M03 y las semillas M04. Si falta uno, no se ejecuta M05. Extremadura se rechaza antes de tocar un artefacto mientras conserve estado experimental bloqueado.
