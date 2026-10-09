# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.6.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.5.0.md`

## 1. Regla de arranque
Leer este documento; `docs/BITACORA.md`; arquitectura; contratos `docs/MODULOS/`; configuración; última ronda; última ejecución; workflow.

## 2. Objetivo
Procedimiento de Distritación DDD reproducible, auditable y generalizable. Aragón primero; después Castilla y León, Extremadura y España completa por configuración/datos, sin forks del motor.

## 3. Arquitectura
M01 secciones+población; M02 adyacencias; M03 grafo; M04 construcción inicial; M05 optimización; M06 consolidación; M07 agregación electoral; M08 producto final. M01-M03 son preparación reutilizable; M04-M06 núcleo territorial; M07-M08 capa electoral desacoplada.

## 4. Reglas duras Aragón — R012
1. 67 distritos exactos.
2. Contigüidad estricta por grafo.
3. Conservación exacta de secciones y población.
4. Suelo 0,80×target y techo 1,75×target.
5. Provincia como frontera dura: ningún distrito puede cruzar provincia.
6. Reparto provincial: Huesca 11, Teruel 7, Zaragoza 49.
7. Municipio que cabe en un distrito: indivisible.
8. Municipio grande: se divide internamente en bloques contiguos; todos salvo como máximo el residual deben permanecer exclusivamente municipales.
9. Solo el residual urbano puede completarse con municipios menores adyacentes de la misma provincia.
10. CUSEC único/no nulo; determinismo; resultados electorales no condicionan geometría.

## 5. Estatus de Run #5
Run #5 `34584775443` sigue siendo evidencia válida de R011 y de publicación completa de outputs, pero no es referencia territorial R012. La auditoría detectó cruces provinciales y fragmentaciones municipales que ahora son invalidantes.

## 6. Implementación vigente R012
Configuración: `configuracion/aragon_2025.yaml` v7.4.0. Validación: `herramientas/validar_ejecucion.py` v1.3.0.

### M04 v7.2.0 — Provincia primero y disciplina municipal
- Construye cada provincia de forma independiente.
- Respeta las cuotas 11/7/49 desde el nacimiento de la solución.
- Agrupa secciones en `ddd_unit_id`.
- Municipios no sobredimensionados: una unidad atómica municipal.
- Municipios grandes: bloques internos contiguos y residual.
- Los bloques urbanos completos se etiquetan mediante `ddd_closed_urban` y forman distritos cerrados.
- Solo distritos no cerrados pueden absorber unidades de municipios menores.

### M05 v7.2.0 — Optimización por unidades territoriales protegidas
- Ya no mueve secciones individuales.
- Mueve únicamente `ddd_unit_id` completos.
- No permite cambios entre provincias.
- No abre ni modifica distritos urbanos cerrados.
- Comprueba contigüidad de donante y receptor después de cada movimiento.
- Prioridad: restricciones duras; después número de distritos fuera de ±12%; máximo desvío y error cuadrático.

Versiones anteriores preservadas en `legacy/modulo04/04_generar_semillas_v7.0.1.py` y `legacy/modulo05/05_optimizar_distritos_v7.1.0.py`.

## 7. Puerta de aceptación siguiente
La siguiente ejecución debe demostrar simultáneamente:
- 67 distritos;
- cuotas provinciales exactas 11/7/49;
- cero cruces provinciales;
- cero fragmentaciones indebidas de municipios pequeños/medios;
- como máximo un distrito mixto por municipio grande dividido;
- contigüidad estricta;
- conservación de las 1.463 secciones y 1.364.621 habitantes;
- suelo/techo poblacional;
- medir cuántos distritos quedan fuera de ±12%.

No se considerará regresión si una primera ejecución R012 falla población pero elimina cruces/fragmentaciones: esa ejecución servirá para localizar el siguiente defecto algorítmico. No se promocionará como referencia hasta cumplir todas las puertas duras.

## 8. Outputs y auditoría
R011 permanece vigente: cada módulo debe exponer el producto completo. M04/M05 deben permitir auditar `ddd_unit_id`, `ddd_closed_urban`, provincia, municipio, población y distrito antes/después.

## 9. Siguiente acción exacta
Ejecutar el workflow en modo `iterativo` con M04/M05 v7.2.0. M01-M03 deben restaurarse desde caché. Después auditar inmediatamente M04 y M05 para comprobar primero estructura provincial/municipal y después equilibrio poblacional. Si falla, corregir únicamente el módulo responsable, preservando esta baseline R012.
