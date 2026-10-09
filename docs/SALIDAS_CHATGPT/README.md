# Salidas de ChatGPT — continuidad operativa

**Versión:** 1.0.0  
**Fecha:** 2026-09-12  
**Estado:** vigente  
**Anterior:** primera versión

Este directorio contiene la salida mínima y persistente de la orquestación de ChatGPT. GitHub sigue siendo la única fuente de verdad.

- `SALIDA_MAESTRA.md`: puntero mutable al estado operativo más reciente.
- `HITOS/`: una salida inmutable por hito aceptado.
- Los logs, cálculos y artefactos pesados permanecen en GitHub Actions y `resultados/`; aquí solo se enlazan.

Al cerrar un hito: crear su fichero, preservar la salida maestra anterior en `legacy/salidas_chatgpt/`, incrementar su versión y actualizarla. Un chat nuevo lee primero `SALIDA_MAESTRA.md` y después únicamente el último hito enlazado.
