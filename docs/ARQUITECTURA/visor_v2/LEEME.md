<!--
Nombre: Especificación del visor v2
Versión: 1.0.0
Fecha: 2026-11-08
Alcance: Maqueta aprobada por el propietario como especificación de T-109
Estado: candidato
Cambios/motivo: fichero nuevo (D-24)
Anterior: ninguna (fichero nuevo)
-->

# Visor v2 · especificación (D-24)

Aprobada por el propietario el 08-11. Maqueta navegable: https://claude.ai/artifact/ATNVGbGxPwo2KCkREZuMxg
(privada del propietario); copia en `maqueta_visor_v2.html` (se abre con un servidor local junto a los dos JSON).

## Qué fija
- Portada «Mapa»: dos vistas separadas, «Congreso de los Diputados» y «Parlamentos autonómicos», sin controles compartidos.
  - Congreso: mapa de España (Canarias desplazada en recuadro), partido más votado por provincia, hemiciclo y ficha de
    provincia al pulsar; chips de sistema (Real 350 · 350 distritos T-102 · 407 distritos) y de capa (más votado, rotación,
    participación, secciones); barra de elecciones generales 2011-2026; lo que no tiene datos sale gris con su motivo.
  - Autonómicos: el mapa es el selector (pulsar comunidad → zoom y ficha); sin desplegables.
- Pestañas secundarias del modelo v3 del propietario: Nacional, Autonómico, Elecciones y Método, con las cifras del catálogo
  (407, 350, 52, 19, 1.262 y reparto por provincia y parlamento) y el visor de producción incrustado donde corresponda.
- Textos: todos los textos de las pestañas salen de `web/textos.md` (`## clave` + texto), que escribe el propietario; la página
  real no lleva textos inventados. Editor `?edit=1` para previsualizar y copiar el fichero.
- Estilo de la v3 (papel, tinta, rojo; Georgia en titulares); topónimos solo en español; aviso «sin valor oficial».

## Límites
- `provincias.json` y `comunidades.json` son geometría de la maqueta (INE CC BY 4.0, vía el espejo del Observatorio, D-8,
  con nombres en español). En producción se usa la geometría propia del proyecto.
- Votos y escaños: `configuracion/resultados_oficiales_congreso_2023.csv` (BOE-A-2023-18907, sha256 c7a636f2…).
