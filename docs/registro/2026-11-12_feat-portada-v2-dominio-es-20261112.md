## 2026-11-12 — T-116 — Preparar la V2 como portada conservando el visor técnico

- **Causa:** el propietario decide publicar el visor V2 ya existente como portada de diputadodedistrito.es, sin sustituir ni rediseñar el código V2.
- **Cambio:** la construcción del sitio candidato conserva la V1 original en `/v1/` con `<base href="../">` y sirve la raíz mediante una redirección a `/v2/`. Mantiene los activos en sus rutas originales y la inyección opt-in del visor analítico Congreso. No modifica el registro de productos, ni genera resultados adicionales, ni cambia `visor/index.html` o `visor/v2/`.
- **Gobernanza:** publicador 3.14.1 con anterior exacto archivado en `legacy/workflows/_reutilizable-publicar-sitio_v3.14.0_20261112.yml`; nuevo materializador 1.0.0 con cabecera completa. Se conserva sin cambios el contrato P50 (un solo `--site /tmp/site-candidate` del materializador original).
- **Pruebas:** `tests/test_preparar_portada_v2.py` verifica conservación de la V1 original, redirección, rutas relativas en dominio y Pages, opt-in Congreso y fallos cerrados; suite CI y revisor en PR #738.
- **PR:** https://github.com/jfmurciego/DiputadodeDistrito/pull/738 — no ejecutar P50 ni desplegar DNS como parte de esta PR.
