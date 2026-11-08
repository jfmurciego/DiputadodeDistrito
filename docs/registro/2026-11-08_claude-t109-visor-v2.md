## 2026-11-08 — T-109 — Visor v2 (vista previa privada, D-24)

Causa: el propietario aprobó la maqueta del visor v2 (`docs/ARQUITECTURA/visor_v2/`). Cambio: `visor/v2/` (portada «Mapa» con vistas
Congreso y Parlamentos autonómicos, pestañas Nacional, Autonómico, Elecciones y Método, textos de `web/textos.md`, vacíos) y `web/textos.md`.
No enlazado ni publicado; la v1 no se toca. La geometría de la maqueta tenía 156 polígonos vacíos (MapLibre no pintaba ninguna provincia)
y Ávila desplazada; corregidos. Pruebas: datos de la maqueta contra el CSV oficial (52 provincias, 350 escaños, 407 distritos) y
navegador con MapLibre 5.7.0 en móvil (mapa, selección de provincia y de comunidad). Riesgo: ninguno en producción; no invalida huellas ni checkpoints.
