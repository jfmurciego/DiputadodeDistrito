# Continuidad general del proyecto — abrir un nuevo chat

**Versión:** 2.0.0
**Fecha de corte:** 2026-09-11
**Anterior:** `legacy/memoria/CONTINUIDAD_NUEVO_CHAT_v1.6.0.md`

## Fuente de verdad

El repositorio privado `jfmurciego/DiputadodeDistrito`, rama `main`, manda sobre la memoria del chat. No reconstruir decisiones desde recuerdos si GitHub contiene evidencia.

## Punto exacto

R014, R015 y R016 están cerrados. Aragón Run #9 `34599224954` es el baseline territorial vigente: 67 distritos, 1.463 secciones, 1.364.621 habitantes, reparto 11/7/49, `fuera_12=0`, contigüidad/provincia/municipios/suelo/techo PASS, máximo desvío 9,930 %. M05 v7.4.0 es la lógica validada.

R018 reorganiza el repositorio para multi-territorio sin cambiar el mapa. El motor común queda en `ddd_core/`, `modulos/` y `herramientas/`; los territorios viven en `territorios/`.

## Regla estructural

Un repositorio. Una rama permanente (`main`). Un motor. Cada territorio es un paquete con `config/`, `inputs/`, `docs/`, `tests/` y referencia de resultados. No crear repositorios o ramas permanentes por comunidad.

## Implantaciones

### Aragón
`territorios/aragon/` es la implantación de referencia. Run #9 sigue protegido. R017 de auditoría de calidad territorial fina queda pendiente para retomarse en el hilo de Aragón.

### Castilla y León
`territorios/castilla_y_leon/` es la siguiente implantación. Abrir un chat nuevo usando **`docs/CONTINUIDAD_CASTILLA_Y_LEON.md`** como prompt/brief principal. Su misión es probar la generalidad del motor, no copiar Aragón.

## Compatibilidad R018

Las rutas raíz `configuracion/`, `inputs/` y `resultados/ejecuciones/` se conservan temporalmente porque el workflow GitHub de Aragón validado todavía las usa. Son compatibilidad transitoria. El desarrollo nuevo debe dirigirse a `territorios/`.

`procedimiento.sh` v2.2.0 ya es multi-territorio a nivel de lanzador: recibe `DDD_PARAMS` y deriva `run_name` del YAML, sin nombre de Aragón codificado en caché.

## Documentos a leer

1. `README.md`.
2. `docs/ESTADO_MAESTRO_PROYECTO.md`.
3. `docs/ARQUITECTURA_MULTI_TERRITORIO.md`.
4. `docs/CONTRATO_TERRITORIO.md`.
5. `docs/POLITICA_DE_VERSIONES.md`.
6. Contratos M01–M08 en `docs/MODULOS/`.
7. Si se trabaja Aragón: `territorios/aragon/README.md` + Run #9.
8. Si se trabaja Castilla y León: `docs/CONTINUIDAD_CASTILLA_Y_LEON.md` + `territorios/castilla_y_leon/README.md`.

## Gobernanza

Toda sustitución versionada conserva primero el predecesor inmediato en `legacy/`. No fabricar versiones históricas. No reescribir un artefacto ya validado solo para cambiar una etiqueta. CI automática obligatoria; cambio funcional territorial requiere además nuevo run reproducible.

## Criterio de madurez

La pregunta clave ya no es cuánto se puede perfeccionar Aragón, sino **cuánto código común hay que cambiar para añadir Castilla y León y después Extremadura**. El objetivo final es cero cambios del motor para un nuevo territorio normal: solo datos, configuración, reglas y tests.
