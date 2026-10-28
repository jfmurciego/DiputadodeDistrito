# Expediente de investigación Nacho / DDD

Versión1.0.0 · 2026-10-10 · Documento nuevo · Origen: encargo Work. Alcance: investigación y experimentos sintéticos aislados. Sin integración funcional, acciones externas de escritura, datos oficiales nuevos ni certificación territorial.

Entrada principal: [INFORME.md](INFORME.md). Detalle de estructuras, dependencias y fórmulas: [PARAMETROS.md](PARAMETROS.md). Inventario de56 correspondencias: [inventario.tsv](inventario.tsv). Evidencias: [historial](historial.json), [ZIP histórico cifrado](archivo-historico.json), [baseline](manifiesto-inicio.json), [preservación](preservacion.json), [PR relacionadas](prs-relacionadas.json), [micropruebas](microchecks.json), [experimentos y límites](experimentos/README.md). Dictamen separado: `REVISION.md` al cerrar la puerta de revisión. Manifest final: `manifest-final.json`.

## Reproducción sin sobrescribir este expediente

Entorno ejecutado: Python3.11.4, Shapely2.1.1, macOS11.7.11; ejecutable existente `/private/tmp/ddd-cartografia-venv/bin/python`. Sin instalación ni GerryChain. Los scripts importan DDD desde el worktree declarado en su encabezado; conservar sus hashes de fuente o declarar una comparación nueva. Los resultados de tiempo pueden cambiar entre ejecuciones. Los scripts E1–E3 y E5 escriben junto a sí mismos: copiarlos primero a un directorio temporal distinto.

```sh
RUN_DIR=$(mktemp -d /private/tmp/ddd-nacho-reproduce.XXXXXX)
cp -R docs/AUDITORIAS/NACHO_2026-10-10/experimentos "$RUN_DIR/experimentos"
/private/tmp/ddd-cartografia-venv/bin/python "$RUN_DIR/experimentos/experiments.py"
python3 "$RUN_DIR/experimentos/graph_contraction.py"
/private/tmp/ddd-cartografia-venv/bin/python docs/AUDITORIAS/NACHO_2026-10-10/microchecks.py "$RUN_DIR/microchecks"
```

`experiments.py` compara mecanismos de postprocesado, no una cadena. `graph_contraction.py` mide validación de asignaciones municipales preconstruidas, no generación. Cada benchmark usa subprocess con timeout60s. E4 micropruebas no emplea un dataset territorial; la reanudación usa artefactos mock autoconsistentes. No confundir aceptación del mock por la función de identidad con certificación.

El código archivado del investigador `inventario.py` puede ejecutarse con un directorio de salida como primer argumento; requiere clon histórico completo existente en `/private/tmp/nplaton-diputado-distrito`. Reconstruye hashes y metadatos, sin ejecutar cuadernos ni imprimir SQL o credenciales. Su salida de baseline refleja el momento de la reejecución: no reemplaza al manifiesto ya conservado. Los dos scripts raíz se adaptaron para salida temporal configurable tras ejecutarse sus mecanismos originales; no cambia el cálculo de las pruebas. La evidencia original E4 permanece en `microchecks.json`.

Los43 hashes del manifest del agente de experimentos se comprobaron después de copiarlo íntegro; son sus bytes originales. `historial.json` incluye hashes y posiciones de mecanismos, no código del notebook. No se presume licencia para reutilizar código de Nacho. Consultar el repositorio/commit original para las referencias de celdas.

## Gobierno y entrega

Work decide la implementación posterior. A2/A3 preexistentes, A1 y N1/N2 se preservan. No se escribe en DDD-control porque está fuera de los directorios autorizados; no se alteran sus estados. Este expediente es el checkpoint local de investigación. Las56 filas cubren todos los componentes actuales y decisiones históricas relevantes accesibles. La contraseña del ZIP y el wheel exacto GerryChain0.2.12 faltan; el informe documenta esos límites y no atribuye resultados empíricos al algoritmo histórico completo.

Esta entrega queda en archivos nuevos del worktree. No hay commit: los metadatos Git están montados de sólo lectura en este entorno y no se solicitó una integración. No hay CI nueva ni autorización para workflows. La revisión de otra sesión Codex aporta separación operativa; no es aprobación externa de producción.
