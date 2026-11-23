<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Descripción de Deslinde para la copia identificativa
FECHA: 2026-11-23
ESTADO: candidato
CAMBIOS: 1.0.0 — fichero nuevo (T-281).
MOTIVO: D-196: la copia identificativa del Registro de la Propiedad Intelectual lleva una descripción del programa en
  lenguaje llano. La imprime `herramientas/preparar_paquete_pi.py` tras la portada (sin esta cabecera).
ANTERIOR: ninguna (fichero nuevo)
-->
# Descripción del programa

Título: Deslinde 1.0. Delimitación reproducible de distritos uninominales.
Autor: [AUTOR].

## Qué hace

Deslinde es un programa de ordenador que divide un territorio (una provincia o una comunidad autónoma) en distritos
electorales de un solo escaño. Parte de las secciones censales oficiales, su población y sus vecindades, y propone el
mapa de distritos que mejor cumple unas reglas fijas: que los distritos tengan una población parecida, que sean de una
pieza, que no partan municipios más de lo imprescindible y que respeten, en lo posible, las divisiones naturales del
territorio (partidos judiciales, comarcas y zonas de movilidad), con formas compactas.

## Cómo lo hace

1. Comprueba cada plan candidato con un núcleo único de reglas (población entre un mínimo y un máximo, contigüidad,
   municipios y provincias): un plan que no las cumple nunca se elige.
2. Genera varios candidatos: un trazado canónico, diez cadenas de recombinación aleatoria (ReCom ponderado), el mapa
   vigente cuando existe y, en territorios pequeños, un candidato exacto por programación con restricciones.
3. Elige el mejor candidato válido con una función de calidad fija («D8»): primero la población dentro de la
   tolerancia y, a igualdad, menos partidos judiciales y comarcas partidos, mejor forma y cortes por donde hay menos
   vínculo entre secciones.
4. Todo es reproducible: el azar sale de una semilla pública calculada con las huellas (sha256) del padrón y del
   seccionado oficiales y el código oficial del territorio. Con los mismos datos se obtiene el mismo mapa, bit a bit.

## Qué contiene este depósito

- El código fuente del paquete «deslinde» (lenguaje Python) y su configuración.
- La definición formal del método (`docs/ARQUITECTURA/DESLINDE_1_0.md`).
- Los estudios que la sostienen (mediciones de naturalidad, batería de pruebas, cotas y certificador exacto).

El índice siguiente da la huella sha256 de cada fichero del paquete ZIP; el código fuente se imprime a continuación.
