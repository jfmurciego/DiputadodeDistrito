<!--
Nombre: Visor v2 (vista previa privada)
Versión: 1.0.0
Fecha: 2026-11-08
Alcance: visor/v2/ (T-109, D-24)
Estado: candidato
Cambios/motivo: fichero nuevo; implementa la especificación docs/ARQUITECTURA/visor_v2/
Anterior: ninguna (fichero nuevo)
-->

# Visor v2 · vista previa privada

Implementa `docs/ARQUITECTURA/visor_v2/LEEME.md`. **No está enlazado ni publicado**: la v1 (`visor/`, `visor/nacional/`) sigue igual
hasta que el propietario apruebe esta versión.

## Verla (Mac, zsh), desde la raíz del repositorio en la rama de la PR
```
python3 -m http.server 8000
```
y abrir `http://localhost:8000/visor/v2/` (con `?edit=1` aparece «Editar textos»). Alternativa, un solo fichero que se abre con doble clic:
`python3 visor/v2/construir_vista_previa.py ~/Desktop/visor_v2.html` (necesita internet para MapLibre).

## Datos
- `datos/provincias.json` y `datos/comunidades.json`: geometría INE (CC BY 4.0, espejo del Observatorio) de la maqueta, con dos
  correcciones: se quitaron 156 polígonos vacíos (rompían MapLibre) y se recolocó Ávila (estaba desplazada −5,6° / −6,6°; encaja en su
  hueco con IoU 0,9999). Votos y escaños = `configuracion/resultados_oficiales_congreso_2023.csv` (BOE-A-2023-18907), comprobados
  contra la maqueta: 52 provincias sin diferencias, 350 escaños y 407 distritos.
- La geometría provincial propia del proyecto no está versionada (solo los GeoJSON de distritos, que no se versionan);
  las pestañas Nacional y Elecciones incrustan el visor de producción `../nacional/`.
- Textos: `web/textos.md` (`## clave`), vacío hasta que lo escriba el propietario; los huecos solo se ven con `?edit=1`.
