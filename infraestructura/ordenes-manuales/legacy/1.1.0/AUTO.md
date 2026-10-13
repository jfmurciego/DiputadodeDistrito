DDD auto — versión 1.1.0, 2026-10-10. Alcance: infraestructura local de los tres frentes; candidato READY_FOR_REVIEW. Origen: lanzador manual del catálogo `ddd.manual-launcher/1.0`; predecesor conservado en `legacy/1.0.0/ddd.py`. Motivo: ejecutar una campaña local con controles y revisión por entrega. Sin cambios de gobierno, motor territorial, K, fuentes productivas o publicación.

La actualización añade `auto` al mismo `ddd.py`. Conserva las 32 fichas y los tres worktrees; lee los parámetros existentes, el Plan Maestro y el historial manual. El catálogo, los parámetros y los encargos incluidos aquí son copias exactas de referencia para las pruebas; el instalador no los sustituye. Los prompts de continuación existentes tampoco se sustituyen. No usa `ddd_batch.py` para aceptar tareas. La instalación existente y `~/.local/bin/ddd` siguen siendo el punto de entrada.

Este expediente está en `DDD-orquestador-auto` porque la sesión no permite escribir en `DDD-control`. La actualización todavía no está instalada. El instalador comprueba el hash exacto del predecesor, conserva su código y evita reemplazar módulos que ya existan:

```sh
python3 infraestructura/ordenes-manuales/instalar_actualizacion.py
# Aplicación local posterior; no ejecuta tareas ni consume Codex:
python3 infraestructura/ordenes-manuales/instalar_actualizacion.py --apply
```

Después de instalar, el operador puede inspeccionar sin consumir Codex:

```sh
ddd auto F03 F04 --dry-run
ddd auto --dry-run
```

Desde esta entrega, sin instalar ni escribir en el controlador existente:

```sh
DDD_LAUNCHER_HOME="$HOME/Desarrollo/DDD-control/ordenes-manuales" \
  python3 infraestructura/ordenes-manuales/ddd.py auto F03 F04 --dry-run
```

El piloto real requiere aprobación previa de esta entrega. Tras esa aprobación, la orden es `ddd auto F03 F04`. Con las evidencias actuales, F03/F04 se validan y revisan sin repetir el Ejecutor: F03 ya tiene dos handoffs históricos, y F04 tiene un intento manual terminado. Para un encargo nuevo autorizado por Work, la ficha de política se configura con `validate_existing: false`; cualquier intento manual previo continúa impidiendo repetición del Ejecutor. Los intentos manuales fallidos pasan a WAIT_OWNER. No hay flag de retry automático ni se interpreta DONE_REVIEW como aceptación.

Los estados significan:

| Estado | Efecto |
|---|---|
| TECH_PASS | Validadores deterministas y revisor PASS sobre la misma entrega; habilita dependencias técnicas locales. |
| FORMAL_PASS | PASS ya registrado por autoridad en el Plan; nunca lo escribe auto. |
| BLOCKED | Dependencia ausente, criterios insuficientes, fallo, dictamen inválido o interrupción. |
| REVIEW_NO_GO | Pruebas técnicas superadas y dictamen válido NO_GO; no habilita dependientes. |
| WAIT_OWNER | Respaldo, aprobación, decisión o intento manual fallido reservado. |

El grafo completo se comprueba para ciclos y referencias desconocidas, incluidas dependencias externas al lote. Solo TECH_PASS/FORMAL_PASS satisfacen dependencias técnicas directas. Se registra también la ascendencia formal pendiente. F02 se reutiliza como TECH_PASS tras comprobar el hash del expediente, 14 identidades, controles F02, bytes de los artefactos y hashes de los receipts. Es una acreditación técnica preexistente, no una nueva ejecución de F02. F01 queda como reserva formal de esta campaña por la orden del Director. El Plan vigente registra F01/F02/F03 PASS y F04 PENDING: esos hechos se conservan íntegros; la reserva no cambia retrospectivamente ninguno de ellos.

La política inicial autoriza solo F03/F04. Las otras 30 tareas siguen disponibles en el catálogo, pero requieren encargo local y validadores aprobados que cubran todos sus criterios. Marcar `covers` no crea una prueba: Work debe revisar la suficiencia del programa determinista y su alcance sin red antes de habilitar una ficha. Sin ficha suficiente, auto falla cerrado. Las tareas `approval`, F01 y N01 siguen reservadas aunque se incluyan en la política.

F03 ejecuta `verify_handoff` y el consumidor real congelado dentro del ZIP histórico, verifica SHA256SUMS y reproduce 12 negativos por territorio. No ejecuta scripts del expediente ni etapas territoriales. F04 ejecuta `validate_prepared_package` y `validate_compatibility_package` existentes sobre cinco candidatos, coteja las identidades y receipts con la matriz de 19 y exige los cinco gaps originales. Los validadores bloquean sockets y conservan el informe. El Ejecutor recibe sandbox workspace-write, never, timeout configurado y red deshabilitada. El Revisor inicia otra sesión efímera con read-only y never. Los logs JSONL conservan uso reportado; `presupuesto_tokens_reportados_suave` se conserva como parámetro/telemetría, no es un presupuesto duro. No se impone un límite económico adicional.

Cada campaña escribe únicamente en `DDD_LAUNCHER_HOME/auto/`: identidad única, configuración congelada, resúmenes nuevos y `eventos.jsonl` append-only. El intento STARTED se guarda con fsync antes de Codex. Cada entrega conserva baseline, SHAs, diff binario, hashes y bytes de archivos versionados y no ignorados, entradas externas fijadas por SHA, programas de control, pruebas y dictamen. Se preservan los cambios previos; un Ejecutor nuevo solo arranca con worktree limpio o un checkpoint propio exacto. Los fallos conservan las salidas parciales y un manifiesto de hashes; no se hace reset, clean ni rollback de cambios del Ejecutor.

El Revisor trabaja en una copia sellada con permisos de lectura y un manifiesto por contenido, sin `.git` que apunte al worktree original. El controlador valida el JSON contra el subconjunto cerrado del esquema suministrado (los keywords no soportados fallan), la identidad de entrega y HEAD, las referencias de evidencia y todos los criterios de PASS. Comprueba los hashes después de revisar. Los permisos locales y hashes ofrecen una entrega congelada y comprobación de alteraciones; no son almacenamiento WORM. Una sesión separada no equivale a aprobación externa ni formal. El dictamen del piloto simulado tampoco constituye revisión real de F03/F04.

Un lock por ruta canónica del worktree coordina manual/auto, además de los locks heredados manual y batch. Los hijos heredan esos descriptores: si muere el controlador, el worktree continúa bloqueado mientras el hijo viva. SIGTERM/Ctrl-C detienen el grupo de proceso. Ante SIGKILL queda STARTED; al recuperar se añade BLOCKED, sin borrar ese intento. Un hijo huérfano que siga vivo requiere intervención humana; no se lanza otro proceso encima.

Para recuperar resultados se leen los `summary-*.json` y `result.json`. Para reanudar las tareas aún no intentadas, use la identidad que imprime CAMPAÑA, el mismo lote, catálogo, parámetros y política:

```sh
ddd auto F03 F04 --resume IDENTIDAD
```

Reanudar conserva PASS, NO_GO y fallos; no repite el Ejecutor ni el Revisor de un intento gastado. Un diario truncado bloquea todo consumo de Codex. Un resumen puede mostrar dependencias bloqueadas que se habiliten en una invocación posterior; no equivale a un intento consumido. La herramienta no modifica estados formales ni ofrece cierres humanos automáticos.

Simulación reproducible en este Mac, con Codex simulado y validadores reales existentes:

```sh
python3 -m unittest tests.test_ddd_auto -v
```

Usa worktrees de prueba en `/private/tmp/ddd-auto-sim-*`, los 32 IDs y parámetros clonados. Los escenarios leen la evidencia histórica real; F04 apunta al frente Fuentes solo en lectura para evitar copiarlo en cada caso. Esa desviación existe solo en la política de simulación. El modo operativo usa la copia capturada de la entrega. Se pueden conservar todos los expedientes en una carpeta creada previamente indicando `DDD_AUTO_SIM_OUTPUT`. Sin los artefactos reales o el Python GIS existente, la simulación falla; no inventa resultados de los validadores.

Política de versiones: predecesor conservado, incremento compatible, metadatos y registro en este expediente. Las pruebas locales no se presentan como CI. CI no ejecutada: workflows expresamente prohibidos por la orden. No afecta comportamiento territorial y no corresponde ejecutar un run de territorio. Commit local no creado en esta sesión: el directorio Git común está fuera de las raíces de escritura. No push, PR, merge, workflow, generación territorial, adquisición en red o publicación. El único siguiente paso de autoridad es revisar la entrega antes de autorizar el piloto real.
