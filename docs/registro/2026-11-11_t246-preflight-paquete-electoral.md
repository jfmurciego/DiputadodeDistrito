## 2026-11-11 — T-246 — La 00 comprueba al planificar que el paquete electoral sigue descargable

- Causa: cuando la 00 consume un par preparado (sin ejecutar 03, p. ej. «Reutilizar»), el paquete electoral
  del par solo se buscaba en la puerta 03 → 04, después de M04-M06. El paquete fuente se retiene 30 días: si
  había caducado, la cadena caía a mitad tras gastar la generación.
- Cambio: herramienta nueva `herramientas/comprobar_paquete_electoral_remoto.py` 1.0.0 y paso
  «Comprobar que el paquete electoral sigue descargable» en el job «Planificar» de
  `ejecucion-completa-proyecto.yml` 1.9.0 (copia en `legacy/workflows/ejecucion-completa-proyecto_v1.8.0_20261111.yml`).
  Por metadatos REST y con las mismas rutas que la puerta 03 (artefacto vivo del run, mismo nombre y digest en
  otro run, copia durable en release), bloquea (salida 76) solo con evidencia positiva:
  `ELECTORAL_PACKAGE_MISSING` (404/410 o ausente de un inventario completo), `ELECTORAL_PACKAGE_EXPIRED`
  (`expired` o `expires_at` pasado) o `ELECTORAL_PACKAGE_DIGEST_MISMATCH`, con el remedio: 03 con
  `reutilizar_si_ya_preparada=false`, `prepare_one` de la legislatura vigente y relanzar la 00. Lo no
  determinable (503 de cuota, red, 403, inventario incompleto, identidad del plan incompleta), un artifact_id
  distinto con el mismo digest y la caducidad en menos de 12 h solo avisan (`::warning::`, salida 0) y decide
  la puerta 03. La clasificación de errores es la de `herramientas/descargar_artefacto.py` (T-251). Sin
  entradas nuevas en la 00; en `pull_request` no se ejecuta.
- Pruebas: `tests/test_comprobar_paquete_electoral_remoto.py` (fixtures, sin red: vivo, caducado, ausente,
  digest y artifact_id distintos, caducidad inminente y pasada, otro run, release durable, API 503/403/red
  con runner simulado, inventario incompleto, no aplicable, condiciones del paso, CLI);
  suites de la 00, par preparado, Gestor, seguridad de workflows y diseño A en verde.
- Riesgos: ninguno sobre checkpoints ni huellas. Una 00 que antes llegaba a la puerta 03 con el paquete
  caducado ahora para en «Planificar».
