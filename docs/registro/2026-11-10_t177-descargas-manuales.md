## 2026-11-10 — T-177 — Lista de descargas manuales para el propietario

**Causa.** La nube solo alcanza `boe.es` e `ine.es`; el propietario bajará a mano las demás fuentes.

**Cambio.** `docs/DESCARGAS_MANUALES.md`: ficheros por prioridad (naturalidad; municipales, europeas y Ecuador), con URL solo si consta en las notas T-173/T-158 («URL a confirmar» si no), destino en release, sha256 con `shasum -a 256` y alternativa de permitir `centrodedescargas.cnig.es` y `www.mapa.gob.es`.

**Pruebas.** Solo documentación; sin tests. Ninguna URL comprobada (hosts bloqueados).

**Riesgos.** Los nombres de release `fuente-*` son una propuesta que sigue el patrón del espejo de Infoelectoral.
