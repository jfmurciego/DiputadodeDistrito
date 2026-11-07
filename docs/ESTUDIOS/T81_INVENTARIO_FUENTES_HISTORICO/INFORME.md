# T-81 · Inventario de fuentes del histórico de generales 2011-2023 (D-9, D-11)

Datos: `orchestracion/inventario_fuentes_historico.json` (generado por `herramientas/inventario_fuentes_historico.py`, sin red,
a partir del manifiesto T-89 y los contratos de Infoelectoral). Por elección y provincia (52): fuente, fecha, sha256, cobertura.

| Elección | Fecha | Observatorio (datos + geometría) | Infoelectoral por mesa | Oficial local (contraste) |
|---|---|---|---|---|
| 2011-11 | 2011-11-20 | 52/52 (seccionado 2012) | no adquirida | no hay: AVISO |
| 2015-12 | 2015-12-20 | 52/52 (2015) | no adquirida | no hay: AVISO |
| 2016-06 | 2016-06-26 | 52/52 (2016) | no adquirida | no hay: AVISO |
| 2019-04 | 2019-04-28 | 52/52 (2019) | no adquirida | no hay: AVISO |
| 2019-11 | 2019-11-10 | 52/52 (2020) | no adquirida | BOE-A-2019-18147: 256 comparaciones, defecto máx. 3,1 %, 0 errores |
| 2023-07 | 2023-07-23 | 52/52 (2024) | 52/52 en el release `fuente-infoelectoral-02202307` (sha256 e78fc231…1717f8) | BOE-A-2023-18907: 197 comparaciones, defecto máx. 7,4 %, 0 errores |

## Lectura
- **Única fuente histórica completa hoy**: el Observatorio (6 × 52 ficheros de datos y 6 × 52 de geometría, sha256 en el manifiesto). Fecha de espejo 2026-11-07; la copia en R2 (`fuentes/nazioenbehatokia/`) está pendiente de subir por el Operador.
- **Infoelectoral**: solo 2023-07 está adquirida (espejo en release). Para 2011-2019 no tenemos ZIP ni sha256 y Interior rechaza runners y sesión cloud: hay que bajarlos desde un equipo con acceso y espejarlos como el de 2023 antes de contrastar por mesa.
- **Seccionado INE**: el catálogo oficial solo trae la edición vigente (OGC). Las ediciones históricas (2012, 2015, 2016, 2019, 2020, 2024) no están adquiridas; hoy la geometría histórica viene solo del Observatorio, sin contraste.
- **Sin contraste oficial local (AVISO)**: 2011-11, 2015-12, 2016-06 y 2019-04. Falta el BOE de cada resolución de la JEC (mismo patrón que BOE-A-2019-18147).
- El contraste existente es agregado por partido-provincia; el defecto es el voto CERA, no incluido por sección.
- **Cobertura por sección** (`secciones`): `null`; los ficheros de datos no están en git (R2), así que el recuento de secciones por provincia queda pendiente de la subida.
- Limitación: no he verificado en línea que el Observatorio siga sirviendo estos ficheros; el inventario refleja lo ya espejado.

## Siguiente (sin encargar, plan: histórico aplazado)
1. Descargar y espejar los ZIP de Infoelectoral 2011-2019 con sha256. 2. Incorporar los BOE de 2011, 2015, 2016 y 2019-04. 3. Adquirir los seccionados INE históricos. 4. Subir el espejo a R2 y rellenar `secciones`.
