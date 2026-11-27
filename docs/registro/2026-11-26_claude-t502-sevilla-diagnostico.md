## 2026-11-26 — T-502 — Diagnóstico de Deslinde en Sevilla

- **Causa:** el piloto del banco (#1025) demostró en Sevilla (nac41, K = 16) un plan válido con 6 demarcaciones
  partidas, y el ganador de Deslinde parte 8.
- **Diagnóstico:** el candidato exacto solo se aplica con K ≤ 4 (`exacto.K_MAX`), y el exhaustivo no se intenta
  (200.160 nodos, por encima del presupuesto de 200.000); las cadenas no bajan de 8. Con `K_MAX = 16` en memoria gana el
  exacto, con 6 y el óptimo demostrado, a cambio de 85 s más. Segundo hallazgo: con la etapa de frontera sin cerrar, la
  cota de CP-SAT cambia entre ejecuciones y haría irreproducible `huella_resultado`.
- **Cambio:** informe con la propuesta, sin implementar: aplicabilidad por tamaño (átomos × K ≤ 2.000) y sin cota de
  etapas abiertas en la huella. Test de regresión `tests/test_t502_sevilla_exacto.py`, desactivado hasta el arreglo
  (`DDD_T502_ACTIVO=1` y entradas de la batería). No toca el motor ni las huellas.
- **Pruebas:** en local, el test activado falla en `main` («8 != 6») y la competición con el parche en memoria da 6.
  Desactivado, se salta.
