# Contrato estándar de territorio DDD

**Versión:** 1.2.0
**Fecha:** 2026-09-13
**Estado:** vigente — R036
**Anterior:** `legacy/docs/CONTRATO_TERRITORIO_v1.1.0.md`

Todo territorio debe satisfacer este contrato antes de considerarse una implantación DDD.

La especificación ya no es sólo documental. Antes de cualquier M01–M06, CI/G10 debe ejecutar `herramientas/validar_contrato_territorial.py --params <yaml> --territory <id>`. Sólo `status=ADMITTED` abre la cadena; `REJECTED` consume cero cálculo territorial.

## 1. Identidad

- `territory_id`: identificador estable, minúsculas y guiones bajos.
- nombre oficial/operativo.
- año de referencia.
- ámbito: regional, nacional u otro.
- `run_name` único.
- `schema_family: ddd-territory`;
- `contract_level`: `bootstrap_m01_m03` o `production_m01_m06`;
- `contract_schema_version: 1.0.0` para producción.

Un bootstrap prueba adquisición y preparación; no declara K ni habilita M04–M06. Un contrato de producción cumple este documento completo y debe coincidir con el catálogo nacional.

## 2. Unidad territorial mínima

Debe declararse la unidad indivisible de entrada y su clave estable: sección censal, precinct, mesa, census tract u otra. La clave debe ser única/no nula y sobrevivir a todo M01–M08.

Campos mínimos:
- identificador;
- geometría;
- población;
- provincia/estado/departamento cuando aplique;
- municipio u otra unidad administrativa relevante;
- nombre administrativo cuando exista.

## 3. Fuentes

Cada fuente debe registrar organismo, fecha/año, fichero, checksum, método de adquisición y transformación necesaria. Prioridad a fuentes oficiales reproducibles.

Fuentes mínimas para M01–M06:
- geometría de unidades;
- población compatible con esas unidades.

Opcionales para M07–M08:
- resultados electorales por unidad suficientemente granular.

## 4. Número de distritos y reparto

Declarar:
- `k_districts` total;
- si existe barrera provincial/estatal;
- método de reparto territorial (Hamilton u otro);
- número explícito de distritos por unidad superior cuando esté fijado;
- target de población resultante.

K queda gobernado en dos capas: el catálogo registra `k_districts`, `k_source` y `k_rationale`; el YAML de producción los repite como contrato ejecutable. La puerta rechaza cualquier divergencia. Fuentes admitidas: norma, fórmula publicada, decisión propia explícita u origen histórico no registrado. Esta última conserva evidencia, pero no constituye criterio reutilizable para un territorio nuevo.

## 5. Restricciones duras

El contrato debe declarar explícitamente:
- contigüidad requerida;
- suelo y techo poblacional;
- tolerancia objetivo fina;
- barreras administrativas infranqueables;
- reglas de municipio indivisible/partible;
- reglas para ciudades sobredimensionadas;
- atomicidad de las unidades movibles;
- excepciones legales o geográficas documentadas.

El perfil general para nuevas admisiones es suelo `0.80`, techo `1.75` y tolerancia `0.12`. Los valores siguen declarándose expresamente en cada YAML: no existe herencia silenciosa. Una desviación exige `limits_profile: exception`, motivo previo, evidencia y fecha de decisión. Está prohibido modificar límites después de observar el resultado para convertir un fallo en aprobación.

La atomicidad municipal también es decisión de fondo. Su valor y motivo deben estar declarados antes de ejecutar; no puede utilizarse como mando de convergencia a posteriori.

## 6. Objetivos blandos

Pueden incluir, en orden explícito:
- desviación poblacional;
- compactación;
- respeto a límites municipales/comarcales;
- estabilidad respecto a un baseline;
- otras métricas no electorales.

La afiliación política o resultados electorales no pueden ser objetivo geométrico del motor DDD.

## 7. Contrato de módulos

- M01 debe producir universo completo y población auditada.
- M02 debe producir adyacencias reproducibles.
- M03 debe producir grafo territorial íntegro.
- M04 debe construir K distritos y respetar restricciones duras de construcción.
- M05 optimiza sin violar restricciones duras.
- M06 consolida y calcula métricas territoriales.
- M07 agrega elecciones al mapa ya fijado.
- M08 produce el producto final combinado.

## 8. Tests obligatorios

Cada territorio debe probar como mínimo:
- cardinalidad exacta de unidades;
- población total conservada;
- claves únicas/no nulas;
- K esperado;
- reparto por unidad superior si existe;
- contigüidad;
- barreras administrativas;
- suelo/techo;
- reglas de atomicidad administrativa;
- determinismo para misma configuración/semilla.

Una vez exista baseline promovido, añadir regresión explícita de ese baseline.

## 9. Criterio de promoción

Un territorio pasa de `preparación` a `candidato` cuando M01–M06 cumplen el contrato local. Pasa a `validado` únicamente tras GitHub Actions reproducible, validación sin fallos, outputs completos y documentación del run.

La admisión previa verifica como mínimo identidad, fuentes con checksum, presencia M01–M06, continuidad exacta entre outputs e inputs, coherencia de K/códigos/roles/restricciones, outputs únicos y confinados al repositorio. La admisión no equivale a promoción: únicamente autoriza que la ejecución pueda comenzar.

## 10. Internacionalización

El contrato no presupone provincias españolas ni CUSEC. Los conceptos deben mapearse a roles genéricos: `unit_id`, `admin_level_1`, `admin_level_2`, `population`, `district_id`, etc. Los nombres españoles pueden mantenerse como adaptadores de las primeras implantaciones, pero no deben convertirse en dependencia conceptual del motor final.
