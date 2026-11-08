## 2026-11-08 — T-105 — Gestor de Campañas 2.0 con el formulario de D-22

- Causa: D-22, el propietario lanza a mano, sin chats, todo el Congreso o cualquier parte con parámetros claros.
- Cambio: `gestor-campanas.yml` 1.5.0 con las entradas en el orden de D-22 (elección, tipo, territorios, inicio,
  publicar, ensemble) más mapa (407/350) y «solo plan» activado por defecto; `herramientas/gestor_campanas_2.py`
  1.0.0 (resolución de partes por nombre, código o matrícula; lo no disponible falla al planificar con `::error::`
  y sin lanzar); `legislatura_vigente.py` 1.2.0 (inicio «aprovechar fuentes», publicar por fila, 06 `ensemble_10`
  tras la publicación, relevo con «@auto»). Guía en `docs/GUIA_GESTOR_CAMPANAS.md`. «matriz» se conserva en «modo».
- Pruebas: `tests.test_gestor_campanas_2` (nuevo) y `tests.test_legislatura_vigente` 1.2.0; plan en seco de todo el
  Congreso (52), Aragón (3), una lista mixta y el mapa 350 (49).
- Riesgos: la 05 y la 06 del Gestor se identifican por orden (una a la vez); sin efecto en motor ni huellas.
  Apilada sobre la #539 (T-102). Prueba real con una provincia: el Operador, con permiso del propietario.
