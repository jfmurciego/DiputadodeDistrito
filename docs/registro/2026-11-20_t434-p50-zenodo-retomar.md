## 2026-11-20 — T-434 — P50 1.2.0: sin el código de Deslinde en el lote, «Retomar el depósito en Zenodo» y prueba sin Release

- Causa: la P50 de prueba (run 44748912809, main@622bc97f) falló en el job `zenodo` con ZENODO_SIN_LINAJE por
  `ddd-deslinde-v1.0.0.tar.gz`. La 1.1.0 trabajaba en `paquetes/` y empaquetaba con `for d in paquetes/*/`, que recoge
  el directorio versionado `paquetes/deslinde` (código del motor: `pyproject.toml`, `src/deslinde/*.py`). Ese tarball de
  código quedó en la Release `mapas-v1.0.0` (pública aunque el destino era el sandbox: «Crear Release» no miraba `destino`).
- Cambio: (1) directorio de trabajo en `$RUNNER_TEMP/p50` y bucles sobre los territorios del plan; comprobación de un
  paquete por territorio. El depósito toma solo los paquetes de los territorios de `MAPAS.json` con
  `zenodo_deposito.py preparar` (1.2.0): sha256 contra el SHA256SUMS de la Release, SHA256SUMS filtrado y LINAJE
  cruzado con el M06 de MAPAS. Se excluye el tarball de Deslinde (no se le añade LINAJE): D-146 deposita solo mapas,
  sin motor. (2) Botón `accion`: «Retomar el depósito en Zenodo de la última versión» (`p50_resolver.py retomar` 1.1.0)
  salta `publicar` y deposita la última Release ya creada con su versión, sin gastar otra. (3) Con destino `prueba`
  no se crea Release: el lote va como artefacto del run (`p50-lote-prueba`, 7 días) al job `zenodo`.
- Pruebas: `tests/test_t434_p50_retomar.py` (ejecuta los pasos de shell: la 1.1.0 congelada reproduce el
  ddd-deslinde y la 1.2.0 no, con el mismo contenido por territorio; condiciones `if` evaluadas; `gh` simulado para
  «Resolver» y «Reunir»; equivalencia del resto contra la copia congelada de la 1.1.0). `preparar` sobre la Release real
  mapas-v1.0.0 (74 assets): 71 paquetes verificados, Deslinde excluido.
- Riesgos: la Release `mapas-v1.0.0` sigue con el tarball de código (no se toca; el depósito lo excluye). En una prueba
  de versión nueva, el enlace a la Release en la descripción del sandbox no existe.
- Incidente (anotado por decisión del propietario, 20-11): el 2026-11-20 a las 13:59 UTC la P50 de prueba subió a la
  Release pública `mapas-v1.0.0` el asset `ddd-deslinde-v1.0.0.tar.gz` (id 772033851, 62 812 B): el código del motor
  (`pyproject.toml`, `requirements-deslinde.lock`, `src/deslinde/*.py`), no un mapa. Causa: el glob `paquetes/*/` del
  empaquetado recogía el directorio versionado `paquetes/deslinde`. Llevaba 3 descargas cuando se detectó; a las 15:2x UTC el
  contador marca 4, y al menos 2 son de la sesión de T-434 (comprobación del contenido y prueba de `preparar`). No se
  ha borrado nada: el borrado del asset lo hace el Operador con la frase del propietario. Test nuevo: ningún paquete de
  P50 lleva código (lista blanca: LINAJE, SHA256SUMS, CITATION.cff, M06 y contexto yaml/json).
