# Andalucía F10 — solicitudes institucionales precisas de acreditación (19/10/2026)

**ESTADO: READY_FOR_OWNER_AUTHORIZATION — NO ENVIADO.** Se redactan dos solicitudes separadas con destinatario competente distinto. No son autorizaciones para reasignar votos, alterar la referencia territorial de 2025, modificar puertas o generar distritos.

## A. A la Oficina del Censo Electoral (INE): correspondencias 2025–2026

**Destinatario:** Oficina del Censo Electoral, a través de la Delegación Provincial del INE competente en cada caso, con coordinación para las ocho provincias andaluzas.  
**Asunto:** Certificación del seccionado electoral efectivo 17/05/2026 y correspondencia con el seccionado INE 2025 para 67 CUSEC de Andalucía.

Solicitamos información no nominativa, preferentemente reutilizable (CSV, XLSX o documentación autenticada), para acreditar la correspondencia administrativa entre los recintos seccionales INE referenciados como 2025 y las secciones y subsecciones electorales efectivamente utilizadas el 17/05/2026.

Hemos recuperado y verificado por SHA-256 los tres ZIP originales del INE de *variaciones del Callejero Electoral*, que cubren enero de 2025 a julio de 2026. El informe `ANDALUCIA_INE_TRAM_3_PERIODOS_86_CUSEC.json` identifica **25 de 25 secciones nuevas** y **9 de 9 retiradas** con registros administrativos directos de modificación de tramos (`CVAR=M`). Esos registros prueban modificaciones de callejero, **no la correspondencia completa y exclusiva de los votos**.

El análisis también identifica **41 secciones con mismo CUSEC pero modificación geométrica material** entre ediciones 2025 y 2026. De ellas, 39 tienen referencias a modificaciones de tramos; las otras dos son `4109110025` y `4109110027`, municipio de Sevilla. Solicitamos para ambas la confirmación del tipo de variación, edición de geometría, fecha efectiva y documentación que permita decidir si el cambio es administrativo, cartográfico o de otra naturaleza.

Por cada alta, baja y sección modificada solicitamos:

1. Fecha de eficacia del cambio, sección/es origen y destino, distrito, municipio y provincia.
2. Correspondencia oficial de la **totalidad** de la sección, o identificación de las múltiples secciones afectadas cuando hubo escisión o fusión, con desglose de calles/tramos y subsecciones.
3. Confirmación del seccionado de referencia para el censo electoral **vigente el 17/05/2026**, y de su correspondencia temporal con la edición INE 2025 utilizada por nuestro estudio.
4. Si existe, un registro de correspondencia territorial o agrupación oficial no nominativa que permita adscribir resultados electorales a unidades 2025 con garantías; si no existe, confirmación explícita de esa limitación.
5. En **Cortegana (Huelva)**, confirmar la relación entre `2102502002` (presente en la cartografía de 2025 y 2026) y `2102502001` (única sección electoral del distrito 02 en la convocatoria). El archivo INE de variaciones registra el **29/01/2026** una modificación `M` de **15 tramos** de `2102502002` a `2102502001`. El anuncio de la Oficina del Censo Electoral publicado en BOP Huelva 61/2026, páginas 16–17, sitúa las mesas **A, B y C** en Cortegana, San Telmo y Valdelamusa, todas dentro de sección 001. Solicitamos los efectos exactos de la modificación y la pertenencia seccional de cada subsección/mesa.

**No solicitamos información personal ni listas de electores o votantes.** Si otro organismo es el custodio, rogamos comunicar su identificación y el cauce de acceso.

**Anexos reproducibles:** informe de las tres ediciones del callejero y sus SHA-256, fichero de 25 secciones nuevas con 15.425 votos a candidaturas y las 9 bajas, inventario de 41 cambios geométricos con 31.792 votos, evidencia OCE/BOP y enlace a PR #269 del repositorio DDD.

## B. A la administración electoral competente: resultados por mesa y actas

**Destinatario inicial propuesto:** Secretaría de la Junta Electoral Provincial de Huelva, para Cortegana; y órgano custodio competente de cada provincia para las demás mesas o resultados afectados. La Junta Electoral de Andalucía puede orientar la coordinación territorial.  
**Asunto:** Acceso a documentación y resultados de escrutinio por mesa, elecciones al Parlamento de Andalucía 17/05/2026.

Solicitamos acceso a las **actas o resultados oficiales desagregados por mesa** relevantes para las secciones afectadas, y en particular a las mesas **A, B y C** de la sección electoral `2102502001` de Cortegana, distrito 02, con desagregación por candidaturas y categorías electorales, en la medida en que dichos documentos formen parte de los archivos que custodia la administración electoral.

El expediente F10 reproduce exactamente la fuente oficial SIEL: **6.044 secciones, 4.136.317 votos a candidaturas territoriales y 21.222 CERA**, total de **4.157.539**. En la sección electoral `2102502001` constan **658 votos a candidaturas agregados**; no está acreditada la distribución territorial respecto a `2102502002`.

Esta petición se formula teniendo en cuenta la **resolución de la Junta Electoral Central de 25/06/2026, expte. 802/147 (consulta de la Junta Electoral Provincial de Huelva)**, en la que se indica que el acceso a la documentación electoral corresponde a las secretarías custodias, que las actas físicas pueden consultarse con protección de datos y que no procede proporcionar listas nominales de votantes. Aceptamos acceso presencial, copia anonimizada o el formato que fundadamente admita la custodia.

**No solicitamos listas de votantes, datos personales, actas no divulgables ni ficheros auxiliares provisionales de la adjudicataria.**

Resolución JEC: https://juntaelectoral.parlamentodeandalucia.es/documents/20117/32508/2026-0617-acuerdo-JEC-acceso-actas-escrutinio.pdf/d9bea5fe-4b81-aaf1-7507-48c052c2c52d

Anuncio OCE Huelva: https://s2.diphuelva.es/portalweb/bope/anuncios/Anuncio_350957_BOP-61_2026.pdf

## C. Evidencia y delimitación del bloqueo

Se ha demostrado:

- Originales oficiales del INE de tres períodos, con CRC, SHA y manifiesto.
- 25/25 relaciones directas entre códigos nuevos 2026 y su sección geográfica predecesora principal, y 9/9 bajas; ambas relaciones son de **tramos**, no de integridad de voto.
- 39/41 secciones de mismo código con cambios documentados en TRAM; dos sin prueba de cambio de tramos en el extracto analizado.
- El tratamiento administrativo de Cortegana tiene un antecedente de 15 tramos registrado el 29/01/2026 y una relación oficial OCE de mesas en marzo.
- 15.425 votos en altas; 31.792 votos en secciones del mismo código con cambios de límites; 658 votos electorales en Cortegana 02-001. **67 secciones, 47.875 votos distintos afectados, sin doble cómputo**. Las 9 secciones retiradas tienen resultados de secciones sucesoras que ya están incluidos en las 41 y no se suman otra vez.

**Falta:** documento o regla institucional admitida que establezca la atribución **completa y exclusiva** de los votos electorales de 2026 a la geografía de 2025 bajo el contrato F10. En su ausencia, `CROSSWALK_ACCREDITED=false`; `F10_ELECTORAL=BLOCKED_CROSSWALK_NOT_PROVEN`; `generation_authorized=false`. Nunca inferir votos por superficie, proximidad o relación parcial de tramos.

**Registro para Work:** una autorización de envío, en el canal y con el firmante indicados por el propietario, sin alterar puertas ni aprobar excepciones por esta petición.
