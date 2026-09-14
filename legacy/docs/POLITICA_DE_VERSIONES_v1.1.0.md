# Política de versiones y conservación

**Versión:** 1.1.0 — Gobernanza canónica y deuda histórica  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/docs/POLITICA_DE_VERSIONES_v1.0.0.md`

## Regla inviolable

Ningún fichero funcional existente se sustituye sin conservar previamente su contenido anterior en `legacy/`. Git conserva el historial, pero `legacy/` es la capa explícita de arqueología inspeccionable sin reconstruir commits.

La regla se aplica obligatoriamente a partir de la adopción de esta política. Los huecos heredados de la recuperación inicial se documentan como **deuda histórica**; nunca se rellenan con contenido inventado ni se declara recuperada una versión que no existe.

## Versionado

Se usa `MAJOR.MINOR.PATCH`:
- **MAJOR:** cambia contrato, algoritmo fundamental o compatibilidad de entradas/salidas.
- **MINOR:** mejora funcional compatible o modificación sustancial de comportamiento.
- **PATCH:** corrección sin cambio de contrato.

El fichero activo mantiene nombre estable. La versión retirada se conserva en `legacy/<familia>/..._vA.B.C.*`.

## Cabecera obligatoria

Código ejecutable, configuración y workflows versionados deben declarar, cuando el formato lo permita: proyecto/componente, versión, nombre de versión, fecha, función, entradas/salidas o alcance, cambios, motivo y predecesor.

Si existe predecesor materializado en `legacy/`, la cabecera debe apuntar a su ruta real. Si no fue recuperado, debe decir **`PREDECESOR HISTÓRICO NO RECUPERADO`** u **`ORIGEN: baseline recuperado`**. Queda prohibido referenciar una ruta inexistente como si fuese una copia disponible.

Outputs generados, datos fuente congelados y formatos que no admiten cabecera textual quedan exentos; su trazabilidad se resuelve mediante manifiestos, hashes y documentación asociada.

## Estado canónico

Los documentos vigentes de estado son:
1. `README.md`;
2. `docs/ESTADO_MAESTRO_PROYECTO.md`;
3. `docs/CONTINUIDAD_NUEVO_CHAT.md`;
4. `docs/BITACORA.md`;
5. `docs/REGISTRO_DE_CAMBIOS.md`.

Los antiguos `docs/MEMORIA_DEL_PROYECTO.md` y `docs/MEMORIA_PROYECTO.md` están retirados. **No deben volver a actualizarse ni utilizarse como fuente canónica.**

## Procedimiento de cambio

Todo cambio funcional exige:
1. conservar primero la versión anterior en `legacy/`;
2. incrementar versión;
3. actualizar cabecera/metadatos;
4. registrar el cambio en `docs/REGISTRO_DE_CAMBIOS.md`;
5. actualizar Estado Maestro, Continuidad, Bitácora y README cuando cambie el estado que comunican;
6. usar un commit identificable;
7. registrar ejecución y resultado cuando el cambio sea ejecutable.

Los cambios puramente documentales también archivan el documento anterior cuando éste tiene versión explícita.

## Aceptación

Una ejecución local, simulación o sesión de IA es diagnóstico. La aceptación del procedimiento exige GitHub Actions reproducible y las validaciones integradas aplicables. La ausencia actual de una suite unitaria completa se registra como deuda de ingeniería; no se oculta ni convierte una ejecución local en evidencia equivalente.

## Ramas

`main` es la rama canónica activa. Las ramas `infra/fuentes-reproducibles*` se consideran históricas/no activas mientras no exista una decisión documentada de reactivación. No se eliminan ramas históricas sin aprobación explícita.

## Resultados

Cada ejecución usa `run_id` inmutable. El manifiesto debe identificar commit, versiones, parámetros, hashes de entradas, semilla, entorno, métricas, validaciones y hashes/rutas de salidas. Ningún resultado anterior se sobrescribe.
