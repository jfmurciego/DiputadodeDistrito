## 2026-11-11 — T-246 — La 00 comprueba al planificar que el paquete electoral sigue descargable

- Causa: cuando la 00 consume un par preparado (sin ejecutar 03, p. ej. «Reutilizar»), el paquete electoral
  del par solo se buscaba en la puerta 03 → 04, después de M04-M06. El paquete fuente se retiene 30 días: si
  había caducado, la cadena caía a mitad tras gastar la generación.
- Cambio: herramienta nueva `herramientas/comprobar_paquete_electoral_remoto.py` 1.0.0 y paso
  «Comprobar que el paquete electoral sigue descargable» en el job «Planificar» de
  `ejecucion-completa-proyecto.yml` 1.9.0 (copia en `legacy/workflows/ejecucion-completa-proyecto_v1.8.0_20261111.yml`).
  Por metadatos REST y con las mismas rutas que la puerta 03 (artefacto vivo del run, mismo nombre y digest en
  otro run, copia durable en release), bloquea con salida 76 y código `ELECTORAL_PACKAGE_{MISSING,EXPIRED,
  DIGEST_MISMATCH,IDENTITY_MISMATCH,EXPIRES_SOON,IDENTITY_INCOMPLETE}`; `EXPIRES_SOON` si caduca en menos de
  12 h. El mensaje dice qué falta y el remedio: 03 con `reutilizar_si_ya_preparada=false`, `prepare_one` de la
  legislatura vigente y relanzar la 00. Un fallo de la API es técnico (salida 1), no pide regenerar. Sin
  entradas nuevas en la 00; en `pull_request` no se ejecuta.
- Pruebas: `tests/test_comprobar_paquete_electoral_remoto.py` (fixtures, sin red: vivo, caducado, ausente,
  digest y artifact_id distintos, caducidad inminente, otro run, release durable, no aplicable, CLI);
  suites de la 00, par preparado, Gestor, seguridad de workflows y diseño A en verde.
- Riesgos: ninguno sobre checkpoints ni huellas. Una 00 que antes llegaba a la puerta 03 con el paquete
  caducado ahora para en «Planificar».
