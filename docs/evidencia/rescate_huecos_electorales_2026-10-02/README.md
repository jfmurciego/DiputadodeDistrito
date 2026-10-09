# Rescate de huecos electorales — evidencia 2026-10-02

Esta carpeta congela la evidencia pequeña y reproducible usada para validar electoral_gap_filler sin depender de hojas remotas cambiantes. Los artefactos brutos se identifican por URL, fecha de recuperación y SHA-256 en real_validation.json; los retales realmente utilizados se copian aquí con su fila, pestaña, página o mesa original.

## Resultado

- Extremadura: el delta 2.419 se descompone en 891 votos CERA de Badajoz, 994 CERA de Cáceres y 534 votos definitivos en dos secciones de Cáceres cuyo paquete principal contiene ceros explícitos. Los 534 no se sobrescriben; el resultado completo es BLOCK.
- Badajoz: la pestaña de terceros reproduce exactamente los 325.305 votos geográficos del primario y aporta 891 CERA, pero no es admisible para producción y sus magnitudes auxiliares no reconcilian con el DOE.
- Cáceres: la copia etiquetada como definitiva reconcilia exactamente con el DOE; las únicas 13 diferencias sección+candidatura se concentran en 1004201001 y 1012501001 y chocan con ceros explícitos del primario.
- Andalucía: el primario provisional tiene 6.044 secciones y 4.128.575 votos frente a 4.157.539 definitivos. OpTE se conserva sólo como evidencia/contraste y se usaron cero filas como relleno. El `main` ya contiene una ruta oficial SIEL 2026 (`adquirir_siel_andalucia_2026.py` + `adaptador_siel_andalucia_2026.py` + manual reproducible) que debe ser la siguiente vía de cierre en un entorno con acceso de red.
- Cuenca: el paquete vigente de Castilla-La Mancha 2023 ya contiene 196 secciones de Cuenca; no existe un hueco actual que justifique usar europeas 2024.

Ningún fichero de esta carpeta habilita registro, promoción o publicación. La admisibilidad de las copias de terceros permanece bloqueada.
