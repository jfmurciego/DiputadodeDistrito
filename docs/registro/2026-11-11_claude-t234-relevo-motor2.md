## 2026-11-11 — T-234 — Relevo formal: Deslinde 1.0 (motor2) por defecto; ruta autónoma m05 retirada

- **Causa:** D-82 (todos los mapas se regeneran con el motor nuevo; ningún mapa del motor antiguo queda vigente) y D-84
  (el algoritmo se llama «Deslinde»; Deslinde 1.0 = canónico + 10 cadenas ReCom + elección D8 + vigente como candidato).
  Fusionar solo al terminar la regeneración (autonómicas y Congreso): PR con `no-automerge`.
- **Cambio:** `motor` por defecto = motor2 en la 00 «P00 Campaña» 1.9.0 (botón, workflow_call, 02 y 00 electoral
  encadenada), en la 02 8.3.0, en el reutilizable de generación territorial 1.5.0 (P30) y en el Gestor: 1.11.0 (modo
  matriz con motor expreso: Canónico → motor2, GerryChain → m05) y `herramientas/legislatura_vigente.py` 1.3.0 (la 00 del
  Gestor 2.0 se lanza con `motor=motor2`). En «Planificar» de la 00: `motor=m05` explícito sigue funcionando con
  `::warning::` (ruta retirada); motor2 con un algoritmo GerryChain o un motor desconocido fallan cerrado (exit 20).
  `docs/MODULOS/` (README, M04, M05 1.4.7): «Deslinde 1.0» como descripción y la ruta autónoma M04+M05 marcada como
  retirada. Nada se renombra; M04/M05/ddd_core, huellas N08/M05 y tests R015/R016 sin tocar (el código del canónico no
  se mueve a `legacy/`: sigue corriendo como candidato y está en las huellas).
- **Efectos:** tras fusionar, una 00 «Reutilizar» sin `motor` rechaza los checkpoints M06 hechos con m05
  (CHECKPOINT_ENGINE_MISMATCH): es lo esperado (D-82). El botón directo de la 02 no tiene entrada `motor`: con un
  algoritmo GerryChain falla cerrado; la ruta m05 se pide por la 00 con `motor=m05`.
- **Pruebas:** `tests/test_relevo_motor2.py` (nuevo: interruptor de la 00 ejecutado con bash, m05 explícito avisa,
  defaults de 02/cadena/Gestor) y `tests/test_p30_motor2_produccion.py` actualizado. Sin ejecuciones productivas.
