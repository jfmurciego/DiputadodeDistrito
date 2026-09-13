# C-12 — Nombres de distrito reproducibles

Versión: 1.0.0  
Fecha: 2026-09-13  
Estado: implementado; pendiente de certificación CI.

## Resultado

La herramienta `herramientas/generar_nombres_distrito.py` deriva 214 nombres
únicos de las composiciones M06 ya certificadas: 67 Aragón, 82 Castilla y León
y 65 Extremadura. No modifica esos productos.

Cada distrito recibe una cabecera municipal dominante calculada por población.
Con al menos 50 % se usa `Provincia — Municipio`; por debajo se usa
`Provincia — Entorno de Municipio`. Las colisiones se resuelven con ordinal
romano en orden estable de `district_id`. La evidencia conserva población,
porcentaje dominante, regla, códigos y hashes SHA-256 de cada entrada.

## Garantías

- contrato y umbral versionados antes de publicar nombres;
- desempate determinista por código municipal y nombre;
- cobertura completa y unicidad verificadas;
- ausencia de campos partidistas comprobada;
- recomputación byte-lógica desde CSV M06 en pruebas.

Los nombres son técnicos y auditables. La futura disponibilidad de comarcas
podrá justificar otra versión para denominaciones rurales, pero no invalida ni
altera esta evidencia. C-12 no convierte por sí solo ningún mapa en publicable.

No se ejecuta M01–M06, no se cambian límites y C-01 permanece intacto.
