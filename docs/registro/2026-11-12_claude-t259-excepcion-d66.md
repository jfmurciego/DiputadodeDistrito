## 2026-11-12 — T-259 — Campo de la excepción D-66 en el contrato (motivo, máx. 2)

- `ddd_motor2/excepcion_d66.py` 1.0.0 (nuevo): esquema `validation.max_mixed_districts_exceptions`, con 0 a 2 municipios
  exceptuados por territorio. Cada entrada lleva `{municipio` (INE de 5 cifras), `max_mixtos: 2` (exacto), `motivo`,
  `prueba_infactibilidad`, `aprobacion` («D-<n>»)`}`. `leer` normaliza o da `ErrorContrato` con un mensaje claro: más de 2
  entradas, campo vacío o que falta, max_mixtos ≠ 2, aprobación mal formada, municipio repetido o claves de más.
  `validar` falla si hay alguna: «excepción D-66 declarada pero el núcleo aún no la aplica: T-269».
- `competicion.py` 1.4.3 (legacy 1.4.2): `competir_publico` valida antes de competir, y `Resultado.excepciones_d66` va a
  COMPETICION.json. La huella no cambia. `informe.py` 1.1.2 (legacy 1.1.1): «Excepciones D-66: ninguna» en COMPETICION.md.
- No toca el núcleo (`reglas/`, certificador, batería) ni los mapas: hoy ningún contrato declara excepciones.
- Pruebas: `test_motor2_excepcion_d66` (7) y `test_motor2_semilla` (campo en JSON/MD, contrato con excepción que no se ejecuta).
