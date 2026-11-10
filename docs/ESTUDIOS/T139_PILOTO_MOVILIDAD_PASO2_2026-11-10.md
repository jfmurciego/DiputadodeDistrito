# T-139 · Piloto de movilidad, paso 2: indicador de cohesión funcional (2026-11-10)

Solo indicador, sin peso. No toca motor ni función de calidad; nada se publica. Provincias aprobadas por el Planificador: Cádiz, Granada, León, Gerona, Tarragona. Datos y unión: paso 1.

## Definición (`herramientas/movilidad_em_union.py indicador`)
- Universo: flujos EM-1 (más de 15 personas) entre áreas **distintas**, con origen y destino dentro del territorio. Los flujos internos de un área (diagonal) no cuentan: son intramunicipales o intra-área.
- Cohesión del distrito d = flujo de salida de áreas de d cuyo destino también está en d / flujo de salida total de d. Cohesión del plan = misma razón sumada sobre todos los distritos.
- Área partida por el plan: su peso se reparte entre distritos en proporción a la población de sus secciones (hipótesis; el INE no da flujos por sección). Un área SCD no se casa con secciones (límite de más abajo).
- «Sin capital»: se excluyen los flujos que empiezan o acaban en cualquier área del municipio capital (código resuelto por el nombre oficial en el xlsx del INE: Cádiz, Granada, León, Girona, Tarragona).
- Los flujos hacia fuera del territorio se cuentan aparte (`hacia_fuera`) y no entran en la fracción. Distritos numerados 1..K (`numeracion_publica`).

## Resultado (`datos/movilidad/piloto_indicador_em1.csv`, sha256 6389bfc0fe19251284735d41ae95a16e5a6c50a674edb17b9c8fbefb479ac95d)
| Provincia | Plan con capital | Plan sin capital | Distritos con capital (mín-máx) | Distritos sin capital (mín-máx) | K |
|---|---|---|---|---|---|
| Cádiz | 0,643 | 0,657 | 0,33-0,83 | 0,33-0,84 | 11 |
| Granada | 0,410 | 0,603 | 0,16-0,84 | 0,38-0,91 | 8 |
| León | 0,660 | 0,834 | 0,33-0,93 | 0,69-0,93 | 4 |
| Gerona | 0,615 | 0,704 | 0,46-0,79 | 0,08-0,82 | 7 |
| Tarragona | 0,556 | 0,588 | 0,26-0,69 | 0,28-0,76 | 7 |
Un distrito sin flujo tras quitar la capital queda sin valor (todo su flujo era de la capital). En Granada y León la capital reparte flujos entre varios distritos y baja mucho el plan; en Gerona un distrito casi entero de la capital cae a 0,08 sin ella.

## Límites
- Datos EM-1 2019-mar-2020, flujos de más de 15 personas, áreas a 1-ene-2019; las secciones del plan vigente son posteriores.
- Un valor por plan no se interpreta sin referencia: falta comparar con otros planes de la misma provincia (paso 3 y universo del motor nuevo).
- El indicador es de origen (residente → destino), no de pares simétricos.

## Qué haría falta para cubrir las 15 capitales excluidas
Madrid, Barcelona, Valencia, Sevilla, Zaragoza, Málaga, Murcia, Palma, Las Palmas, Valladolid, Córdoba, Alicante, Oviedo/Gijón, Bilbao y Pontevedra/Vigo (provincias Alicante, Asturias, Baleares, Barcelona, Córdoba, Las Palmas, Madrid, Málaga, Murcia, Pontevedra, Sevilla, Valencia, Valladolid, Vizcaya y Zaragoza) tienen áreas SCD sin equivalencia con secciones. Opciones:
1. Pedir al INE la tabla sección ↔ SCD (InfoINE; el diseño de registro del fichero de formas de EM-1 trae celdas, `shapefiles_celdas_marzo2020.zip`): permitiría casar por geometría cada sección con su SCD.
2. Casarlas por geometría nosotros: intersección de las celdas de EM-1 (shapefile del INE, 33 MB, ya descargado en la sesión, sin versionar) con las secciones del motor; coste: una herramienta nueva y validación de proyecciones.
3. Tratar el municipio SCD como un solo nodo si el plan no lo parte; en las 15 provincias lo parte, por lo que no vale.
4. Usar MITMA (distrito/municipio diario) para estas capitales: requiere acceso desde fuera de la nube y revisar licencia.
