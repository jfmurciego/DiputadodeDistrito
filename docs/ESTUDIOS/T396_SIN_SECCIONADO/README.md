# T-396 · Secciones con población sin geometría en el seccionado del año (D-153)

Resuelve el bloqueo §5.1 de T-365. Regla (herramienta `herramientas/contrato_historico_epoca.py` 1.1.0, contratos 1.2.0):

1. Sección con población en la tabla y sin geometría en el seccionado del año → se busca su geometría en el seccionado más cercano en años que la tenga
   (empate: el anterior). Donantes con sha256 acreditado: Censo 2011 (`cartografia_censo2011_nacional.zip`, T-357) y seccionados 2012, 2015, 2016, 2019-2022
   (T-357/T-364b). El Censo 2011 es el universo de la tabla de 2011-11: las 43 secciones sin geometría de 2015-2022 están todas ahí.
2. Se localiza el **centroide** (punto representativo si cae fuera de todas) en el seccionado del año: esa es la sucesora.
3. Sucesora de la misma provincia → **asignada** (su población se suma a la sucesora; origen `dato` si ambas lo eran, `reasignada` si alguna era estimada,
   que cuenta como estimada en el umbral del 1 %). Sucesora de otra provincia → provincia **APARTADA** (no se genera).
   Sin geometría en ningún año, punto fuera del seccionado o sucesora sin fila en la tabla → **excluida**, con su población declarada.
4. Todo queda en el contrato (`provincias.<c>.poblacion.sin_seccionado_resuelto`: asignadas con sucesora y año del donante, excluidas con motivo,
   habitantes); `materializar` solo aplica lo declarado y falla cerrado si la tabla no coincide. `secciones_sin_seccionado` queda con las sin resolver.

Informe por provincia, derivado de los contratos: `informe_sin_seccionado.csv` (`python herramientas/contrato_historico_epoca.py informe`).

## Resultado sobre los contratos de `main` (#865)

- 2015-12, 2016-06, 2019-04 y 2019-11 ya no tenían secciones sin seccionado (T-364b las reasigna al construir la tabla): sus contratos solo cambian de versión.
- 2011-11 (la tabla del Censo no usa seccionado): 44 secciones en 13 provincias → 42 asignadas (todas con el Censo 2011 como donante) y 2 excluidas
  (la sucesora no tiene fila en la tabla: 0804702003 → 0804703001 y 3501602060 → 3501603042). Habitantes en el CSV; ninguna provincia APARTADA.
  Los 52 siguen LISTA; `materializar` ya no falla por «población sin geometría» en ninguna.

## Pendiente, fuera de T-396

2011-11: 11 de las 13 provincias (08, 15, 21, 22, 24, 27, 32, 33, 35, 36, 46) siguen fallando en `materializar` por el caso contrario, **secciones del seccionado 2012
sin población** (105 en total en el país: la tabla del Censo no las tiene, p. ej. 0804703001), `CASADO_POBLACION_SECCIONADO … sin población`. Solo 03 y 12 materializan.
Necesita una regla propia (decisión del Planificador). Reproducción: `bajar_fuentes.sh` + `--donantes` con los ZIP de seccionados y el Censo 2011.
