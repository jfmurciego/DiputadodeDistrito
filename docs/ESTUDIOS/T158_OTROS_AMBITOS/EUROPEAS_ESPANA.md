# Europeas (España) · nota de preparación (T-158)

Fecha de consulta: 2026-11-10. Estado: PREPARACIÓN.

## 1. Sistema vigente y norma (verificado en LOREG, BOE-A-1985-11672; sha256 en `README.md`)
- Art. 214 (añadido por LO 1/1987): la circunscripción es **el territorio nacional**.
- Art. 215 (redacción LO 16/2003): el número de diputados que se elige en España se fija según el ordenamiento jurídico europeo (versiones históricas: 60 y 64). El valor de la legislatura vigente (61 desde 2024) y su acto de origen (Decisión (UE) 2023/2061 del Consejo Europeo) **NO VERIFICADO**: EUR-Lex no es alcanzable.
- Art. 216: reparto por el art. 163 (D'Hondt) **sin la barrera del 3 %** (excepción del apartado 1.a) ni el apartado 2).
- Art. 217: vacantes cubiertas por el siguiente de la lista.
- Listas cerradas y bloqueadas con paridad (art. 44 bis): citada en el texto consolidado.

## 2. Qué sería un «distrito uninominal»
Circunscripción única nacional con K = escaños de España (61 según lo anterior, a verificar). Equivale a trazar K distritos
continuos en el país entero (con islas y Ceuta/Melilla como problema aparte) o a respetar la partición provincial con K
desigual por provincia (decisión de diseño). Es la versión más cercana al módulo nacional existente (Congreso con 52 provincias, 350 escaños; ver T-102): mismo seccionado, mismo padrón, otra K y sin barrera de provincia.

## 3. Unidades y cartografía
Las mismas que el Congreso: 36.554 secciones censales INE 2025 (ENTREGA.md de FUENTES_NACIONALES_INE_2025). Nada nuevo que adquirir.
Ceuta, Melilla y las islas no son contiguas: ya se tratan en el contrato nacional (aristas virtuales/enclaves; ver `docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012`).

## 4. Población oficial
La que ya usa el contrato nacional (INE, padrón 2025 por sección; suma 49.128.297 según ENTREGA.md). En europeas votan además residentes ausentes (CERA) y ciudadanos de la UE residentes en España que lo soliciten (art. 210): el censo electoral difiere del padrón.

## 5. Resultados por sección y licencia
- España: Interior (Infoelectoral) publica resultados por mesa de las europeas; **no alcanzable** desde la nube. Las europeas 2024-06 serían el equivalente de 2023-07 en el espejo del release `fuente-infoelectoral-02202307`; habría que crear otro espejo con un ZIP que el propietario descargue.
- Europa: results.elections.europa.eu y el Parlamento Europeo publican solo agregados por Estado; **no alcanzables**; no aportan sección.
- Licencia: NO VERIFICADO.

## 6. Reglas del núcleo a parametrizar
- **Partición dura**: hoy provincia; aquí «ninguna» (una sola unidad nacional) o provincia con K asignado. Es la parametrización más importante: el motor actual da por supuesto el ámbito provincial (CPRO) en M04/M05.
- **K**: K = 61 fijo por norma; reparto entre provincias solo si se mantiene la partición provincial (entonces habría que decidir el método de reparto, no está en la norma).
- **Techo/suelo**: población objetivo = 49,1 M / 61 ≈ 805.000 hab. por distrito; el techo de ratio actual (pensado para ~140.000) cambia el tamaño del problema en un orden de magnitud (≈ 600 secciones por distrito). Posible cuello de botella de rendimiento en M05.
- **Atomicidad**: la sección sigue valiendo (muy inferior al distrito).
- Escala de cómputo: un único territorio de 36.554 unidades en un solo problema; hoy se resuelve por provincia (≤ ~3.500 secciones). Riesgo de tiempo/memoria.

## 7. Huecos y riesgos
1. Número de escaños y acto europeo sin verificar. 2. Resultados por mesa no alcanzables. 3. Tamaño del grafo único.
4. Sentido político de un «distrito» europeo con 805.000 habitantes (decisión del propietario; no se estudia).
5. Censo electoral ≠ padrón (CERA, ciudadanos UE).

## 8. Esfuerzo (estimación)
Bajo-medio: 4-6 tareas (contrato nacional sin partición provincial, política, escalado de M05, espejo de resultados 2024, validación). Si se mantiene la partición provincial con K por provincia: 2-3 tareas más una decisión de reparto. Depende de que el motor soporte el problema nacional único.
