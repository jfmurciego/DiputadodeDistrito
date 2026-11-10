# Núcleo único de reglas (T-137, motor 2 · fase 0)

Estado: propuesta para decidir (propietario + Planificador). Sin código de producción en esta PR.
Inventario de partida: `docs/ESTUDIOS/T137_NUCLEO_REGLAS/INVENTARIO_DIVERGENCIAS.md`.

## Objetivo

Una sola definición ejecutable de «plan válido» que usen la batería (T-132), los generadores del motor 2 y, tras el
relevo, la validación de producción. El motor 2 vive al lado (`ddd_motor2/`); M04/M05/`ddd_core` y sus huellas no se
tocan hasta que el propietario decida el relevo.

## Diseño

Paquete `ddd_motor2/reglas/`, Python puro (sin pandas, geopandas ni shapely; solo stdlib), dos capas:

1. **Datos declarativos** (`modelo.py`, dataclasses congeladas):
   - `Unidad(id, poblacion:int, municipio, particion, provincia, nucleo_cerrado:str|None)`: unidad atómica; la sección
     es una unidad trivial. Población entera (sin márgenes `1e-9`).
   - `Problema(unidades, aristas, puentes)`: grafo operativo; los `topology_bridges` son aristas declaradas aparte para
     poder informar de ellos.
   - `Reglas`: se construye **solo** con `Reglas.desde_contrato(cfg)`, que aplica una única precedencia y normalización
     (claves de partición/provincia normalizadas una vez) y **falla** si falta una razón (como `hard_limits`; sin
     0,80/1,75 por defecto). Campos: K, cuotas por provincia, suelo, techo, tolerancia, exenciones municipales y por
     partición, provincia única, disciplina municipal (campo, `max_mixed`), núcleos cerrados, contigüidad.
     Expone `huella()` (sha256 de su forma canónica) para que batería y evidencias digan con qué reglas se midió.
2. **Evaluador** (`evaluar.py`):
   - `evaluar(problema, reglas, asignacion) -> Informe`: completo; lista de `Violacion(regla, ambito, detalle)` con
     códigos estables (`R-POB-SUELO`, `R-POB-TECHO`, `R-K`, `R-PROV`, `R-CUOTA`, `R-CONTIG`, `R-ATOM`, `R-MUN-MIN`,
     `R-MUN-MAX`, `R-MUN-MIXTOS`, `R-NUCLEO`) y métricas no duras (desviación, fuera de tolerancia).
   - `Estado` incremental (poblaciones, municipios por distrito, mixtos) con `movimiento_valido(u, d0, d1)` y
     `aplicar(...)`: el camino caliente de los generadores (Flip/ReCom/recocido) consulta lo mismo que `evaluar`.
     Contigüidad incremental: BFS local del distrito origen.
   - Invariante comprobado por test: tras cualquier secuencia de `aplicar`, `Estado.violaciones() == evaluar(...)`.
3. **Adaptadores** (`adaptadores.py`, fuera del núcleo; aquí sí pandas/geopandas): de M03/M04/M05 al `Problema`, y
   `validar_ejecucion` → `evaluar` para compararlos en la batería.

Decisiones de criterio que **no** fija esta PR (opciones para el propietario):
- Tolerancia: (a) métrica, como VAL/GCP; (b) dura, como GCE.
- `max_mixed`: (a) del contrato en todas partes; (b) 1 fijo, como VAL.
- Defaults de provincia única: (a) obligatoria en el contrato (fallar si falta); (b) True; (c) False como VAL.
- Exención por partición en distritos con varias particiones: (a) basta una exenta; (b) todas; (c) la primera (VAL).

## Enumerador exacto (criterio del propietario: cadena solo donde el espacio es grande)

Donde el espacio de planes cabe (K≤3 o pocas unidades; p. ej. Álava, con cadena degenerada según
`ddd_ensemble/statistical_quality.py`: `unique_state_ratio<0,10` y `self_loop_rate>0,90`), se enumeran todos los
planes en vez de muestrear. No se rebajan umbrales de calidad ni se tocan tolerancias por territorio.

Qué usa del núcleo (la misma definición de plan válido, sin copia):
- `Problema` y `Reglas` tal cual; `evaluar` como veredicto final de cada plan enumerado.
- Poda durante la enumeración con predicados parciales del núcleo, que deben ser **monótonos** (si fallan en un
  plan parcial, fallan en todo plan que lo extienda): techo, contigüidad del bloque cerrado, provincia única,
  cuotas por provincia, R012 máx y mixtos, núcleos cerrados. Suelo y R012 mín solo se comprueban en distritos
  cerrados. El núcleo expone estos predicados (`podar(parcial)`) y un test comprueba que enumerador + poda dan el
  mismo conjunto que `evaluar` sobre fuerza bruta en problemas pequeños.
- Salida: número exacto de planes válidos y su lista (o huella) para la batería; la elección del oficial entre ellos
  es decisión de criterio aparte.

Umbral entre cadena y enumeración (opciones para decidir; T-136 mide cuántos planes válidos hay en Álava):
- (a) **Por tamaño a priori**: K≤3 o nº de unidades ≤ N. Simple; no garantiza que la enumeración termine.
- (b) **Por cota del espacio**: contar particiones conexas (p. ej. cota superior por enumeración con presupuesto
  de nodos); enumerar si se completa dentro del presupuesto, si no, cadena.
- (c) **Por diagnóstico de la cadena**: correr la cadena y, si sale degenerada con los umbrales actuales de
  `statistical_quality`, pasar a enumeración. Usa evidencia ya existente, pero gasta la cadena primero.
- Evidencia que hace falta antes de fijarlo: recuento exacto de T-136 en Álava y tiempo de enumeración frente a
  tamaño en los territorios pequeños de la batería.

## Migración sin invalidar huellas

1. **F0 (esta tarea)**: documento + inventario.
2. **F1**: `ddd_motor2/reglas/` + tests unitarios con planes sintéticos de cada divergencia del inventario; sin
   importarlo desde producción. Huellas intactas.
3. **F2 · sombra**: la batería T-132 evalúa cada plan con VAL **y** con el núcleo; un informe de discrepancias por
   territorio (71). Toda discrepancia se explica por una decisión de criterio o se corrige en el núcleo.
4. **F3**: los generadores del motor 2 usan solo el núcleo. GCP/GCE/CAN siguen como están.
5. **F4 · relevo** (decide el propietario): `validar_ejecucion` llama al núcleo con versión nueva y legacy; las
   huellas M05 no cambian porque no se toca M05; la 00 de comprobación será «Generar desde fuente».

## Riesgos

- **Cambio silencioso del veredicto**: fijar una opción (p. ej. tolerancia dura) cambia PASS/FAIL históricos. Mitiga
  F2: ningún relevo con discrepancias sin explicar.
- **Rendimiento**: el evaluador puro debe igualar a GerryChain en el camino caliente; medir en Madrid/Barcelona
  (mayor K) antes de F3.
- **Puentes topológicos**: hoy el ensemble no los admite; el núcleo los modela, pero el generador debe respetarlos.
- **Copias que reaparecen**: regla de revisión: ningún módulo nuevo define suelo/techo/R012; un test busca
  `population_floor_ratio` fuera de `ddd_motor2/reglas/` y de los módulos de producción congelados.
- **Datos de entrada**: el formato de `ddd_unit_id` no se interpreta; el municipio va como campo de la unidad
  (corrige la divergencia 4).
