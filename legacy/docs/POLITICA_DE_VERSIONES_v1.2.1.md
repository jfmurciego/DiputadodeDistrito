# Política de versiones y conservación

**Versión:** 1.2.1 — Gobernanza documental verificable  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/docs/POLITICA_DE_VERSIONES_v1.2.0.md`

## Regla inviolable

Ningún fichero funcional/versionado existente se sustituye sin conservar previamente su contenido anterior en `legacy/`. Git conserva historial; `legacy/` es la capa explícita de arqueología inspeccionable sin reconstruir commits.

La copia archivada representa evidencia y debe conservar el contenido anterior **literalmente**. Un linter o formatter no debe modificar retrospectivamente esa copia para eliminar whitespace u otros defectos cosméticos. Los huecos heredados se documentan como deuda histórica; nunca se rellenan con contenido inventado.

## Versionado

Se usa `MAJOR.MINOR.PATCH`:
- **MAJOR:** cambia contrato, algoritmo fundamental o compatibilidad de entradas/salidas.
- **MINOR:** mejora funcional compatible o modificación sustancial de comportamiento.
- **PATCH:** corrección compatible, metadatos o trazabilidad sin cambio de contrato.

El fichero activo mantiene nombre estable. La versión retirada se conserva en `legacy/<familia>/..._vA.B.C.*`.

## Cabecera obligatoria

Código ejecutable, configuración y workflows versionados deben declarar, cuando el formato lo permita: proyecto/componente, versión, nombre de versión, fecha, función/alcance, estado, cambios, motivo y predecesor.

Si existe predecesor materializado, `ANTERIOR` debe apuntar a su ruta real. Si no fue recuperado debe declararse `PREDECESOR HISTÓRICO NO RECUPERADO` u `ORIGEN: baseline recuperado`. Queda prohibido fingir una ruta `legacy/` inexistente.

Los documentos canónicos con versión explícita también deben conservar su predecesor inmediato y, cuando declaren `Anterior`, esa ruta debe existir físicamente. Los documentos acumulativos sin versión propia, como `REGISTRO_DE_CAMBIOS.md`, deben conservar una instantánea previa cuando sean reescritos.

Outputs generados, fuentes congeladas y formatos sin cabecera textual resuelven trazabilidad mediante manifiestos, hashes y documentación asociada.

## Estado canónico

Los documentos vigentes son `README.md`, `docs/ESTADO_MAESTRO_PROYECTO.md`, `docs/CONTINUIDAD_NUEVO_CHAT.md`, `docs/BITACORA.md` y `docs/REGISTRO_DE_CAMBIOS.md`. Los antiguos `docs/MEMORIA*` están retirados y no deben actualizarse.

## Procedimiento de cambio

Todo cambio funcional exige:
1. conservar **antes** la versión anterior en `legacy/`;
2. incrementar versión;
3. actualizar cabecera/metadatos;
4. registrar el cambio;
5. actualizar documentos canónicos si cambia el estado que comunican;
6. usar commit identificable;
7. ejecutar la puerta automática de regresión aplicable;
8. registrar una nueva ejecución territorial cuando cambie comportamiento del procedimiento.

Los cambios documentales versionados conservan también su predecesor. Las copias `legacy/` de documentos o código no se corrigen retroactivamente para satisfacer reglas introducidas después.

## Puerta automática R015

`.github/workflows/pruebas-ddd.yml` ejecuta la suite `tests/test_r015_invariantes.py`. Como mínimo debe permanecer verde para cualquier cambio que afecte componentes auditados, configuración, workflows, M04/M05 o documentación de gobernanza.

La suite verifica dos niveles de trazabilidad: (1) cabeceras y predecesores reales de los componentes funcionales auditados; (2) referencias `Anterior` de los documentos canónicos versionados. Una referencia activa a un `legacy/` inexistente debe hacer fallar la CI.

La suite no sustituye al procedimiento territorial. Si cambia lógica funcional, una CI verde demuestra ausencia de las regresiones cubiertas, pero la promoción exige además un nuevo run completo/iterativo del procedimiento y su expediente.

## Aceptación

Una ejecución local, simulación o sesión de IA es diagnóstico. La evidencia de aceptación procede de GitHub Actions reproducible, validaciones integradas y, desde R015, puerta de regresión automática. La referencia territorial vigente sigue siendo Run #8 hasta que una ronda funcional posterior produzca una nueva referencia aceptada.

## Ramas

`main` es la rama canónica activa. `infra/fuentes-reproducibles*` son ramas históricas/no activas salvo decisión documentada. No se eliminan ramas históricas sin aprobación explícita.

## Resultados

Cada ejecución usa `run_id` inmutable. El manifiesto identifica commit, versiones, parámetros, hashes de entradas, semilla, entorno, métricas, validaciones y hashes/rutas de salidas. Ningún resultado anterior se sobrescribe.
