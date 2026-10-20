# F10 — Ejecución autónoma sobre Aragón, Castilla y León y Extremadura (2026-10-20)

**Alcance:** exclusivamente Fuentes Oficiales, sin redistribución estimada de votos, modificación de contratos, producción, ni promoción F10. Tres líneas independientes comprobadas incluso si otras fallan. **No se declara acreditación de bytes inaccesibles.**

## Aragón: dos orígenes oficiales por mesa, identidad de elección CA2026

**Nuevo origen procesable:** Gobierno de Aragón publica su dataset oficial 'Elecciones a Cortes de Aragón, año 2026, detalle distrito mesa electoral' en datos.gob.es: https://datos.gob.es/es/catalogo/a02002834-elecciones-a-cortes-de-aragon-ano-2026-detalle-distrito-mesa-electoral.

Distribuciones oficiales publicadas por ese catálogo:
- Votos por candidatura y mesa CSV: `https://opendata.aragon.es/GA_OD_Core/download?resource_id=381&formato=csv&filters={"cod_elec":"CA2026"}`
- Votos por candidatura y mesa JSON: `https://opendata.aragon.es/GA_OD_Core/download?resource_id=381&formato=json&filters={"cod_elec":"CA2026"}`
- Participación por mesa CSV: `https://opendata.aragon.es/GA_OD_Core/download?resource_id=380&formato=csv&filters={"cod_elec":"CA2026"}`
- Participación por mesa JSON: `https://opendata.aragon.es/GA_OD_Core/download?resource_id=380&formato=json&filters={"cod_elec":"CA2026"}`

Esta segunda vía independiente complementa los originales definitivos XLS provinciales localizados en `docs/AUDITORIAS/F10_FUENTES_OFICIALES_20261020/ORIGENES_ELECTORALES_Y_PUERTAS.md`. La API Open Data devuelve **target_unreachable** desde el conector de este entorno. Las descargas provinciales devuelven bytes XLS que el extractor de texto no conserva íntegros. El runtime local no resuelve DNS externo. Por ello, **ningún CSV, JSON o XLS ha sido validado bit a bit ni agregado**. Es imprescindible descargar binarios/CSV mediante canal de transferencia íntegra, calcular SHA-256, cotejar columnas provincia/municipio/distrito/sección/mesa/candidatura, y conciliar sumas con el acuerdo electoral. Identificar expresamente datos provisionales frente a definitivos antes de sustituir el recibo electoral vigente.

**Pendiente específico:** correspondencia de 2026 con seccionado territorial INE 2025; la disponibilidad de mesa no acredita transferencias entre dos secciones. Conservar `BLOCKED`.

## Castilla y León: control de definitivos corregidos y universo electoral

**Actas normativas oficiales**, todas enlazadas desde https://juntaelectoral.ccyl.es/resultadoselectorales.html :
- Publicación 29/04/2026: `https://bocyl.jcyl.es/boletines/2026/04/29/pdf/BOCYL-D-29042026-80-13.pdf`
- Primera corrección 08/06/2026: `https://bocyl.jcyl.es/boletines/2026/06/08/pdf/BOCYL-D-08062026-108-27.pdf`
- Segunda corrección 11/06/2026: `https://bocyl.jcyl.es/boletines/2026/06/11/pdf/BOCYL-D-11062026-111-18.pdf`

**Control oficial adicional:** estadísticas INE de elección autonómica 15/03/2026 https://ine.es/dynt3/inebase/es/index.htm?capsel=13528&padre=13527, incluyendo número de municipios, distritos, secciones y mesas. Es referencia para verificar integridad electoral, **no** fichero de votos a candidatura por mesa. El dataset abierto `datos-basicos-de-elecciones-a-las-cortes` https://analisis.datosabiertos.jcyl.es/explore/dataset/datos-basicos-de-elecciones-a-las-cortes/api/ cubre estructura electoral general, no acredita escrutinio definitivo granular: no utilizarlo como sustituto.

En este entorno no se obtuvo bytes íntegros de los tres PDF para comparar a nivel de fila qué resultados rectifican. No afirmar conciliación definitiva. **Procedimiento pendiente:** capturar PDFs, SHA-256, extraer anexos, identificar literalmente las celdas rectificadas, formar control de nueve provincias y conciliar fichero electoral por mesa certificado; luego validar los códigos 2025/2026 afectados con documentación OCE. Mantener `BLOCKED`.

## Extremadura: reconciliación oficial y límite granular

**Fuente primaria:** DOE núm. 8, 14/01/2026, acuerdo de 07/01/2026: `https://doe.juntaex.es/otrosFormatos/html.php?anio=2026&doe=80o&xml=2026AC0001`. Acredita voto a candidaturas por provincia (Badajoz **326196** y Cáceres **198641**, suma **524837**), no votos definitivos por mesa. La fuente provisional granular ya catalogada totaliza **522418** y la diferencia de agregados es **2419**. Esta operación aritmética **no localiza las mesas alteradas**; no repartir diferencia entre secciones ni confundir provisional con definitivo.

La nota oficial de dispositivo electoral de 19/12/2025 https://www.juntaex.es/w/presentacion-centro-datos-elecciones-autonomicas señala expresamente recogida de **escrutinio provisional** mediante su CDD: su portal no acredita por sí solo el escrutinio general. La Junta Electoral Central conserva referencia al acuerdo definitivo https://www.juntaelectoralcentral.es/cs/Satellite?c=JECEleccion_C&childpagename=JEC%2FJEC_Layout&cid=1408442283375&pagename=jec%2Fwrapper%2FJEC_Wrapper&rendermode=preview. No se halló en esta búsqueda un origen oficial verificable con resultado **definitivo desagregado por mesa**. Esperar respuesta del titular de las Juntas provinciales o localizar actas certificadas con el desglose. Conservar `BLOCKED`.

## Resultado de ejecución / no-promoción

| Territorio | Fuente localizada | Descarga íntegra/hash | Conciliación numérica granular | Correspondencia oficial | F10 |
|---|---|---|---|---|---|
| Aragón | XLS 3 provincias y CSV/JSON oficiales por mesa | NO | NO | Pendiente | BLOCKED |
| Castilla y León | 3 publicaciones oficiales; fuente INE mesas/censo | NO | NO | Pendiente | BLOCKED |
| Extremadura | DOE definitivo por provincia | Disponible como HTML, sin artefacto firmado nuevo | Sólo diferencia agregada 2419, no por mesa | Definitivos mesa pendientes | BLOCKED |

**No editar la matriz nacional**: descubrimiento de orígenes no cambia la admisibilidad. Se han buscado las fuentes de los tres territorios independientemente; las barreras identificadas son transporte íntegro binario/CSV y acreditación electoral administrativa, no una autorización del usuario. Las solicitudes institucionales han sido remitidas por el usuario con su correo privado, sin almacenarlo ni exponerlo.
