# T-418 · Doble vuelta desde R2 (opción nueva de P70 Archivo) — diseño corto

VERSIÓN: 1.0.0 · FECHA: 2026-11-19 · ESTADO: propuesta · ANTERIOR: ninguna (fichero nuevo)

Objetivo (D-178/D-179, prioridad V4): sin regenerar, calcular dv_base, dv_A y dv_B de los 52 territorios del Congreso (`nac`) a partir de lo que
ya está en R2 y dejar los datos que lee la V4 (T-413 §5). Solo lectura sobre git; solo escribe objetos nuevos en R2. No lanza ni publica.

## 1. Opción en el botón (D-129/D-130)
Una acción más en `accion` de `p70-archivo.yml` (una familia, opciones dentro): **«P75 Doble vuelta desde R2»**. Sin entradas nuevas:
`territorios` (vacío = los 52 `nac`) y `eleccion` (vacío = 2023-07), que ya existen. Los 19 `aut` quedan fuera (tabla de bloques solo de generales).
Job nuevo `doble_vuelta_r2`, un solo job que recorre los territorios en serie (≈ 85 MB en total; sin matriz). Grupo de concurrencia
`archivar-artefactos-r2` (único escritor en R2). Permisos `contents: read`; sin entorno `produccion` (no borra nada).

## 2. Por territorio
1. Run = el `canonical_m08` más reciente de `publicaciones_visor.json` (como `p70_resolver.py`).
2. Baja `ddd-minimo-<run>-M08.zip` de R2 y comprueba su sha256 contra `orchestracion/archivo_r2.json`; si no coincide, el territorio falla (sin reintentos de datos).
3. Lee `MANIFEST_MINIMO.json` y **informa** de si trae `…_m07_resultados_partido.csv` (sí/no por territorio). Sin él: no se calcula, se lista (nunca reconstruir votos).
4. Comprueba que la elección del paquete es la pedida (`electoral_package_election_id` del `CHAIN_STATE`/`production_status`; la lleva el estado, no `publicaciones_visor.json`).
5. Ejecuta `doble_vuelta.py --alias … --detalle …` (+ `doble_vuelta_cobertura.py`, #915) con la tabla de bloques y el alias de `main`.
6. Sube la salida a R2 y anota su sha256.

## 3. Salidas
- R2: `<territorio>/<run>/ddd-doble-vuelta-<run>.zip` (los 4 ficheros: `doble_vuelta.csv`, `detalle.csv`, `cobertura.json`, `manifiesto.json`) y `doble_vuelta/<eleccion>/INFORME.json`
  con una fila por territorio (run, sha256 del paquete de entrada y de salida, `trae_m07`, % sin casar, estado). Es la fuente de la V4 (T-413 §5).
- Resumen del job (tabla legible) y artefacto del run (14 días) con el mismo informe.
- Criterio de hecho: 52/52 calculados o los restos listados uno a uno con causa.

## 4. Archivos compartidos y pruebas
`.github/workflows/p70-archivo.yml` (turno exclusivo; copia 1.0.0 en `legacy/workflows/`), `tests/test_t368_p70_equivalencia.py` (fija las opciones de P70:
se amplía con la nueva y se comprueba que las demás acciones no cambian). Nuevos: `herramientas/p75_doble_vuelta_r2.py` (núcleo sin red con el cliente de
`archivar_artefactos_r2.py` inyectable) y `tests/test_t418_p75.py` con R2 simulado: sha256 distinto, paquete sin CSV, elección distinta, éxito, determinismo.
No toca `modulos/`, `doble_vuelta.py` ni el visor. PR única `no-automerge`.

## 5. Decisiones que no se deducen (con recomendación)
1. **Registro**: ¿anotar el paquete nuevo en `archivo_r2.json` (commit con la app de registro, no es solo lectura) o solo en R2 (`INFORME.json`)?
   Recomiendo solo R2 ahora; el publicador P40 de la V4 deja el sha256 en git.
2. **Numeración de distritos**: M07 escribe `district_id` 0..K-1 y lo público es 1..K (`numeracion_publica`, T-135). Recomiendo guardar el valor interno
   y que el publicador de la V4 convierta (como con los GeoJSON).
3. **Formato del detalle**: el de #907 (`district_id, escenario, candidatura, partido, bloque, votos_1v, votos_candidatura`) frente al de T-413 §5
   (`…, destino, votos_transferidos`). Recomiendo el de #907 (ya en main) y que T-413 lo adopte; la transferencia ya está en el CSV principal.
4. **Sin el CSV en el paquete**: si algún territorio no lo trae, ¿regenerar con P30 solo esos? Recomiendo sí, solo esos y tras el 29-11 con T-313.
