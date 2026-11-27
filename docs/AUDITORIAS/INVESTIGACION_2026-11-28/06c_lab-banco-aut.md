<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 0.1.0
NOMBRE DE VERSIÓN: Investigación T-509 · ámbito 06c · laboratorio del banco, autonómicas (esqueleto)
FECHA: 2026-11-28
ESTADO: DOCUMENTO DE TRABAJO de la investigación T-509. No es el plan; no autoriza lanzar ni publicar nada
CAMBIOS: 0.1.0 — esqueleto (primer empuje)
MOTIVO: orden del propietario (28-11): banco de comparación completo con el motor 1.2 para aut01–aut19
ANTERIOR: ninguna (fichero nuevo)
-->

# 06c · Laboratorio del banco — autonómicas (aut01–aut19)

Estado: **esqueleto**. Empezado el 27-11 a las 23:42Z. Código de `main` 62387488 (Deslinde 1.2) + protocolo 9e630d11.
Sesión cloud, 4 núcleos y 15 GB. No se lanza ni se publica nada: todo es cálculo local.

## Diseño (heredado de T-465, `docs/ESTUDIOS/T465_BANCO_PILOTO/DISENO.md`)

- Tramo: aut01 a aut19. La Comunidad de Madrid (aut13) no se adquiere en la nube: marcada, sin medir.
- Entradas: `bateria_motor.py entradas --desde-fuente --seccionado shapefile` con los seccionados del INE verificados
  por sha256 contra `orchestracion/fuentes_r2.json`.
- Métodos, con el mismo problema, los mismos átomos y la misma clave D8 (`Natural.clave("D8")`):
  1. Deslinde 1.2: `python -m ddd_motor2.competir` (competición local por defecto).
  2. GerryChain puro: ReCom sobre átomos, 10⁴ pasos, varias semillas públicas.
  3. Exacto (CP-SAT): solo donde quepa; límite de 10 minutos por territorio. Donde no cierre, cota.
- Orden: de menor a mayor tamaño. Se llega hasta donde dé el tiempo (fase 1 acaba a las 02:15Z).

## Tabla por territorio

Pendiente (se rellena con `resultados/RESUMEN.json`).

| Territorio | K | Clave D8 de Deslinde | Mejor de GerryChain (10⁴) | Óptimo o cota | Tiempos | Quién gana |
|---|---|---|---|---|---|---|

## Hallazgos

Pendiente.

## Lo que no pude comprobar

Pendiente.

## Objeciones

Pendiente.
