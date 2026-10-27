DDD auto 1.3.0 — 2026-10-11. Infraestructura local candidata; NO_READY para campaña.
Anterior: legacy/1.2.0/AUTO.md. Motivo: orden única de Dirección; catálogo expandible, ventanas acotadas y supervisión segura. No altera contratos productivos ni autoriza trabajos.

El ddd existente carga un catálogo versionado y sus fichas largas por SHA. Mantiene list/show/history, IDs originales y aliases sin colisiones. Las 26 candidatas se concilian con iniciativas existentes; sus enlaces no convierten revisiones parciales en cierres. migrar_plan.py opera exclusivamente sobre una copia: conserva el prefijo exacto del diario, los PASS y genera índice de ocho entidades y relaciones con evidencia. Una segunda ejecución es idempotente. La transacción instalada exige quietud, revisión y puertas del instalador.

Comprobaciones sin escritura ni consumo Codex:

```sh
python3 infraestructura/ordenes-manuales/ddd.py auto --plan RUTA --catalog CATÁLOGO --front all --night --dry-run
python3 infraestructura/ordenes-manuales/ddd.py auto --plan RUTA --catalog CATÁLOGO --status
```

Se admiten IDs concretos y aliases. El dry-run informa ENABLED, WAIT_OWNER, BLOCKED y ALREADY_EVIDENCED por frente y tarea. Cero ENABLED devuelve NO_READY y código 1. --status devuelve el estado y bandeja acumulada sin escribir. No se incluye un comando de campaña aprobado: falta piloto real. --run requiere --pilot o --night; --resume ID se combina con ese modo y --run. Una reanudación no repite intentos ya consumidos.

--night exige schema ddd.owner-window/1.0 con authority Owner, status APPROVED, aprobación original path/SHA, ventana máxima 12h, fingerprints exactos plan/catálogo/alcance y presupuesto por tarea y campaña. El manifiesto DRAFT nunca concede autoridad. PILOT comprende exactamente dos READ_ONLY de frentes A y N; NIGHT requiere receipt verificable de ese piloto REAL_CODEX, validadores y sesiones separadas con evidencia intacta. No se deduce autorización de este documento, del inventario ni de la orden de diseño. La compatibilidad --pilot con decisiones históricas Work no habilita --night.

La política instalada se conserva y no se amplía automáticamente. Cada tarea requiere contrato local suficiente: rutas explícitas, entradas por SHA y validadores offline que cubran todos los criterios. READ_ONLY usa copia acotada de entradas (máximo 16MiB), sin escritura en los tres frentes; LOCAL_IMPLEMENTATION requiere permiso de clase y rutas expresas. El prompt incorpora la ficha larga exacta, objetivos, normas, fingerprints, validadores, tiempo y salida estructurada. No ejecuta motores históricos, adquisiciones ni GIS por una autorización de contraste probatorio.

Preparación y aceptación resuelven dependencias separadas; ALREADY_EVIDENCED histórico evita repetición sin satisfacer TECH_PASS ni producción. TECH_PASS requiere pruebas y revisión de bytes finales. Integración y producción permanecen cerradas. La identidad/edición/SHA de artefactos se verifica antes de preparar. Un SHA de receipt o entrega alterado bloquea nuevamente la tarea y sus consumidores sin retry automático.

Un escritor por worktree, locks manual/batch heredados, dos slots Codex globales y un GIS intenso como máximo. La cola secuencial vuelve a evaluar después de cada entrega, continúa tareas independientes tras NO_GO y aparca worktrees ocupados o sucios sin checkpoint propio. No usa reset/clean ni cambia HEAD. El Revisor trabaja en sesión distinta read-only/never sobre copia sellada; comprueba manifest, HEAD, criterios y evidencia. Una sesión separada no equivale a acreditación externa. Los hashes detectan alteraciones; no autentican por sí solos identidad humana.

Terminales técnicos: TECH_PASS y REVIEW_NO_GO. Estacionarios: WAIT_OWNER, BLOCKED, INTERRUPTED, QUOTA_STOP. Un STARTED huérfano conserva su evidencia y no repite Ejecutor. El diario falla cerrado ante truncado/corrupción; los locks heredados protegen procesos tras SIGKILL. Cuota detiene nuevas tareas y solo una reanudación explícita abre continuación de otras tareas, sin repetir la agotada. Reparación requiere una orden local concreta, causa e intento por SHA; máximo dos ciclos por causa con revisión posterior. La ventana nocturna no concede reparación implícita.

Cada ejecución o reanudación produce summary-UUID.json y BANDEJA_MATINAL-UUID.md nuevos, con entregas, pruebas, decisiones y bloqueos acumulados. --dry-run no crea diario, locks, carpetas ni resúmenes. El límite de segundos cubre Ejecutor, validadores y Revisor; tokens reportados son una guardia suave, sin inventar coste en euros.

El instalador público --apply exige --gate-file: revisión separada sobre todos los bytes del bundle, piloto real de dos READ_ONLY independientes, autorización acotada y targets exactos. Compara predecessor, locks y bytes protegidos, crea backup externo con hashes/permisos y verifica rollback. --rollback requiere backup y fingerprints actuales sin cambios ajenos; un rollback del plan conserva el diario por eventos compensatorios. Parámetros, encargos, política, historial, logs y legacy se protegen. Un controlador concurrente o bytes distintos abortan; no hay bypass de producción en la CLI. Los mocks viven exclusivamente en unit tests con destinos desechables.

Pruebas: python3 -m unittest tests.test_ddd_auto tests.test_ddd_night tests.test_ddd_plan_migration tests.test_ddd_installer -v. Codex simulado en fixtures; validadores offline reales del controlador y de F03/F04 históricos. No equivale a piloto REAL_CODEX. CI/workflows no ejecutados por prohibición expresa. Expediente completo en DDD-control/entregas/plan-vivo-supervisor-20261011; inventario remoto UNVERIFIED_OFFLINE.
