# T-478 · Notas de traspaso (trabajo en curso)

Hecho: `tests/test_t478_indicadores.py` (casos a mano; falta `herramientas/indicadores_sistemas.py`, que el test importa:
`gallagher`, `loosemore_hanby`, `numero_efectivo`, `prima_ganador`, `votos_sin_representacion`, `ganador_mayoria_simple`,
`escanos_reales(eleccion)` → {código INE provincia: {partido homologado: escaños}}, `sumar`).

Fuentes comprobadas (todas en git, con sha256):
- 2023 en los mapas PUBLICADOS: `datos_abiertos/INDEX.json` (52 territorios, 407 distritos) → `resultados.run_id` →
  `datos/resultados/MANIFEST.json` `partidos_runs` (filtrar variantes 350 con `territorio_ids.es_variante_350`) → `ruta`
  (votos por partido y distrito, con blancos/nulos/censo); sha256 = `sha256_csv` (verificado 52/52). Total 24.284.335 votos.
  Albacete trae desajuste 0,63 % > tope 0,5 % (`desajustes`): señalarlo.
- 2011-2019 (y 2023 de contraste): `datos/resultados/historico/<AAAAMM>/<id viejo>_partidos.csv`, claves de
  `datos/resultados/historico/MANIFEST.json` (52; `provincia` = código INE). OJO: reagregado sobre mapas M06 ANTERIORES
  (mismo K por provincia, 407): en 42 de 52 el reparto de votos por distrito difiere del publicado. Etiquetar «mapa del histórico».
- Escaños reales: `configuracion/resultados_oficiales_congreso_{2011_11,…,2023}.csv` (cuadro II: solo partidos con escaño;
  sha256 en el .json). Paso a homologado: `configuracion/alias_siglas_boe_espejo.csv` (eleccion, provincia, sigla_boe →
  siglas_espejo; si falta, la sigla tal cual) y luego `configuracion/alias_partidos_generales.csv`. Cobertura 100 %;
  2023 da PP 137, PSOE 121, VOX 33, Sumar 31 (= BOE).
- Votos del sistema real: suma por provincia de los distritos (espejo/ZIP, sin CERA); los escaños, del BOE (con CERA).
- Alias y bloques: `doble_vuelta.cargar_alias` (`202307`) y `cargar_tabla` de `configuracion/bloques_partidos_2026-11-25.csv`
  (`2023-07`); cubren el 100 % de los votos en las 6 elecciones. Doble vuelta: reutilizar `doble_vuelta.resolver`
  (dv_base, dv_A, dv_B) sin tocarlo; en dv_A/dv_B la unidad es la candidatura (bloque coaligado).
- Población: `configuracion/poblacion_oficial_provincias_2022-01-01.csv` y `_2025-01-01.csv` (líneas `#` de cabecera).
  Desigualdad = Loosemore-Hanby escaños (o distritos) por provincia frente a población (y frente a censo por elección).

Cifras de la auditoría a comprobar: PP 33 % (2023); «207 de 325 en 49 provincias» viene de `dashboard/hemiciclo.json`
(vetado): no reproducible desde git; con los mapas publicados la mayoría simple da otra cifra sobre 407 (homologando, PP≈235).
10,7 % → 1,9 %: auditoría §6.1 con «padrón 2023» (no está en git: usar 2022 y 2025 y decirlo).

Reglas del código en `herramientas/`: sin ids viejos literales ni prefijo `congreso_` (test_t220); las rutas salen de las
claves de los manifiestos. Salidas en `docs/ESTUDIOS/T478/` (CSV + INFORME + borrador «Qué cambiaría» + fuentes con sha256).
