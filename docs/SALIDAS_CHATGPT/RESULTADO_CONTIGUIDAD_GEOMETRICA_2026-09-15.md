# Resultado — auditoría independiente de contigüidad geométrica

**Fecha:** 2026-09-15  
**Responsabilidad:** auditoría geométrica independiente de distritos; no modifica M04, M05, M06 ni resultados territoriales.

## 1. Motivo y diseño

La puerta existente `herramientas/auditar_topologia_geometrica.py` comprueba que las aristas de M03 correspondan a fronteras compartidas métricas y que cada distrito sea conexo sobre ese grafo. Esa comprobación es necesaria, pero no demuestra por sí sola que la **geometría disuelta real** de cada distrito forme una única pieza territorial.

M06, por contrato, no cambia `district_id` y publica un GeoJSON de secciones finales y otro GeoJSON disuelto por distrito. La auditoría nueva se coloca conceptualmente después de M06, pero reconstruye el dissolve desde las secciones para no confiar ni en el grafo M03 ni en el dissolve ya publicado por M06.

## 2. Código

Se añaden exclusivamente:

- `herramientas/auditar_componentes_geometricos.py`
- `tests/test_auditar_componentes_geometricos.py`

No se modifica la herramienta topológica existente. Al ser una herramienta nueva, no existe versión previa que deba preservarse en `legacy/`.

La herramienta:

1. lee el GeoJSON de secciones de M06, también si está empaquetado como `.geojson.zip`;
2. exige CRS declarado, identificadores de sección únicos y geometrías poligonales válidas;
3. reproyecta al CRS métrico indicado;
4. agrupa todas las secciones por `district_id`;
5. ordena las secciones por identificador para estabilizar la entrada al dissolve;
6. ejecuta una unión geométrica independiente (`unary_union`);
7. distingue `Polygon` y `MultiPolygon` y cuenta componentes poligonales reales;
8. cuenta anillos interiores;
9. calcula área, bounding box y SHA-256 WKB del distrito y de cada componente;
10. emite un registro reproducible por distrito;
11. termina con código 2 si encuentra una discontinuidad no gobernada o un bloqueo de contrato.

La herramienta **no consulta M03 ni sus aristas**.

## 3. Semántica de la puerta

### Distrito continental normal

Un distrito solo es `CONNECTED` cuando el dissolve devuelve exactamente:

- `Polygon`;
- `component_count = 1`.

Por tanto, dos polígonos unidos únicamente por una esquina no quedan certificados como continuidad territorial normal: el dissolve conserva ese caso como `MultiPolygon`.

### Huecos interiores y enclaves

Un `Polygon` puede contener uno o más anillos interiores. La auditoría los registra mediante `interior_ring_count`, pero no los transforma automáticamente en una discontinuidad: el polígono exterior sigue siendo una sola componente.

La herramienta no inventa la causa territorial del hueco ni decide por sí sola si es administrativamente legítimo; deja la evidencia geométrica para su gobierno explícito cuando proceda.

### Islas, exclaves u otros MultiPolygon legítimos

Por defecto, **todo `MultiPolygon` bloquea**.

Solo puede superar la puerta mediante un JSON de política explícito con schema:

```json
{
  "schema": "ddd.geometric-contiguity-policy/1.0",
  "allowed_disconnected_districts": [
    {
      "district_id": 17,
      "expected_components": 2,
      "kind": "island",
      "reason": "Motivo territorial documentado"
    }
  ]
}
```

La excepción debe identificar distrito, tipo, motivo y número exacto esperado de componentes. Si el número real no coincide, la excepción no aplica y la puerta bloquea. Una excepción declarada para un distrito que en realidad ya es `Polygon` también se considera desalineación de política y bloquea.

**No se incorpora ninguna excepción para Aragón en este trabajo.**

## 4. Informe distrital reproducible

El JSON de salida contiene, entre otros:

- `decision`: `PASS`, `PASS_WITH_EXCEPTIONS` o `BLOCK`;
- `gate_statement`;
- número de secciones y distritos;
- `connected_districts`;
- `governed_exceptions`;
- `blocked_districts`;
- bloqueos de contrato;
- una entrada por distrito con:
  - número de secciones;
  - tipos geométricos de entrada;
  - tipo geométrico disuelto;
  - número de componentes;
  - anillos interiores;
  - estado;
  - política aplicada, si existe;
  - área total;
  - área, peso, bbox y huella SHA-256 de cada componente;
  - bbox y huella SHA-256 del dissolve completo.

Para Aragón continental normal, la puerta buscada es literalmente equivalente a:

`67 distritos evaluados / 67 geométricamente conexos`

sin política de excepciones.

## 5. Tests sintéticos

Comando de prueba:

```bash
python -m unittest discover -s tests -p 'test_auditar_componentes_geometricos.py' -v
```

Resultado local de esta intervención: **5/5 OK**.

Casos cubiertos:

1. dos polígonos unidos por frontera real → `PASS`, `Polygon`, 1 componente;
2. dos polígonos unidos solo por esquina → `BLOCK`, `MultiPolygon`, 2 componentes;
3. dos polígonos separados → `BLOCK`, 2 componentes;
4. `MultiPolygon` separado → bloquea sin política y pasa solo con excepción explícita cuyo `expected_components` coincide;
5. `Polygon` con hueco interior → permanece conexo y el hueco queda registrado.

## 6. Resultados sobre evidencia disponible

La configuración vigente de Aragón declara `min_shared_border_m: 1.0`, K=67 y salida M06 de secciones en:

`ejecuciones/{run_id}/aragon_2025_m06_secciones.geojson.zip`

Los resultados M06 históricos ya almacenados en el repositorio pertenecen a ejecuciones anteriores al endurecimiento topológico actual y, por tanto, **no son evidencia válida para afirmar 67/67 bajo la nueva topología**.

Durante esta intervención no apareció en `main` un nuevo M06 post-endurecimiento disponible para auditoría. No se ha ejecutado ningún territorio, conforme a la restricción de esta tarea.

Estado factual:

- herramienta geométrica independiente: preparada;
- tests sintéticos: PASS 5/5;
- Aragón post-endurecimiento: **pendiente del próximo M06**;
- certificación `67/67`: **no afirmada todavía por falta de evidencia M06 nueva**.

## 7. Limitaciones

- La herramienta valida geometría, no causalidad territorial: no inventa por qué existe una isla o exclave.
- Una excepción territorial debe venir declarada por política externa; la geometría por sí sola no la autoriza.
- Geometrías de sección inválidas se rechazan; no se reparan silenciosamente.
- La huella WKB es reproducible dentro de una misma pila GEOS/Shapely y una entrada ordenada; no sustituye la prueba geométrica.
- El CRS de trabajo afecta métricas de área/bbox, no la política de componentes. Para M06 se usa `EPSG:3035`, CRS métrico contractual vigente.
- La auditoría reconstruye el dissolve desde las secciones M06. No usa el GeoJSON disuelto de M06 como fuente de verdad, para mantener independencia.

## 8. Comando exacto para auditar el próximo M06 de Aragón

Sin excepciones territoriales:

```bash
python herramientas/auditar_componentes_geometricos.py \
  --sections ejecuciones/<RUN_ID>/aragon_2025_m06_secciones.geojson.zip \
  --section-field CUSEC_KEY \
  --district-field district_id \
  --working-crs EPSG:3035 \
  --expected-districts 67 \
  --output ejecuciones/<RUN_ID>/aragon_2025_m06_contiguedad_geometrica.json
```

La puerta correcta para Aragón continental normal es `decision = PASS` y:

`67 distritos evaluados / 67 geométricamente conexos`.

Si apareciera una anomalía territorial legítima, primero debe existir una política explícita y auditada; solo entonces procede añadir `--policy <fichero.json>`.
