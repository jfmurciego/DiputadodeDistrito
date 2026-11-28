## 2026-11-27 — T-473 — Página de opciones de licencia del código

**Causa.** D-214 / plan de mejora 25-11 (bloque F): la licencia propietaria («el acceso al repositorio no concede ningún
derecho de uso») choca con «investigación verificable» y bloquea el kit de reproducción (T-472) y la revisión externa
(T-474). El propietario necesita las opciones y sus consecuencias para decidir.

**Cambio.** `docs/LICENCIA_OPCIONES.md` 1.0.0 (solo documentación): estado actual comprobado (`LICENSE`, `CITATION.cff`,
README, pie y portada de la web, Metodología, README de Deslinde, registro de la propiedad intelectual T-281/#995, DOI de
Zenodo), nueve contradicciones, tres opciones (A cerrada; B PolyForm Strict 1.0.0; C reglas y validador en Apache-2.0
con el motor cerrado) con qué permiten, qué no, qué recibe el propietario y qué pasa si no, y recomendación B sin
aplicarla. Marcas y las dos voces, fuera (precisión del Planificador). No cambia ninguna licencia.

**Pruebas.** Citas de las licencias contrastadas con sus textos oficiales (sha256 en el documento; webs de PolyForm,
Creative Commons y Zenodo no accesibles desde la nube). GovernanceHeaders, test_t220_renombrado y
`comprobar_guardian_main.py todo` en verde.

**Riesgos.** Ninguno en motor, huellas ni checkpoints. Sin run. Pendiente de comprobar en Zenodo la licencia y el
contenido de los dos depósitos.
