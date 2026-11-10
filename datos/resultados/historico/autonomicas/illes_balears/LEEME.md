# Baleares: datos aproximados en el distrito

Las cuatro elecciones de esta carpeta (2011, 2015, 2019, 2023) llevan `aproximado_en_distrito: true` en su `MANIFEST.json`
y en el de la comunidad. El motivo: la composición canónica del M06 vigente (`datos/composicion/illes_balears.csv`) se
construyó con el seccionado INE 2023 (670 secciones); el seccionado 2025 trae 5 secciones más (7.988 habitantes) que no
están en esa composición y se asignaron al distrito de la unión de secciones conocidas más próxima (empate: mayor
contacto). Los votos de esas secciones pueden estar en un distrito vecino del real. La suma y el cuadre global no cambian.
Quien consuma estos CSV por distrito debe tratarlos como aproximados en esas 5 secciones.
