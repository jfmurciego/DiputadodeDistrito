DDD auto 1.2.2 — 2026-10-13. Alcance: infraestructura local transversal candidata; sin autoridad productiva.
Predecesor: legacy/1.2.1/AUTO.md; cambios: proyección trazable de IDs canónicos del catálogo desde el registro maestro más amplio; motivo: permitir que el controlador acote su ámbito sin exigir que el Plan carezca de tareas independientes.

Se amplía el ddd existente. No se introduce planificador ni catálogo alternativo: cada ID de las 32 fichas del catálogo manual debe aparecer exactamente una vez en estado.json del Plan autoritativo. El controlador proyecta esas coincidencias exactas y registra `task_id_mapping` (identidad ID-a-ID), `excluded_plan_task_ids`, los estados seleccionados y el SHA-256 del Plan completo. No renombra IDs ni altera el Plan. IDs canónicos ausentes o duplicados bloquean; para las tareas seleccionadas, dependencias, frente, ejecución, aceptación y estados se contrastan con el catálogo y el grafo se valida. Las tareas ajenas al catálogo quedan fuera del snapshot operativo; duplicados en cualquier parte siguen bloqueando. Los PASS administrativos se conservan y las incoherencias de ascendencia formal se muestran. TECH_PASS requiere validadores y revisión; no constituye cierre administrativo.

Las campañas de 1.2.1 pueden reanudarse si el Plan completo conserva exactamente los mismos bytes y no contiene IDs externos a las fichas canónicas. Un Plan con entradas adicionales o cualquier cambio de contenido no supera esta compatibilidad histórica y requiere una campaña nueva.

```sh
ddd auto --plan RUTA --front all --pilot --dry-run
ddd auto --plan RUTA --front all --pilot --run
ddd auto --plan RUTA --status
```

Para probar esta entrega sin instalar, sustituir ddd por `python3 infraestructura/ordenes-manuales/ddd.py`. --status y --dry-run no escriben ni invocan Codex. --run exige --pilot. --front acepta all y los nombres canónicos de los tres frentes; se permiten IDs explícitos para acotar el lote.

La política distribuida mantiene **cero tareas autorizadas para ejecutar**. F03/F04 tienen validadores offline disponibles para reutilizar evidencias; añadir un ID a una lista no acredita autorización. Cada ficha requiere una referencia authorization con path y sha256 a una decisión de Work. La decisión debe contener:

```json
{
  "authority": "Work", "decision": "Referencia literal a la decisión acreditada",
  "task": "F04", "scope": "local_prepare",
  "plan_sha256": "SHA256 de estado.json",
  "spec_sha256": "object_hash de la ficha, sin authorization ni repair_authorization",
  "production": false, "network": false,
  "budget": {"seconds": 600, "max_attempts": 1}
}
```

Los hashes vinculan los bytes de una decisión suministrada por la dirección; no autentican criptográficamente la identidad de Work. No se deben fabricar decisiones para habilitar tareas. La referencia se vuelve a comprobar antes y después del intento. El presupuesto temporal comprende Ejecutor, validadores y Revisor; nunca excede segundos_maximos del lanzador. No se presenta como límite duro de tokens o euros.

Las dependencias se resuelven sobre todo el DAG, incluida su ascendencia y las tareas externas al lote. Para preparación se exige ascendencia técnica satisfecha, salvo prepare_dependencies expresamente incluida en el alcance acreditado de la ficha. Aceptación exige prueba técnica o PASS previo y ascendencia formal completa. Integración necesita autorización separada, revisión del SHA final y CI del mismo SHA; producción necesita otra autorización y readiness. Ambas puertas permanecen cerradas en el piloto. Las fases approval y respaldos manuales no invocan Ejecutor. No se modifica el Plan ni el historial manual.

Cada incremento completo se captura con HEAD, diff, índice Git, permisos, bytes (también ignorados), entradas y evidencia. Una captura superior a 256 MiB bloquea antes de Ejecutor y requiere preparación acotada. Un worktree sucio solo admite ejecución con checkpoint propio exacto. Cambios de HEAD, índice, rutas fuera del alcance o modificaciones durante validación/revisión bloquean y conservan entrega parcial. No hay reset ni limpieza.

Codex Ejecutor se invoca en el worktree verificado, workspace-write/never y sin red. El Revisor usa otra sesión efímera read-only/never sobre copia sellada. Se exige JSON estructurado, evidencias existentes, HEAD y hash del manifiesto exactos, sesión distinta y todos los criterios; NO_GO no habilita dependientes. La revisión es técnica local y no equivale a aprobación externa. Los permisos y hashes detectan alteraciones; no constituyen almacenamiento WORM.

Estados e intentos viven en DDD_LAUNCHER_HOME/auto/IDENTIDAD_PLAN. Cada evento contiene el estado y se publica mediante reemplazo atómico y fsync; el diario es la fuente del checkpoint, sin un segundo estado que pueda divergir. Se preservan los bytes de eventos anteriores. STARTED se publica antes de invocar procesos. Un diario corrupto falla cerrado. Cada reanudación produce un resumen consolidado nuevo para Work; conserva PASS, NO_GO, fallos y ejecuciones interrumpidas sin repetir intentos. La configuración y revisión del Plan deben coincidir:

```sh
ddd auto --plan RUTA --front all --pilot --run --resume CAMPAÑA
```

Se usan locks exclusivos por ruta canónica de worktree, interoperables con manual/auto, y locks heredados manual/batch. Dos slots globales limitan las sesiones Codex; un lock global limita GIS intensivo a una tarea. Auto ejecuta secuencialmente; manual y auto pueden ocupar como máximo dos slots. Los hijos heredan locks, incluso ante SIGKILL del controlador. SIGTERM termina el grupo de procesos. Un bloqueo de un frente permite continuar otro frente libre. El batch existente invoca ddd run y hereda los nuevos controles del lanzador manual tras instalar esta entrega.

Las reparaciones no se reintentan automáticamente. `--repair ID` exige otra referencia repair_authorization, scope local_repair, causa, prior_attempt_sha256 del result.json anterior y presupuesto de uno o dos intentos. Solo repara fallos locales consumidos con dependencias satisfechas; nunca producción o decisiones reservadas. Cada reparación exige una nueva orden y credencial del último intento.

Instalador solicitado, sin instalar todavía:

```sh
bash scripts/instalar-ddd-auto.sh --dry-run
# Solo tras orden posterior de instalación:
bash scripts/instalar-ddd-auto.sh --apply
```

Comprueba predecesor exacto y hace copia de seguridad con fecha. Conserva catálogo, parámetros personalizados, encargos, historial, logs y evidencias; no ejecuta piloto ni cambia ~/.local/bin/ddd. Las copias incluidas del catálogo y parámetros son las referencias existentes para pruebas; no se instalan.

Pruebas: `python3 -m unittest tests.test_ddd_auto -v`. Los worktrees se crean en /private/tmp. Codex simulado; validadores F03/F04 reales offline, dependientes de Python GIS y expedientes locales existentes. Se distinguen de un piloto real, que no se ha ejecutado. Evidencias históricas 1.1.0 y su dictamen siguen conservados; no aprueban 1.2.0.

Política de versiones: predecesores conservados, mejora MINOR compatible, metadatos y registro en este expediente. CI no ejecutada por prohibición expresa de workflows. No afecta comportamiento territorial. Prohibiciones mantenidas: push, PR, merge, workflows, generación, descargas oficiales y publicación. La consulta remota de main no se pudo completar por DNS; se registra la referencia local sin atribuirle actualidad remota. El patch histórico ddd-1.1.0.patch se conserva sin modificar; tiene tres líneas con whitespace histórico que no se normalizan. La comprobación de whitespace de código actual excluye ese artefacto histórico y se distingue del chequeo global.

Cierre de esta sesión: 28 pruebas PASS y Revisor separado GO sobre bytes finales. Git add y git commit rechazados con Operation not permitted en index.lock compartido; HEAD sigue en la base y no hay commit de entrega. Diff exacto exportado en /private/tmp/ddd-auto-1.2.0-review.patch. Cambios staged/unstaged y evidencias nuevas se conservan.


La semilla F02 local se acepta solo si su SHA-256 coincide con el pin revisado incluido en el controlador, su estado/origen son los esperados y sus receipts/bytes verifican. El campo `synthetic_test_fixture_only` se rechaza. Los tests de orquestación usan F02 formal PASS en un Plan temporal aislado; no fabrican receipts para acreditar una semilla técnica. La decisión Work sigue ligada por hash pero no autenticada criptográficamente; no ejecutar tareas reales hasta que la institución defina y habilite un anclaje de confianza independiente.
