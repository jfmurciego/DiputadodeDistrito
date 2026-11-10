# T-139 · Piloto de movilidad, paso 1: datos, unión y 5 provincias (2026-11-10)

Opción B del propietario: piloto en 5 provincias, solo indicador, sin peso. No toca motor ni función de calidad; nada se publica.
Continúa `T138_MOVILIDAD_COHESION_FUNCIONAL_2026-11-10.md`.

## Datos (almacenamiento durable = git; R2 solo si el Operador lo ordena)
`datos/movilidad/` (derivado en CSV de los xlsx del INE, CC BY 4.0, estadística experimental; atribución: INE). `MANIFEST.json` lleva URL, sha256 de origen y de salida:
- `areas_movilidad_2019.csv` 70388ee7d4a7a5482829eb2512d22ca7bc02c0a638758cc0472401b020d08c4d (xlsx origen `areas_de_movilidad_y_poblacion_a_1_ene_2019.xlsx`).
- `flujos_em1_origen_destino.csv` 043b3acede9d28a18b1fef4dccecdad73e4e93986c633898bcb8b8c43dd76f51 (Tabla 1.3 EM-1, 82.296 flujos de más de 15 personas).
- `codigos_flujo.csv` e326b2d281e0bac8a94699f9d31883a983bad8539bbf20678a029dfc45d7c7a6.
Regenerar: `python herramientas/movilidad_em_union.py convertir <areas.xlsx> <flujos.xlsx> --origen-json <origen.json>` (necesita `openpyxl`; el análisis no).

## Unión flujo ↔ ID_GRUPO (verificada)
Los códigos de flujo (`001A`) y los de grupo (`01VI`) no se relacionan por prefijo. Se unen por el literal del área con espacios y Unicode normalizados: **3.214 códigos ↔ 3.214 grupos, uno a uno, sin ambigüedad** (`verificar`). Sin normalizar, 43 nombres fallan por espacios/Unicode. Pseudo-destino `OTRO` («OTROS DESTINOS», 3.214 filas, una por origen): se cuenta aparte, no se une.

## Qué parte el plan: criterio de selección
Se casa cada sección del plan vigente (`datos/composicion/congreso_*.csv`) con su área: sección (10 cifras), distrito (7) o municipio (5). Las áreas SCD (secciones dispersas de 16 municipios, entre ellos las capitales de Alicante, Asturias, Baleares, Barcelona, Córdoba, Las Palmas, Madrid, Málaga, Murcia, Pontevedra, Sevilla, Valencia, Valladolid, Vizcaya y Zaragoza) **no se pueden casar con secciones**. Si el plan parte uno de esos municipios, el indicador depende de partir la capital: se excluyen esas 15 provincias.
Filtro R0: K ≥ 4, ningún municipio sin área partido por el plan, sin islas (los flujos entre islas no existen), población en áreas partidas por el plan ≤ 20 %.
Con R0 la «metropolitana grande» (Madrid, Barcelona) no existe: ambas parten su capital. La mayor sin ese problema es Cádiz.

| Perfil | Provincia | K | Población | Municipios | Mayor municipio | 2.º/1.º | Pob. en áreas partidas |
|---|---|---|---|---|---|---|---|
| Metropolitana grande (mayor población en R0) | Cádiz | 11 | 1.254.866 | 45 | 17 % | 0,58 | 14 % |
| Ciudad media con corona (mayor municipio 20-35 %, 2.º/1.º < 0,3, mayor población) | Granada | 8 | 934.072 | 174 | 25 % | 0,25 | 16 % |
| Rural dispersa (más municipios por distrito) | León | 4 | 448.573 | 211 | 27 % | 0,52 | 9 % |
| Litoral/turística (costa; atributo geográfico, no del dato) | Gerona | 7 | 808.672 | 221 | 13 % | 0,46 | 13 % |
| Varios polos comparables (mayor 2.º/1.º entre las restantes) | Tarragona | 7 | 848.592 | 184 | 16 % | 0,78 | 13 % |

Alternativas: polos → Ciudad Real (0,60, K 4); litoral → Huelva (K 4) o Guipúzcoa (K 6). Sustituir es decisión del Coordinador/propietario. Tabla completa de las 52 circunscripciones: `python herramientas/movilidad_em_union.py candidatas`.

## Límites
Flujos de menos de 16 personas ausentes; datos 2019 a mar-2020 (áreas a 1-ene-2019; las secciones del plan vigente pueden haber cambiado); «partida» = población de un área de movilidad repartida entre varios distritos: su flujo interno no se puede asignar sin hipótesis.
Siguientes pasos (una PR cada uno): 2) indicador por distrito y plan, con y sin capital; 3) tabla por provincia con población y compacidad y recomendación de peso.
