# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.4.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.3.0.md`

## 1. Regla de arranque
Leer este documento; `docs/BITACORA.md`; `docs/ARQUITECTURA_DEL_PROCEDIMIENTO.md`; los ocho contratos de `docs/MODULOS/`; configuración; última ronda; última ejecución; workflow.

## 2. Objetivo
Procedimiento de Distritación DDD reproducible, auditable y generalizable. Aragón es la primera implantación; Castilla y León, Extremadura y España completa deben entrar por datos/configuración, no mediante forks del motor.

## 3. Arquitectura
M01 secciones+población; M02 adyacencias; M03 grafo; M04 solución inicial; M05 optimización; M06 consolidación territorial; M07 agregación electoral; M08 producto final. M01-M03 son preparación reutilizable; M04-M06 núcleo iterativo; M07-M08 capa electoral desacoplada.

## 4. Restricciones Aragón
67 distritos exactos; contigüidad estricta por grafo; target=población/67; suelo 0,80×target; techo 1,75×target; objetivo histórico ±0,12; split máximo 3 donde aplique; CUSEC único/no nulo; conservación de población; determinismo; resultados electorales no condicionan geometría.

## 5. Referencia vigente demostrada
GitHub Run #5 `34584775443`, run id `gh-34584775443-1`, commit ejecutado `518e3324b028d5ac03ca28246696b9b39660f869`: workflow y publicación R011 PASS.

Validación:
- 67 distritos;
- 1.463 secciones;
- población 1.364.621;
- target 20.367,48;
- suelo 16.293,98;
- techo 35.643,09;
- 0 bajo suelo;
- 0 sobre techo;
- 0 desconectados.

M01-M03 fueron reutilizados desde la preparación territorial cacheada; M04-M08 se ejecutaron. Se materializaron outputs auditables M01-M08, ocho artefactos independientes y la carpeta Git `resultados/ejecuciones/gh-34584775443-1/`.

## 6. Regla de producto por módulo
Ningún módulo puede quedar representado únicamente por un log, contador o informe. Debe existir el estado completo producido y debe poder auditarse. Las estructuras ligeras completas se publican en Git; las geometrías pesadas se preservan como artefactos de Actions con hashes registrados en `PRODUCTOS.json`.

## 7. Auditoría territorial del Run #5
Documento canónico: `docs/AUDITORIAS/AUDITORIA_TERRITORIAL_RUN5_2026-09-11.md`.

### Calidad poblacional
- 65 de 67 distritos están dentro de ±12% del target.
- Solo distrito 16: 27.255 habitantes, +33,82%.
- Solo distrito 37: 27.220 habitantes, +33,64%.
- Ambos pertenecen exclusivamente a Teruel.

### Calidad territorial
- 13 distritos cruzan fronteras provinciales.
- 2 distritos contienen secciones de Huesca, Teruel y Zaragoza.
- distrito 64: 4.771,16 km², 78 municipios, Polsby-Popper ~0,0412.
- distrito 13: 3.364,07 km² y 69 municipios.
- distrito 30: 2.640,49 km² y 67 municipios.
- mínimo Polsby-Popper ~0,0412; mediana ~0,1315.
- 30 municipios aparecen repartidos entre más de un distrito. Zaragoza alcanza 40 distritos; Huesca 5; Barbastro, Monzón y Utebo 3. Las divisiones necesarias deben distinguirse de las fragmentaciones evitables.

Conclusión: el motor ya produce una solución legal y contigua, pero todavía no una solución territorialmente final. Población correcta no equivale a calidad territorial.

## 8. Dirección de M05
M05 v7.1.0 debe evolucionar de objetivo casi exclusivamente poblacional a **optimización multiobjetivo territorial**.

Jerarquía prevista:

### A — restricciones duras
1. 67 distritos exactos.
2. Contigüidad estricta.
3. Conservación de población/secciones.
4. Suelo 0,80×target.
5. Techo 1,75×target.

### B — equilibrio poblacional
6. Llevar todos los distritos a ±12% cuando sea factible.
7. Atacar prioritariamente los distritos 16 y 37 sin degradar los 65 ya conformes.

### C — calidad territorial
La función de coste debe incorporar de forma parametrizable, distinguiendo restricciones y penalizaciones:
- cruces provinciales;
- fragmentación municipal evitable;
- número excesivo de municipios;
- compacidad;
- superficie/anomalías territoriales;
- posteriormente coherencia comarcal y urbana con fuentes explícitas.

No se deben aumentar iteraciones aleatorias como sustituto de una función objetivo territorial correcta.

## 9. Contrato rico de distrito
M06 debe evolucionar hacia una ficha territorial completa. Ya incluye población, target, desviación, límites, secciones, municipios, provincias, superficie, perímetro, compacidad, centroide y bounding box. Debe incorporar progresivamente, con fuentes verificables: peso poblacional por provincia, municipio dominante, municipios completos/fragmentados, comarcas, cabecera, densidad, carácter urbano/rural, vecinos distritales e indicadores de integridad administrativa.

## 10. Fuentes
Desarrollo: ZIP canónicos reconstruidos desde `inputs/partes/`. Hash seccionado `55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4`; población `91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3`. Validación/certificación final: adquisición directa INE de R006.

## 11. Concurrencia y rendimiento
Solo `preparar-territorio` está serializado. M04-M08 pueden correr concurrentemente. M01-M03 se cachean y las ejecuciones iterativas referencian/reutilizan la preparación vigente.

## 12. Diferencias históricas abiertas
Persisten como arqueología la población antigua 1.358.812 frente a 1.364.621 actual y la referencia histórica ~4.302 aristas frente a 4.293 reproducibles. No se ocultan ni bloquean la referencia vigente.

## 13. Siguiente acción exacta
Diseñar R012 antes de modificar código: formalizar métricas de integridad provincial y municipal, definir qué cruces/fragmentaciones son duros, cuáles fuertemente penalizados y cuáles admisibles, y diseñar la estrategia dirigida para resolver los distritos 16 y 37 sin romper los 65 ya dentro de ±12%. Después implementar M05 siguiente versión, preservando v7.1.0.
