# Reproducción de la validación visual aislada

Versión: 1.0.0 · Fecha: 2026-10-10 · Estado: navegador BLOQUEADO.
Alcance: evidencia y procedimiento local visual. Cambios/motivo: nuevo expediente por encargo Work.
Origen: nuevo documento, sin predecesor sustituido.

Desde `/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos`, el cotejo estático se reproduce sin motores ni dependencias nuevas:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 docs/AUDITORIAS/NACHO_VISUAL_2026-10-10/validar_evidencia.py
```

Salida esperada: `PASS_STATIC_ONLY`. Se escribe sólo `DATOS_RESULTADO.json` en este expediente. No acredita renderizado, consola ni controles. Un fallo inicial del harness nuevo utilizó un diccionario para el SHA de asignación; la convención congelada es una lista de16 distritos. Se corrigió esa lectura y pasó el cotejo; no era un defecto del prototipo ni se cambiaron sus datos.

El diagnóstico puede abrirse directamente por su ruta `docs/AUDITORIAS/NACHO_VALIDACION_2026-10-10/visualizacion/diagnostico.html`. La galería necesita HTTP para `fetch` y MapLibre5.6.0, ya referenciado por su HTML mediante CDN. Procedimiento pendiente en entorno autorizado con navegador operativo (no ejecutado aquí):

```sh
python3 -m http.server 8767 --bind 127.0.0.1 --directory docs/AUDITORIAS/NACHO_VALIDACION_2026-10-10/visualizacion
```

Abrir `http://127.0.0.1:8767/diagnostico.html` y `http://127.0.0.1:8767/gallery/index.html`. El servidor sirve sólo la carpeta visual por loopback; detenerlo al terminar. Verificar hashes contra `IDENTIDAD.json` antes y después. No ejecutar `validate.py`, motores ni scripts de generación para esta tarea.

Para reproducir el intento Firefox registrado usando un perfil nuevo y sin desactivar sandbox:

```sh
DDD_VISUAL_PROFILE=$(mktemp -d /private/tmp/ddd-nacho-visual-firefox.XXXXXX)
"/Applications/Firefox.app/Contents/MacOS/firefox" --headless --no-remote --profile "$DDD_VISUAL_PROFILE" --window-size 1440,1200 --screenshot /private/tmp/ddd-nacho-diagnostico.png "file://$PWD/docs/AUDITORIAS/NACHO_VALIDACION_2026-10-10/visualizacion/diagnostico.html"
```

Comando original exacto, perfil usado y resultado en `BROWSER_ATTEMPT.json`. Alternativa intentada: `/usr/bin/safaridriver --port 8766`; falló antes de una sesión y se conservó el resultado. No repetir lanzamientos si continúa el mismo bloqueo ni modificar la seguridad del entorno.

Procedimiento visual pendiente, con consola del navegador abierta:

1. Diagnóstico: capturar página completa y mapas/tablas legibles; comprobar las 12 filas frente a `DATOS_RESULTADO.json`. Accionar fronteras y mostrar/ocultar C, conservando una captura de cada estado. Confirmar etiquetas sintéticas, cuatro fallos C y ausencia de excepción autorizada. Comprobar una vista estrecha y teclado; anotar dimensiones y versión de navegador.
2. Galería: comprobar carga efectiva de ambos mapas y16 features, cambio A/B, zoom/desplazamiento y navegación. No hay popup ni selección individual de distritos ni leyenda explícita implementados: registrarlo como capacidad ausente. Cambiar perfil y Pareto (sólo B en tarjetas), seleccionar candidato A/B, llenar responsable/justificación y capturar el estado. Exportar únicamente una solicitud local; verificar literal/schema/datos y que C no sea seleccionable. No ejecutar ningún promotor.
3. Guardar consola, solicitudes fallidas y capturas sin ocultar errores. Verificar que filtros de tarjetas no se presenten como filtros de mapas: el código los aplica sólo a tarjetas. Separar fallos ambientales/CDN de defectos del prototipo. Si aparece una dependencia de cambios del motor, detenerse.

Las capturas y estos controles **no se completaron en esta sesión**. El dictamen está en [INFORME.md](INFORME.md). La revisión de Madrid permanece fuera de alcance.
