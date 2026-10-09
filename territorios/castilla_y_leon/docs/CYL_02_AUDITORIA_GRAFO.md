# CYL-02 — Auditoría del grafo territorial de Castilla y León

**Fecha:** 2026-09-11
**Estado:** diagnóstico reproducible obtenido; reparación topológica candidata pendiente de aceptación final

## 1. Ejecución de diagnóstico

GitHub Run `34608550741` ejecutó M01-M03 de forma reproducible sobre Castilla y León.

Resultado base antes de puentes topológicos:
- M01: 3.506 secciones; 0 población ausente; 2.401.221 habitantes.
- M02: 10.392 aristas geométricas (`touches`).
- M03: 3.506 nodos; 10.392 aristas; 2 nodos globalmente aislados.

## 2. Componentes por provincia antes de reparar

| Provincia | Secciones | Componentes | Tamaños |
|---|---:|---:|---|
| Ávila | 308 | 1 | 308 |
| Burgos | 577 | 4 | 573 + 2 + 1 + 1 |
| León | 444 | 1 | 444 |
| Palencia | 273 | 3 | 271 + 1 + 1 |
| Salamanca | 530 | 1 | 530 |
| Segovia | 276 | 1 | 276 |
| Soria | 218 | 1 | 218 |
| Valladolid | 565 | 2 | 563 + 2 |
| Zamora | 315 | 1 | 315 |

## 3. Componentes desconectados identificados

### Burgos

1. `0910901001` Condado de Treviño + `0927601001` La Puebla de Arganzón.
   - Componente de dos secciones.
   - Es el enclave de Treviño: territorio burgalés rodeado por Álava.
   - No puede tocar geométricamente el cuerpo principal de Burgos sin atravesar otra provincia/comunidad.
   - Puente elegido: `0910901001` → `0921904001` (Miranda de Ebro), sección del cuerpo principal burgalés más próxima; distancia geométrica aproximada 5.483 m.

2. `0915401001` Hacinas.
   - Nodo aislado en el seccionado usado por M02.
   - No es un enclave provincial; la geometría queda separada unos 622 m de `0933001001` Salas de los Infantes.
   - Se clasifica como `cartographic_gap`.
   - Puente: `0915401001` → `0933001001`.

3. `0922301001` Monasterio de la Sierra.
   - Nodo aislado en el seccionado usado por M02.
   - No es un enclave provincial; distancia aproximada 758 m a `0941401001` Valle de Valdelaguna.
   - Se clasifica como `cartographic_gap`.
   - Puente: `0922301001` → `0941401001`.

### Palencia

1. `3403201001` Berzosilla.
   - Exclave provincial palentino separado del cuerpo principal.
   - Toca geométricamente secciones de Burgos, pero la provincia se considera barrera administrativa.
   - Puente mínimo al cuerpo principal palentino: `3403201001` → `3413501001` Pomar de Valdivia; distancia aproximada 2.766 m.

2. `3424201001` Villodrigo.
   - Exclave palentino dentro de Burgos.
   - Toca secciones burgalesas pero no el cuerpo principal de Palencia.
   - Puente mínimo: `3424201001` → `3412101001` Palenzuela; distancia aproximada 1.725 m.

### Valladolid

`4713401001` Roales de Campos + `4712801001` Quintanilla del Molar.
- Componente vallisoletano de dos secciones separado del cuerpo principal y rodeado por territorio de León/Zamora.
- Puente mínimo: `4713401001` → `4718301001` Valdunquillo; distancia aproximada 3.873 m.

## 4. Decisión de arquitectura

No se usará un `buffer` global para forzar contactos. Eso podría crear adyacencias falsas en cualquier parte del territorio.

M02 v7.1.0 incorpora un mecanismo **genérico y configurable** `topology_bridges`:
- cada puente es explícito;
- ambos CUSEC deben existir;
- queda marcado en el JSONL con `edge_type`, `reason` y `source`;
- si el territorio no declara puentes, M02 conserva el comportamiento geométrico anterior;
- no existe ningún `if castilla_y_leon` en el motor.

Regla adoptada: un único puente mínimo por componente desconectado hacia el cuerpo principal de la misma provincia. El puente expresa conectividad administrativa/topológica para el algoritmo; **no modifica la geometría oficial ni afirma contacto físico**.

## 5. Criterio de aceptación CYL-02

La siguiente ejecución debe mantener:
- 3.506 nodos;
- población 2.401.221;
- ninguna sección perdida;
- M02 geométrico reproducible;
- exactamente 6 puentes configurados;
- 0 nodos aislados;
- exactamente 1 componente de grafo dentro de cada una de las nueve provincias;
- regresión Aragón R015/R016 verde.

Solo después de estos PASS puede cerrarse M03 y empezar a definir el contrato de M04.
