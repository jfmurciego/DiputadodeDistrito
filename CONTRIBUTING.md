# Cómo contribuir

Gracias por el interés. Este proyecto se rige por el [Código de conducta](CODE_OF_CONDUCT.md) y desde el 14-11-2026 tiene una
[licencia propietaria](LICENSE) (todos los derechos reservados; lo publicado antes conserva la Apache-2.0).

## Instalación y pruebas
- Entorno fijado: `docs/INSTALACION_LOCAL.md` (Mac, sin instalar dependencias en el sistema) y los `requirements*.lock`.
- Pruebas: `python -m unittest tests.test_r015_invariantes.GovernanceHeaders` (gobernanza) y el módulo de `tests/` afectado.
- Comprobación de conflictos antes de empujar: `python herramientas/comprobar_guardian_main.py todo`.

## Flujo
1. Abre una incidencia describiendo el problema o la mejora.
2. Rama desde `main`, un cambio por causa, con su prueba.
3. Los ficheros versionados suben su cabecera VERSIÓN y dejan copia en `legacy/` (ver `docs/POLITICA_DE_VERSIONES.md`).
4. Cada PR añade su entrada en `docs/registro/AAAA-MM-DD_<rama>.md` (formato en `docs/registro/README.md`).
5. La PR se fusiona con la CI «pruebas» en verde.

Los mapas producidos son un ejercicio de investigación sin valor oficial; los datos de origen (INE, Interior) conservan
sus condiciones de reutilización.
