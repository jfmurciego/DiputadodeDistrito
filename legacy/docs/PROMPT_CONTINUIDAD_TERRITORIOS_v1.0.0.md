# Prompt de continuidad — estados territoriales DDD

Repositorio de referencia: `jfmurciego/DiputadodeDistrito` (`main`).

Continúa el proyecto **Diputado de Distrito** usando GitHub como fuente de verdad. Mantén el motor común en `ddd_core/` y `modulos/`; los territorios solo aportan configuración, inputs, documentación, pruebas y excepciones auditadas. No introduzcas parches territoriales ocultos. Todo cambio debe quedar versionado, con legacy de la versión anterior cuando corresponda y trazabilidad documental.

## Orden territorial y estado actual

1. **Aragón — territorio principal de referencia y foco actual.**
   - Estado: implantación validada y protegida.
   - Resultado vigente: 67 distritos, 1.463 secciones, 1.364.621 habitantes; Huesca 11 / Teruel 7 / Zaragoza 49; 0 cruces provinciales; 0 desconectados; 0 infracciones municipales; 0 bajo suelo; 0 sobre techo; `fuera_12=0`; máximo desvío 9,930 %.
   - M06 está materializado y validado con catálogo y composición completos.
   - Siguiente trabajo: auditoría territorial fina de los 67 distritos — compactación, cuellos, tentáculos, naturalidad de fronteras y coherencia administrativa. No reabrir optimización poblacional por inercia.
   - Referencia: `territorios/aragon/README.md`.

2. **Castilla y León — segunda implantación validada.**
   - Estado: validada hasta M06.
   - M05 cerró con 82 distritos, `hard=0`, `fuera_12=0` y desviación máxima aproximada de 11,98 %.
   - M06 materializó catálogo de 82 distritos y composición de 3.506 secciones.
   - M07 permanece bloqueado únicamente por falta de una fuente electoral territorial validada.
   - Referencia: `territorios/castilla_y_leon/` y `territorios/README.md`.

3. **Extremadura — tercera implantación.**
   - Estado: M01-M03 cerrados; M04/M05 en fase de generalización y pruebas topológicas.
   - Base cerrada: 964 secciones, 1.053.345 habitantes, topología M03 completamente conexa mediante predicado geométrico robusto y dos pasarelas administrativas auditadas en Don Benito.
   - K de trabajo: 65 distritos, reparto Hamilton 41/24 entre Badajoz y Cáceres.
   - EXT-12 demostró que existen movimientos locales que reducen fragilidad topológica sin romper las restricciones duras; EXT-13 está ensayando pulido topológico previo a M05. Estas pruebas siguen siendo experimentales y no deben confundirse con el foco territorial principal.
   - Referencia: `territorios/extremadura/`, workflows EXT-* y `territorios/README.md`.

4. **Andalucía — cuarta implantación.**
   - Estado: M01-M03 cerrados; pendiente de recibir la política M04 generalizada.
   - M01: 6.029 secciones, 8.676.713 habitantes, 0 faltantes.
   - M03: 16.671 aristas, 0 aislados, 0 provincias desconectadas y 0 municipios desconectados; dos pasarelas administrativas auditadas en Cortegana y Vélez-Málaga.
   - AND-03 debe esperar a que la política general de M04 quede suficientemente estabilizada; después deberá ejecutar su propio barrido de parámetros y no heredar ciegamente valores de Extremadura.
   - Referencia: `territorios/andalucia/` y `territorios/README.md`.

5. **Cataluña — quinta implantación.**
   - Estado: CAT-01 abierto; baseline M01-M03 en ejecución.
   - Provincias: Barcelona 08, Girona 17, Lleida 25, Tarragona 43.
   - Antes de fijar K, Hamilton, puentes administrativos o política M04 deben cerrarse de forma reproducible: secciones reales, población total y provincial, faltantes, aristas, aislados, componentes provinciales y municipios desconectados.
   - Cualquier discontinuidad debe auditarse individualmente antes de añadir puentes. Solo después de cerrar M01-M03 podrá reutilizar mecanismos ya validados en otros territorios.
   - Referencia: `territorios/cataluna/CONTINUIDAD.md`.

## Regla de continuidad

El orden de lectura y comparación es siempre: **Aragón → Castilla y León → Extremadura → Andalucía → Cataluña**. Aragón es la regresión territorial principal; Castilla y León es la segunda regresión validada; Extremadura sirve para generalizar M04/M05; Andalucía verifica escalabilidad; Cataluña es la siguiente implantación en construcción. No presentar Extremadura como territorio principal de trabajo ni alterar este orden sin una decisión explícita del usuario.
