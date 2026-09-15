# Integración de visor de ejecuciones y ruta integral Aragón — 2026-09-15

## Estado ejecutivo

Se ha cerrado la integración necesaria para dejar de trabajar con resultados territoriales invisibles o separados de la interfaz de revisión.

El visor técnico acepta ahora un segundo selector **Resultado** además de Territorio. Puede mostrar en el mismo entorno:

- productos históricos del repositorio;
- un M06 procedente de un run de GitHub Actions;
- un M08 electoral procedente del mismo run, cuando exista;
- candidatos de un ensemble GerryChain completo, incorporados como opciones del mismo combo.

Los GeoJSON grandes no se escriben en `main`: se recuperan desde artefactos o releases y se empaquetan para GitHub Pages en tiempo de despliegue.

## Evidencia Aragón ya disponible

El artefacto canónico de M01–M06 sigue siendo el run `34960965537`, con 1.463 secciones, 67 distritos, 4.063 aristas, `hard=0`, `fuera_12=0` y maxdev 0.11820424865218981.

Sobre el `aragon_2025_m06_secciones.geojson.zip` exacto de ese artefacto se ha ejecutado la nueva auditoría independiente de componentes geométricos. Resultado:

- 67 distritos evaluados;
- 60 geométricamente conexos;
- 7 bloqueados;
- decisión: `BLOCK`.

Distritos bloqueados: `0, 2, 4, 7, 9, 51, 63`.

El distrito 9 es especialmente material: su segunda componente representa aproximadamente el 35,0 % del área disuelta. Por tanto no procede tratar el problema como un simple artefacto microscópico de borde.

La evidencia compacta queda registrada en:

`docs/SALIDAS_CHATGPT/EVIDENCIAS/aragon_m06_contiguedad_geometrica_run_34960965537.json`

Esta conclusión no revoca la certificación previa de población, universo, cuotas provinciales ni conectividad por grafo. Añade una puerta más fuerte: el mapa certificado por grafo todavía no es promocionable como mapa territorial final.

## Cambios de visor

- `visor/index.html`: añade selector de resultado.
- `visor/app.js`: versión 1.3.0; consume `data/viewer-results.json`, permite cambiar M06/M08/ensembles y muestra el estado geométrico.
- `visor/styles.css`: adapta la cabecera y distingue visualmente estados PASS/BLOCK.
- `herramientas/preparar_visor_ejecucion.py`: construye el registro unificado y copia/descomprime únicamente los artefactos seleccionados.
- `legacy/visor/app_v1.2.0.js`: preservación del visor anterior.

## Despliegue manual inmediato

El workflow activo pasa a llamarse **Desplegar visor técnico**.

Permite indicar:

- `production_run_id`: run M06/M08 que se quiere visualizar;
- `ensemble_release_tag`: release de ensemble opcional.

Para visualizar inmediatamente el Aragón ya calculado debe usarse:

`production_run_id = 34960965537`

El workflow recupera el artefacto, incorpora la auditoría geométrica registrada y despliega Pages con el nuevo combo de resultados.

## Producción M01–M08 reforzada

`.github/workflows/producir-territorio-por-contrato.yml` sube a 1.3.0.

Después de cualquier ejecución que haya materializado M06:

1. conserva el resultado de la cadena aunque haya un fallo posterior;
2. ejecuta `herramientas/auditar_componentes_geometricos.py` sobre las secciones M06;
3. guarda `*_m06_contiguedad_geometrica.json` dentro del artefacto;
4. la conclusión final falla si la cadena M01–M08 falla o si la puerta geométrica bloquea;
5. `actions/upload-artifact` se ejecuta siempre, de modo que el mapa queda disponible para diagnóstico y visor incluso si no puede promocionarse.

La versión 1.2.0 queda en `legacy/workflows/producir-territorio-por-contrato_v1.2.0.yml`.

## Ensemble y visor unificado

`generar-alternativas-territoriales.yml` sube a 1.2.0.

Además de release borrador y posible Pages propio, un ensemble completo genera ahora el artefacto:

`ensemble-site-<run_key>`

que contiene la galería portable. El despliegue del visor puede ingerir ese artefacto/release y transformar cada candidato válido en una opción del combo de resultados. El parámetro reusable `deploy_pages` permite evitar que la galería GerryChain pise el visor general cuando se orqueste desde una ejecución superior.

## Ejecución de extremo a extremo

Se añade:

`.github/workflows/aragon-ejecucion-integral.yml`

Nombre visible: **Aragón — M01 a M08 y visor**.

Su objetivo es que el director haga una única autorización y obtenga:

1. reconstrucción de fuentes;
2. M01 → M08;
3. auditoría geométrica independiente si M06 existe;
4. artefacto completo aunque una puerta posterior bloquee;
5. visor Pages desplegado automáticamente con M06 y M08 disponibles.

La generación de ensembles se mantiene como operación separada hasta que Aragón supere la puerta geométrica. El visor ya está preparado para incorporarlos después mediante el combo.

## Orden operativo siguiente

1. Desplegar ya el run `34960965537` con **Desplegar visor técnico** para inspeccionar visualmente el M06 actual y los siete bloqueos.
2. Ejecutar **Aragón — M01 a M08 y visor** con `EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION` para comprobar toda la cadena electoral de inicio a fin y dejar M06/M08 visibles en Pages, aunque la puerta geométrica marque BLOCK.
3. Corregir el constructor/optimizador para eliminar las siete discontinuidades geométricas sin reintroducir contactos puntuales ni relajar población, provincia o disciplina municipal.
4. Repetir la ejecución integral hasta obtener `67/67` geométricamente conexos.
5. Solo entonces lanzar Aragón-10 GerryChain y añadir sus alternativas al combo del visor. Aragón-50 continúa bloqueado hasta revisión del piloto.
