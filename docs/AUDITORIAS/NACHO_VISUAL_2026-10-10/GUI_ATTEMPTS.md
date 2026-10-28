# Intentos de apertura normal

Versión: 1.0.0 · Fecha: 2026-10-10 · Alcance: apertura del diagnóstico local en aplicaciones instaladas.
Estado: BLOQUEADO; ninguna aplicación llegó a una página capturable.
Origen: continuación de la validación autorizada por Work; sin predecesor sustituido.

El primer comando de macOS `open -a Safari "file:///.../diagnostico.html"` trató esa URL como una ruta relativa. Se descartó; no cuenta como una apertura válida. La consulta AppleScript posterior informó que no podía acceder a Safari. Se corrigió el comando pasando directamente aplicación y archivo:

```sh
open -a /Applications/Safari.app /Users/macbookpro/Desarrollo/DDD-distritos-autonomicos/docs/AUDITORIAS/NACHO_VALIDACION_2026-10-10/visualizacion/diagnostico.html
```

Resultado: código1, LaunchServices `NSOSStatusErrorDomain -10822`, `kLSServerCommunicationErr`; indica que el proceso del servidor de registro/recent items no está disponible. Ninguna ventana/página quedó abierta.

Intento Firefox normal, ejecución directa y perfil aislado:

```sh
/Applications/Firefox.app/Contents/MacOS/firefox --no-remote --new-instance --profile /private/tmp/ddd-nacho-visual-firefox-gui-726_8s0d file:///Users/macbookpro/Desarrollo/DDD-distritos-autonomicos/docs/AUDITORIAS/NACHO_VALIDACION_2026-10-10/visualizacion/diagnostico.html
```

Firefox157.0.1 terminó en0,091s con `returncode=-6`; stdout/stderr vacíos; ninguna captura. Evidencia: [BROWSER_ATTEMPT_GUI.json](BROWSER_ATTEMPT_GUI.json), [firefox_gui.stdout.log](firefox_gui.stdout.log) y [firefox_gui.stderr.log](firefox_gui.stderr.log). No se desactivó el sandbox ni se modificaron preferencias del sistema.

Conclusión limitada: las aplicaciones no arrancan en esta sesión por el estado del entorno local; no se cargó ni ejecutó el prototipo y no se generaron capturas. El fallo de LaunchServices precisa el error del sistema devuelto; no se atribuye una causa más específica a Firefox.
