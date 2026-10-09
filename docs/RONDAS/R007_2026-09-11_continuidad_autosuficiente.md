# R007 — Continuidad autosuficiente del repositorio

**Fecha:** 2026-09-11  
**Tipo:** documentación/arquitectura de conocimiento; no cambia el algoritmo ni los contratos ejecutables.

## Motivo
Se audita si una sesión nueva puede continuar el proyecto leyendo únicamente GitHub. La documentación existente cubría arquitectura y rondas recientes, pero dispersaba o no explicitaba varios hechos históricos necesarios para evitar regresiones.

## Hallazgos
Faltaban en un punto canónico: historia H≈61; criterio de granularización Zaragoza CUDIS→CUSEC; split≤3; defecto V2 de contigüidad; criterio de nombres urbanos; diferencia 1.358.812 vs 1.364.621; referencia 4.302 vs 4.293 aristas; defectos históricos de ingestión/configuración; orden de lectura para una sesión nueva; y una declaración inequívoca de la siguiente acción.

## Acción
Se crea `docs/ESTADO_MAESTRO_PROYECTO.md` v1.0.0 como índice y estado canónico de continuidad. No sustituye bitácora, arquitectura, expedientes de ejecución ni `legacy/`; los enlaza y resume aquello que una sesión nueva necesita conocer antes de actuar.

## Regla nueva
Toda ronda futura que cambie objetivo, restricción, baseline, fuente, arquitectura, estado de ejecución o siguiente acción debe actualizar también `docs/ESTADO_MAESTRO_PROYECTO.md`.

## Estado
El repositorio se considera documentalmente autosuficiente para iniciar una sesión nueva, sujeto a que la sesión lea el Estado Maestro y los documentos indicados antes de modificar código. La siguiente acción sigue siendo inspeccionar y registrar GitHub Run #2 completo de R006.