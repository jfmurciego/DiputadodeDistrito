# C-13 — Alcance de comunidades de interés

Versión: 1.0.1  
Fecha: 2026-09-13  
Estado: cerrado y certificado en CI 34786528440.  
Anterior: `legacy/docs/AUDITORIA_C13_COMUNIDADES_INTERES_v1.0.0.md`.

## Decisión

Las comunidades de interés pasan a ser un criterio formal supra-municipal de
publicabilidad. La disciplina municipal ya pertenece a P04 y no puede contarse
de nuevo como prueba de P07. La unidad admisible es una comarca o un equivalente
funcional declarado con fuente pública, identidad estable, fecha, condiciones
de reutilización y cobertura municipal completa.

El criterio es neutral ex ante: no puede usar votos, partidos ni resultados
electorales para definir comunidades o umbrales.

## Medición obligatoria

El contrato `configuracion/comunidades_interes.json` fija cuatro salidas:

1. comunidades partidas entre distritos;
2. comunidades representadas por distrito;
3. peso poblacional de la comunidad dominante por distrito;
4. retención poblacional en el distrito modal de cada comunidad.

Antes de cualquier ejecución territorial deben declararse el máximo de
comunidades partidas, el mínimo de retención y el tratamiento de divisiones
inevitables. Fijarlos después de observar un mapa queda prohibido.

## Estado de la evidencia existente

Aragón y Castilla y León contienen rutas de comarca con `enabled: false`; no
existe evidencia de incorporación al universo M01 ni medición en M06.
Extremadura no declara fuente. Los tres territorios quedan `NOT_EVALUABLE` en
P07, estado que bloquea publicación igual que un fallo.

No se infieren comarcas desde nombres o geometría, no se cambian límites y no se
ejecuta M01–M06. Reincorporar una fuente concreta será una decisión territorial
posterior y requerirá orden expresa.

El commit `5a4a884` supera la suite general `34786528440`, único workflow
activado. No se ejecutó ninguna regresión territorial.
