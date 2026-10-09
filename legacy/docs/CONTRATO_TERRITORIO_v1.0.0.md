# Contrato estándar de territorio DDD

**Versión:** 1.0.0
**Fecha:** 2026-09-11
**Estado:** vigente — R018

Todo territorio debe satisfacer este contrato antes de considerarse una implantación DDD.

## 1. Identidad

- `territory_id`: identificador estable, minúsculas y guiones bajos.
- nombre oficial/operativo.
- año de referencia.
- ámbito: regional, nacional u otro.
- `run_name` único.

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

Nunca se heredan silenciosamente los valores de Aragón. Si un valor coincide, debe estar declarado igualmente.

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

## 10. Internacionalización

El contrato no presupone provincias españolas ni CUSEC. Los conceptos deben mapearse a roles genéricos: `unit_id`, `admin_level_1`, `admin_level_2`, `population`, `district_id`, etc. Los nombres españoles pueden mantenerse como adaptadores de las primeras implantaciones, pero no deben convertirse en dependencia conceptual del motor final.
