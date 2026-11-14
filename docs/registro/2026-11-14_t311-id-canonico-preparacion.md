## 2026-11-14 — T-311 — La preparación escribe el id canónico aunque reutilice un P10 viejo; revert de r3 tanda 1

- Causa: en r3 (aut01-aut10, runs 43633634369…43633725411) la P10 reutilizó paquetes anteriores a T-307 (mismo
  `package_sha256`, artefacto nuevo). `adquirir_fuentes_oficiales` 1.4.3 (#776) no actúa al reutilizar, y
  `materializar_contrato_generacion` copiaba el `resolved_source_contract` del paquete tal cual a `autNN_2025.yaml`
  → `territory.territory_id` legacy en los 10 yamls (`SinIdsViejos` con 10).
- Cambio: `materializar_contrato_generacion` (g) normaliza `territory.territory_id` con `resolver_id`, recalcula
  `contract_sha256` y guarda el del paquete en `package_contract_sha256`; un id fuera de la tabla se conserva.
  Legacy: `legacy/herramientas/materializar_contrato_generacion_pre_id_canonico_20261114.py`.
- Revert (`git revert --no-commit` commit a commit): los 20 commits de github-actions de d8ee954 a c4e4206 y los 8
  «catálogo de procedencia regenerado» de ddd-registro[bot] intercalados. No se revierten #779 #780 #769 #781 #782 ni
  los «numerar registro». Los ficheros revertidos quedan idénticos a d515ca1. Operador: r3 parada antes del revert.
- T-312: `test_aragon_source_receipt…` comprueba el linaje (mismo run, o receipt durable del paquete fuente del M06
  con el mismo `package_sha256` y `compatibility_identity_sha256`), no el run fijo. Rojo con el test viejo sobre
  `origin/main` (43633644499 != 40691712762), verde con el nuevo en `origin/main` y en esta rama.
  Legacy: `legacy/tests/test_preparacion_legislatura_vigente_pre_t312_20261114.py`.
- CLM (aut08) `DURABLE_LINEAGE_INCOMPATIBLE`: no es el id. La campaña registró una preparación nueva (artefacto
  `…-aut08-2025-43633706440`) del mismo paquete mientras el M06 vigente declara en su manifiesto (fase «01 ·») el
  artefacto anterior (`…-castilla_la_mancha-2025-40690624792`); `resolver_activos_durables` exige artefacto y SHA
  idénticos. Desaparece con el revert. Defecto aparte, no arreglado: una re-preparación sin M06 nuevo deja el
  producto territorial «disponible» con un linaje que el resolvedor durable rechaza (se reproducirá al rehacer las P10
  sobre territorios con M06; queda para el Planificador).
- Ensayo local P10 de Extremadura (aut11) sobre esta rama: declaración pedida con el id legacy → `id: aut11`;
  adquisición `official_live` del INE (20 min, paquete e9c9e323…, inventario y manifiesto con aut11); registro con
  `promover_catalogo_tras_preparacion` sin `--persist`: yaml, receipt, `catalogo_preparacion.yaml` y maestro con aut11
  (solo `id_legacy:` del maestro nombra el viejo); evaluación pre-generación (`build_generation_evaluation`) con aut11.
  Caso r3 simulado (mismo paquete con el contrato resuelto en legacy y su SHA recalculado): yaml con aut11 y
  `SinIdsViejos` verde; con el materializador anterior, el mismo ensayo deja el legacy y `SinIdsViejos` falla.
  No se ejecutó la persistencia (push) ni la regeneración del catálogo de procedencia.
- Pruebas: `tests/test_t311_contrato_resuelto_id_canonico.py` (rojo con la versión anterior), t220, t307, r015,
  procedencia, guardián, fuentes oficiales, materialización y preparación de legislatura: 156 verdes.
- Efectos: sin cambio de huellas M04/M05. Los 10 P10 de la tanda 1 se rehacen (decisión del Planificador).
