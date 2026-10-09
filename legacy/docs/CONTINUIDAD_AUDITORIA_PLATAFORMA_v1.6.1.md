# Continuidad de la auditoría de plataforma DDD

**Versión:** 1.6.1
**Fecha de corte:** 2026-09-14
**Estado:** VIGENTE — fuente de migración al nuevo hilo
**Commit de partida:** `4b8af76` (`R036.0: registrar migración de auditoría`)
**Anterior:** `legacy/docs/CONTINUIDAD_AUDITORIA_PLATAFORMA_v1.6.0.md`
**Propósito:** permitir que otra sesión continúe la auditoría y la ingeniería sin depender del chat anterior ni repetir resultados territoriales.

## 1. Veredicto que debe conservarse

La auditoría externa sobre `b33c96b` concluyó correctamente que la plataforma no podía procesar cualquier territorio. Después de ese corte, R034 y R035 corrigieron dos bloqueos importantes: existe una puerta de admisión contractual previa al cálculo y existe una interfaz/workflow único que deriva la ejecución del YAML sin seleccionar Aragón o Castilla y León en código.

Eso **no demuestra aún** que la plataforma nacional esté terminada. R035 certifica la interfaz común, no la producción ciega de un territorio nuevo. La documentación anterior que afirmaba que no quedaban tareas de ingeniería base queda corregida por este documento y por `docs/CIERRE_INGENIERIA_PRODUCCION.md` v1.2.0.

## 2. Estado actual verificado

### Cerrado

- [x] Aragón y Castilla y León conservan sus productos certificados; no se han recalculado.
- [x] Extremadura permanece `EXPERIMENTAL_BLOCKED`; no se ha promovido.
- [x] R034 valida antes de M01: identidad, fuentes con checksum, contrato, módulos M01–M06, continuidad de artefactos, K, límites y confinamiento de rutas.
- [x] R035 aporta `Producción territorial por contrato`, con modos sin cálculo y autorización literal obligatoria para `execute`.
- [x] G10 dispone de huellas, estado durable y checkpoints; una publicación no debe reactivar el motor territorial.
- [x] El visor y los productos públicos de Aragón/Castilla y León se validan y empaquetan sin depender de Pages.
- [x] CI de R035: run `34747763671`, `SUCCESS`; no ejecutó M01–M06.
- [x] R036 certificado en commit `3d1337c`: cinco workflows SUCCESS; gobierno de K, perfil general `0.80/1.75/0.12`, excepciones y esquema `bootstrap`/`production`.
- [x] R037 certificado en commit `8376276`, CI `34757140425` SUCCESS; no ejecutó ni disparó regresiones territoriales.

### Abierto

- [x] **R036 — Política de K.** El catálogo gobierna procedencia/justificación y el contrato conserva el valor ejecutable; la puerta exige coherencia.
- [x] **R036 — Contrato general de límites.** Perfil general `0.80/1.75/0.12`; toda excepción exige motivo, evidencia y fecha previos.
- [x] **R036 — Esquema único.** Familia `ddd-territory`, versión de contrato y niveles `bootstrap_m01_m03` / `production_m01_m06` formalizados.
- [x] **R037 — Aislados y desconexiones.** R023 se convierte en bloqueo explícito; toda reparación futura exige pasarela tipada, motivada y con fuente.
- [x] **R037 — Archipiélagos.** Contigüidad interna por componente, sin aristas marítimas ni distritos entre islas; K se reparte antes de M04.
- [x] **R038 — Operación limpia.** Diez workflows sustituidos están en `legacy/workflows/r038`; la interfaz manual y la línea contractual son las únicas interfaces territoriales activas. CI `34830677071` SUCCESS.
- [x] **R039 — Capa electoral.** Contrato `ddd-election` 1.0.0, entrada con SHA-256 y procedencia, adaptadores declarativos, diccionario canónico cerrado y unión M08 exhaustiva. Aragón es la implantación de referencia; el código común no contiene tablas territoriales. CI `34833051502` SUCCESS.
- [ ] **R040 — Prueba ciega.** Cuando exista autorización explícita, ejecutar La Rioja sin tocar `.github/workflows/`, `modulos/` ni `ddd_core`; después Cantabria para probar el caso degradado.
- [ ] **Publicación.** Pages sigue dependiendo de habilitación del propietario; el artefacto descargable ya evita que ese permiso bloquee la entrega.

## 3. Orden de trabajo del nuevo hilo

**Prioridad rectora corregida:** cerrar la auditoría crítica C-01–C-14 antes de R038–R040 o de cualquier expansión territorial. El primer paquete es C-05/C-09 sobre M07. R038–R040 quedan suspendidos, no cancelados.

1. Leer este documento, `docs/SALIDAS_CHATGPT/PUNTO_REENGANCHE.md`, `docs/CIERRE_INGENIERIA_PRODUCCION.md`, el estado G10 y la auditoría externa completa aportada por el usuario.
2. Verificar `main`, CI, workflows activos e issue #5 antes de cambiar nada.
3. Cerrar el Paquete A: C-05 completo y la parte M07 de C-09, sin recalcular M01–M06.
4. Resolver por paquetes los restantes C-01–C-14, empezando por la decisión de publicabilidad C-14/C-02/C-03.
5. Mantener R040 suspendido hasta orden expresa; R038 y R039 están cerrados sin cálculo territorial.
6. Mantener R040 además bloqueada hasta autorización expresa. La prueba debe ser falsable y no permitir código específico del territorio.

## 4. Reglas inviolables

- No ejecutar nuevas comunidades ni recalcular M01–M06 de Aragón o Castilla y León salvo cambio material de huella/contrato **y** orden explícita.
- No recalcular Extremadura ni cambiar su contrato para hacerla aprobar; sigue siendo evidencia experimental bloqueada.
- No declarar «cualquier territorio» hasta superar R040.
- Cada cambio lleva versión, copia anterior en `legacy/`, entrada en `docs/REGISTRO_DE_CAMBIOS.md` y actualización del reenganche.
- GitHub es la fuente de verdad. Los resultados certificados se reutilizan; la existencia de un fichero por sí sola no basta sin huella/evidencia.
- Comunicar al director del proyecto sólo estado, hito cerrado, faltantes, riesgo/decisión y siguiente paso. Los detalles técnicos quedan en GitHub.

## 5. Definición de terminado

La plataforma podrá llamarse genérica cuando un territorio peninsular nuevo se admita por catálogo/contrato, recorra la misma cadena M01–M06 y deje evidencia sin tocar código común; un caso con aislamiento tenga una política reproducible; los archipiélagos tengan contrato topológico explícito; y M07–M08 puedan producir un producto electoral sin tablas artesanales de Aragón.

Tras R039, la cinta, la puerta de seguridad, las reglas de corte y la sección electoral común existen. La afirmación «cualquier territorio» continúa prohibida hasta superar R040 con autorización expresa.

## 6. Enlaces operativos

- Repositorio: https://github.com/jfmurciego/DiputadodeDistrito
- Issue operativo: https://github.com/jfmurciego/DiputadodeDistrito/issues/5
- CI certificada R035: https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34747763671
- Workflow común: `.github/workflows/producir-territorio-por-contrato.yml`
- Puerta de contrato: `ddd_core/territory_contract.py`
