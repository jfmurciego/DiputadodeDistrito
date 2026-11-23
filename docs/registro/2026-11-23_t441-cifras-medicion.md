## 2026-11-23 — T-441 — Cifras reales de la medición de la web en el diseño de carga ligera (§1.3)

- **Causa:** §1.3 de `docs/ESTUDIOS/T441_CARGA_LIGERA/DISENO.md` esperaba un run válido de `medir-web`; el primero útil es el 45145365825 (23-11, `main`@964f7f3: todo 200 tras resolver el propietario el bloqueo de Cloudflare, D-199).
- **Cambio:** DISENO.md 1.2.0: tabla §1.3 con primer byte y total (mediana con compresión) y bytes con / sin compresión de las nueve filas del run, y lo que confirman (Pages comprime JSON y GeoJSON; lo más pesado medido, distritos de Madrid, 891 KB comprimido / 2,7 MB). Solo datos del log; sin propuestas nuevas.
- **Pruebas:** cifras copiadas del log del job de medición del run 45145365825; guardián en local.
- **Riesgos:** ninguno (documento).
