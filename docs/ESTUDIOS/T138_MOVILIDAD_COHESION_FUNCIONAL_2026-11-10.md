# T-138 · Nota de viabilidad: movilidad como cohesión funcional (2026-11-10)

Solo documentación. Evidencia descargada de `www.ine.es` desde la sesión cloud (huellas abajo). No fija pesos: eso es del propietario con el Planificador.

## 1. Conjuntos y cuál sirve
| Conjunto | Qué es | ¿Sirve? |
|---|---|---|
| EM-1 (piloto 2019, datos a mar-2020) | Flujos O-D entre áreas de movilidad, telefonía móvil | Sí, como base (día laborable típico) |
| EM-2/3/4 (2020-2021, miércoles y domingos hasta dic-2021; estacional) | Misma estructura, series largas | Sí, pero años COVID: sesgo |
| Descripción de áreas (1-ene 2019/2020/2021) | Tabla municipio/sección/distrito → grupo (área) y población | Imprescindible (clave de unión) |
| Censo 2021: lugar de trabajo/estudio | Municipio de trabajo desde el archivo censal (origen Padrón) | **No verificado** que haya matriz O-D municipal descargable; ver §3 |
| ECEPOV 2021 «Movilidad cotidiana» | Encuesta muestral, municipios >50.000 y capitales | No: muestral y sin matriz |
| MITMA/Transportes (Open Data Movilidad) | Matrices por distrito/municipio, diarias | Mejor resolución, pero `transportes.gob.es` y `opendata-movilidad.mitma.es` **bloqueados** en cloud; no es INE: licencia y condiciones sin verificar |

## 2. Granularidad, cobertura, licencia, formato
- Unidad geográfica: 9.864 unidades (7.992 municipios, 664 distritos y 701 secciones de grandes ciudades, 507 SCD = grupos de municipios pequeños) agrupadas en **3.214 áreas de movilidad** (8.131 municipios cubiertos). Los flujos van **entre áreas, no entre secciones**; solo en grandes ciudades el área es distrito o sección.
- Flujos: solo O-D con **más de 15 personas** (censura). Tabla 1.3 de 29-dic-2021: 58.899 filas, 3.214 áreas de origen. EM-1: 82.297 filas.
- Cobertura temporal: 2019 (EM-1) y mar-2020 a dic-2021. Cerrado: el INE no lo actualiza (sin serie vigente).
- Formato: `.xlsx` en ZIP (también tablas px/jaxi 48251-48254, solo INEbase, `servicios.ine.es` bloqueado). Tamaños: áreas 4,9 MB; EM-1 77 MB; dic-2021 49 MB; shapefiles de celdas 17 MB (.7z).
- Licencia: CC BY 4.0 (página de Datos abiertos del INE): reutilizable y publicable con atribución. Estadística **experimental**: dejar constancia.
- Las áreas de las tablas de flujos usan códigos propios (`001A`…), distintos de `ID_GRUPO` (`01VI`…) del fichero de áreas: la unión es por nombre/literal, **sin verificar**; hay que validarla antes de usarla.

## 3. Acceso desde la sesión cloud
- `www.ine.es` accesible (HTTP 200): bajado. `servicios.ine.es` (API Tempus), `transportes.gob.es` y `opendata-movilidad.mitma.es`: bloqueados (403/000).
- Si hiciera falta Tempus, MITMA o el Censo 2021: el propietario o un runner con acceso, o ampliar hosts del entorno.
- Censo 2021 O-D por trabajo/estudio: la búsqueda no localizó tabla municipal descargable; el INE advierte de flujos extraños cuando el origen (Padrón) no refleja la realidad. Pendiente de confirmar con el propietario/INE.

sha256 de lo descargado:
- `descripcion_areas_movilidad_poblacion.zip` ec4bb56ba0702f00211500d7ef2b771a32a06ea1d028348c4a69b64deb5d1263
- `areas_de_movilidad_y_poblacion_a_1_ene_2021.xlsx` 78c496c810c892c60f025316c7c8b215c4fdb5bdcfc59289fbd837fcbd0c1761
- `exp_em1_descargas.zip` 8c01ff6c016d785489b1a2ef93a5260d32482395a4ecc795d7e68fa951eb62f6
- `shapefiles_areas_movilidad.zip` 9feb8470f9a50ba74354e6b06e7bb7784b7f95e47ac0c856a4b1256db7e92717
- `movilidad_cotidiana_diciembre_2021.zip` ce40ca46b368dcab28d9fb3c6d693260ef34a8fe61f2dbcfa4a9f1b6988d095e
- Tabla 1.3 (29-dic-2021) c6e820123d1ef9d917a46aa020ab598b3bbee8ebfe12ebf32dcd7d8f50dceeb2; Tabla 1.3 EM-1 ed0e7c6049e54c18a535d344f50aa4a6b89bffda175c18834005cbaea54e6200
- URLs bajo `https://www.ine.es/experimental/movilidad/` (`experimental_em1.htm`, `experimental_em4.htm`).

## 4. Viabilidad de la medida
Medida posible: fracción interna del distrito `F(D) = Σ flujos(a→b | a,b∈D) / Σ flujos(a→·, a∈D)`, con áreas ⊂ distrito.
- Municipio ≈ área en 7.992 casos: el cálculo es directo si el distrito está formado por municipios enteros. Con SCD (municipios pequeños agrupados) el área es indivisible: no se puede separar.
- Sección: **no hay flujos por sección** salvo 701 secciones de grandes ciudades; en el resto, la sección hereda el área. Un distrito que parta un área exige repartir proporcionalmente (hipótesis, no dato).
- Censura >15 personas: se pierde cola de flujos pequeños (sesgo hacia lo grande); el interno de un área (diagonal) sí aparece.
- Día-tipo (miércoles) y periodo COVID: el dato más limpio es EM-1 (2019-mar-2020); sin actualización posible.
- Privacidad: ya agregado y censurado por el INE; publicar derivados agregados es lícito (CC BY 4.0).
- Reproducibilidad: sí si se fija el ZIP con sha256 (espejo en release, como Infoelectoral); el INE no cambia estos ficheros. Dependencia de unión por nombre: riesgo.
- Cobertura del motor: el motor ya parte de secciones; la medida solo discrimina entre elecciones de agrupar áreas, no dentro de ellas.

## 5. Recomendación (decide el propietario con el Planificador)
- **A. No** (coste 0): quedarse con contigüidad, población y fronteras administrativas.
- **B. Solo piloto en 2-3 provincias** (recomendada si se quiere probar): una provincia con ciudad grande (distritos/secciones) y una rural (SCD). Trabajo estimado: espejo del ZIP en release, tabla área→municipio validada, `F(D)` como métrica informativa sin peso, comparar con el reparto actual. Sin tocar suelo, techo, K ni atomicidad.
- **C. Nacional con peso en la función de calidad**: solo tras B, tras resolver la unión y con decisión explícita del peso. Cambiaría M04/M05 y huellas (`huellas.md`): relanzar con «Generar desde fuente».
Alternativa de más resolución (MITMA, distrito/municipio diario): requiere acceso fuera de cloud y revisar su licencia.
