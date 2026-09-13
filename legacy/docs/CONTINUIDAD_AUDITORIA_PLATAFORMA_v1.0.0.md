# Continuidad de la auditoría de plataforma DDD

**Versión:** 1.0.0
**Fecha de corte:** 2026-09-13
**Estado:** VIGENTE — fuente de migración al nuevo hilo
**Commit de partida:** `c0c1bf5` (`R035.1: certificar y cerrar línea de producción`)
**Anterior:** ninguno — documento nuevo
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

### Abierto

- [ ] **R036 — Política de K.** Definir el origen y la justificación auditable de `k_districts`; decidir si vive en catálogo, contrato o ambos y validar coherencia.
- [ ] **R036 — Contrato general de límites.** Fijar valores heredados por defecto y exigir motivo/versionado para toda desviación territorial; no elegir umbrales después de ver resultados.
- [ ] **R036 — Esquema único.** Formalizar versión y campos obligatorios, además del validador ejecutable ya existente; distinguir claramente `bootstrap M01–M03` de `production M01–M06`.
- [ ] **R037 — Aislados y desconexiones.** Convertir los diagnósticos existentes en políticas explícitas de admisión/reparación/bloqueo.
- [ ] **R037 — Archipiélagos.** Decidir y documentar qué significa contigüidad entre islas antes de crear carpetas o ejecutar Baleares/Canarias.
- [ ] **R038 — Workflows.** Archivar los territoriales de Extremadura y los falsos genéricos que hayan quedado sustituidos por la línea común; dejar claro cuál es operativo y cuál es histórico.
- [ ] **R038 — Herramientas experimentales.** Clasificar los auditores de un uso: destilar estrategias reutilizables o moverlos a `legacy/`; no borrarlos sin conservar historia.
- [ ] **R038 — Documentación.** Corregir afirmaciones aspiracionales sobre CUSEC/provincias y extender la prohibición de acoplamiento territorial a workflows y validadores.
- [ ] **R039 — Capa electoral.** Crear contrato común de convocatoria, adquisición o entrada verificable, diccionario de partidos y normalización; hoy M07–M08 siguen siendo Aragón.
- [ ] **R040 — Prueba ciega.** Cuando exista autorización explícita, ejecutar La Rioja sin tocar `.github/workflows/`, `modulos/` ni `ddd_core`; después Cantabria para probar el caso degradado.
- [ ] **Publicación.** Pages sigue dependiendo de habilitación del propietario; el artefacto descargable ya evita que ese permiso bloquee la entrega.

## 3. Orden de trabajo del nuevo hilo

1. Leer este documento, `docs/SALIDAS_CHATGPT/PUNTO_REENGANCHE.md`, `docs/CIERRE_INGENIERIA_PRODUCCION.md`, el estado G10 y la auditoría externa completa aportada por el usuario.
2. Verificar `main`, CI, workflows activos e issue #5 antes de cambiar nada.
3. Ejecutar R036 sin cálculo territorial: política de K, límites heredados, excepciones y esquema único.
4. Ejecutar R037 sin abrir comunidades: contratos de topología para aislados, desconexiones y archipiélagos.
5. Ejecutar R038: limpieza/versionado de workflows, auditores y documentación.
6. Ejecutar R039: contrato y línea electoral común, con pruebas sintéticas o fixtures; no alterar productos canónicos.
7. Mantener R040 bloqueada hasta autorización expresa. La prueba debe ser falsable y no permitir código específico del territorio.
8. Incorporar los demás hallazgos de Claude a esta lista conforme se aporten; no limitar la revisión al informe reproducido en el chat anterior.

## 4. Reglas inviolables

- No ejecutar nuevas comunidades ni recalcular M01–M06 de Aragón o Castilla y León salvo cambio material de huella/contrato **y** orden explícita.
- No recalcular Extremadura ni cambiar su contrato para hacerla aprobar; sigue siendo evidencia experimental bloqueada.
- No declarar «cualquier territorio» hasta superar R040.
- Cada cambio lleva versión, copia anterior en `legacy/`, entrada en `docs/REGISTRO_DE_CAMBIOS.md` y actualización del reenganche.
- GitHub es la fuente de verdad. Los resultados certificados se reutilizan; la existencia de un fichero por sí sola no basta sin huella/evidencia.
- Comunicar al director del proyecto sólo estado, hito cerrado, faltantes, riesgo/decisión y siguiente paso. Los detalles técnicos quedan en GitHub.

## 5. Definición de terminado

La plataforma podrá llamarse genérica cuando un territorio peninsular nuevo se admita por catálogo/contrato, recorra la misma cadena M01–M06 y deje evidencia sin tocar código común; un caso con aislamiento tenga una política reproducible; los archipiélagos tengan contrato topológico explícito; y M07–M08 puedan producir un producto electoral sin tablas artesanales de Aragón.

Hasta entonces, la metáfora correcta es: **la cinta transportadora y la puerta de seguridad ya existen, pero todavía faltan las reglas universales de corte y la sección electoral de la fábrica.**

## 6. Enlaces operativos

- Repositorio: https://github.com/jfmurciego/DiputadodeDistrito
- Issue operativo: https://github.com/jfmurciego/DiputadodeDistrito/issues/5
- CI certificada R035: https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34747763671
- Workflow común: `.github/workflows/producir-territorio-por-contrato.yml`
- Puerta de contrato: `ddd_core/territory_contract.py`
