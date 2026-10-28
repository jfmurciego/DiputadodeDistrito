# Reproducción de la validación experimental

Versión1.0.0 · 2026-10-10. Informe: [INFORME.md](INFORME.md). Evidencia congelada: `mediciones/` y `visualizacion/`. Los scripts son de investigación y usan los motores existentes sin cambios. No ejecutarlos sobre territorios productivos. No requieren instalar dependencias.

## Verificar la entrega sin ejecutar motores

Desde el worktree indicado:

```sh
python3 - <<'PY'
import hashlib,json
from pathlib import Path
p=Path('docs/AUDITORIAS/NACHO_VALIDACION_2026-10-10')
m=json.loads((p/'MANIFIESTO.json').read_text())
for relative,expected in m['files'].items():
    assert hashlib.sha256((p/relative).read_bytes()).hexdigest()==expected,relative
print('PASS',len(m['files']),'archivos')
PY
```

El manifiesto cubre fuentes aisladas, fixtures, mediciones, configuraciones, logs, informe y revisión; se excluye a sí mismo. `CONSERVACION.json` comprueba el baseline de producción/cambios preexistentes e investigación anterior. El informe conserva los SHA de cada fixture y cada run E2 conserva los SHA del código productivo realmente cargado. HEAD sin esos SHA es insuficiente.

## Repetir las mediciones en otra carpeta temporal

Las siguientes líneas son **procedimiento posterior reproducible**, no nuevas ejecuciones durante la entrega. Los doce motores sintéticos tardaron aproximadamente un minuto en total; el presupuesto es por proceso, no para el conjunto. El entorno indicado ya estaba instalado y se utilizó tal cual. Si ese directorio deja de existir, se bloqueará la reproducción: no instalar automáticamente; solicitar autorización de Work para restaurar las versiones registradas en `mediciones/entorno.json`.

```sh
cd /Users/macbookpro/Desarrollo/DDD-distritos-autonomicos
DDD_VALIDACION_COPY=$(mktemp -d /private/tmp/ddd-nacho-repro.XXXXXX)
cp -R docs/AUDITORIAS/NACHO_VALIDACION_2026-10-10/mediciones "$DDD_VALIDACION_COPY/mediciones"
cp -R docs/AUDITORIAS/NACHO_VALIDACION_2026-10-10/visualizacion "$DDD_VALIDACION_COPY/visualizacion"
```

Experimento1: seis subprocess, misma entrada extraída, timeout30 s cada uno. No se necesita el archivo territorial completo ni una descarga: sus tres miembros están incluidos.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 /private/tmp/madrid-gerrychain-venv/bin/python "$DDD_VALIDACION_COPY/mediciones/contraccion.py" --fixture "$DDD_VALIDACION_COPY/mediciones/fixture-e1"
```

Experimento2: congela otra vez A/B a partir de la evidencia anterior intacta, ejecuta seis parejas y calcula el resumen. `baseline_invalida.py` sólo comprueba el rechazo de C antes de cadena. `sumarizar.py` no ejecuta motores. Las rutas absolutas de fuente/worktree están declaradas al principio de los scripts; para otra máquina deben apuntar a una copia de **estas mismas fuentes SHA**. Las timings no serán bit a bit iguales.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 /private/tmp/madrid-gerrychain-venv/bin/python "$DDD_VALIDACION_COPY/mediciones/comparar_m05.py"
PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 /private/tmp/madrid-gerrychain-venv/bin/python "$DDD_VALIDACION_COPY/mediciones/baseline_invalida.py"
PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 /private/tmp/madrid-gerrychain-venv/bin/python "$DDD_VALIDACION_COPY/mediciones/sumarizar.py"
```

Experimento3: ensambla reportes copiados, reconstruye assets de asignaciones ya existentes y prueba funciones JS, sin generar distritos. `validate.py` documenta el bloqueo Chrome previamente ocurrido y no vuelve a intentarlo. Los resultados de DOM/MapLibre son simulados; las pruebas del visor son funciones puras.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 /private/tmp/madrid-gerrychain-venv/bin/python "$DDD_VALIDACION_COPY/visualizacion/validate.py"
PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 /private/tmp/madrid-gerrychain-venv/bin/python "$DDD_VALIDACION_COPY/visualizacion/run_js.py"
PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 /private/tmp/madrid-gerrychain-venv/bin/python "$DDD_VALIDACION_COPY/visualizacion/run_visor_check.py"
```

El entorno macOS utilizado incluye `/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc`. Si falta, identificar estas dos pruebas JS como bloqueadas; no sustituirlas por una lectura estática pretendiendo que se ejecutaron. Los scripts establecen timeout60 s, CPU55 s y límite DATA640 MiB para sus subprocess JS.

## Comprobación posterior del navegador bloqueado

El [diagnóstico offline](visualizacion/diagnostico.html) tiene SVG y controles sin CDN. El intento de navegador de esta sesión quedó bloqueado por `bootstrap EPERM`; este comando es **pendiente de ejecución en un entorno autorizado**, no resultado acreditado ni petición para relajar el sandbox actual:

```sh
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --disable-background-networking --allow-file-access-from-files --timeout=15000 --screenshot="$DDD_VALIDACION_COPY/diagnostico.png" "file://$DDD_VALIDACION_COPY/visualizacion/diagnostico.html"
```

Abrir también el HTML en navegador autorizado; verificar simultáneamente A/B, tabla de12 distritos, límites800/1750/banda800–1200, texto de selección B y causas C; accionar fronteras y mostrar/ocultar rechazado. Registrar screenshot y DOM junto con versión de navegador. Para la galería real, servir la copia local de `gallery/` y assets y disponer de MapLibre conforme a la política del entorno (la galería existente referencia CDN); verificar los mismos controles ya probados lógicamente y la carga de mapas real. No adjudicar render/usabilidad hasta completar esa prueba. C debe seguir fuera de controles de selección.

## Archivos principales

- [e1-results.json](mediciones/e1-results.json): seis mediciones de contracción, integridad y memoria.
- [e2-results.json](mediciones/e2-results.json): doce motores, seis parejas y decisiones; `e2-runs/` conserva parámetros, reports, outputs, traces y comandos.
- [e2-negative-baseline.json](mediciones/e2-negative-baseline.json): rechazo efectivo del candidato C.
- [validation_results.json](visualizacion/validation_results.json) y [VISOR_COMPARACION.md](visualizacion/VISOR_COMPARACION.md): pruebas actuales de ensemble/galería/visor y alcance de la simulación.
- [ESPECIFICACION.md](visualizacion/ESPECIFICACION.md), [diagnostico.html](visualizacion/diagnostico.html) y [comparison.csv](visualizacion/comparison.csv): propuesta informativa aislada para decisión de Work.

Las especificaciones son candidatas técnicas. No constituyen autorización de integración, certificación, cambio de contratos ni de presupuesto A2.
