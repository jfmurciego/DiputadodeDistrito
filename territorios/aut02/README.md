# Territorio: Aragón

**Estado:** validado — implantación de referencia DDD
**Baseline:** GitHub Run #9 `34599224954` / R016

## Resultado vigente

67 distritos; 1.463 secciones; 1.364.621 habitantes; Huesca 11 / Teruel 7 / Zaragoza 49; 0 cruces provinciales; 0 desconectados; 0 infracciones municipales; 0 bajo suelo; 0 sobre techo; `fuera_12=0`; máximo desvío 9,930 %.

## Estructura

- `config/aragon_2025.yaml`: copia canónica territorial de la configuración validada.
- `inputs/`: mismas fuentes Git congeladas que la ruta histórica `inputs/`.
- `resultados/`: referencia estructural a resultados/preparaciones existentes.
- documentación global de runs: `docs/EJECUCIONES/`.

## Compatibilidad

El workflow GitHub validado todavía usa las rutas históricas de raíz. No borrarlas hasta que un workflow multi-territorio reproduzca Run #9 usando exclusivamente este paquete.

## Próximo trabajo Aragón

R017 queda pendiente: auditoría de calidad territorial fina de los 67 distritos, con atención a compactación, cuellos, tentáculos, agrupaciones administrativas y naturalidad de fronteras. No continuar optimizando población por inercia.
