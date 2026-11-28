<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Licencia del código: tres opciones para decidir
FECHA: 2026-11-27
ESTADO: PROPUESTA. No cambia ninguna licencia; decide el propietario
CAMBIOS: 1.0.0 — fichero nuevo (T-473, D-214).
MOTIVO: la licencia cerrada choca con «investigación verificable» y bloquea el kit de reproducción (T-472) y la
  revisión externa (T-474). El propietario necesita las opciones y sus consecuencias en lenguaje llano para elegir.
ANTERIOR: ninguna (fichero nuevo)
-->
# Licencia del código: tres opciones para decidir

Esta página no cambia nada. Explica cómo está hoy la licencia, dónde se contradice y qué pasaría con cada una de las
tres opciones. Al final hay una recomendación. Las marcas y la separación entre Deslinde y Diputado de Distrito quedan
fuera (van aparte).

**En una línea:** hoy nadie puede ejecutar el programa sin tu permiso por escrito, así que nadie de fuera puede
comprobar los mapas. La opción B lo permite para investigar y comprobar, sin uso comercial y sin que nadie pueda
copiarlo ni repartirlo.

No es asesoramiento jurídico. Antes de aplicar cualquier opción conviene que la lea quien te asesoró en el registro de
la propiedad intelectual.

---

## 1. Cómo está hoy (comprobado en el proyecto el 27-11)

| Dónde | Qué dice |
|---|---|
| `LICENSE` (1.1.0, 15-11) | Licencia propietaria, todos los derechos reservados. Apartado 2: no se permite «copiar, reproducir, distribuir, publicar, modificar, crear obras derivadas, sublicenciar o explotar comercialmente» sin autorización escrita. «El acceso al repositorio no concede ningún derecho de uso». |
| `LICENSE`, apartado 3 | Excepciones abiertas (D-92): datos abiertos y mapas publicados en CC BY 4.0; «Reglas y contratos (esquema y validador propios, sin el núcleo): CC BY 4.0»; plan y arquitectura publicados en CC BY-NC 4.0; visor y web, derechos reservados; fotos de la galería con su propia licencia. Todo ello «en el repositorio público de publicación». |
| `LICENSE`, apartado 4 | Hasta el 14-11-2026 todo estuvo bajo Apache-2.0, y quien recibió esas versiones conserva esos derechos, «que no pueden retirarse con efecto retroactivo». |
| `README.md` | Repite lo anterior: código propietario desde el 14-11; lo anterior conserva la Apache-2.0; datos en CC BY 4.0. |
| `CITATION.cff` | Tipo «software», título «motor reproducible de distritos uninominales», enlace a `LICENSE`. Dos DOI de Zenodo: la serie de mapas (10.5281/zenodo.24448721, «solo mapas, CC BY 4.0») y el mapa de Huesca 1.0.0 del 9-11 (10.5281/zenodo.24093968). |
| `README.md`, línea 6 | «Cada depósito contiene el código fuente del repositorio en esa versión». |
| `datos_abiertos/README.md` | CC BY 4.0, también con fines comerciales, citando la fuente. |
| Web (portada `visor/v4/index.html`) | Rótulo «INVESTIGACIÓN VERIFICABLE»; la descripción para buscadores dice «la investigación verificable». |
| Web (pie de todas las páginas) | «© 2026 … Todos los derechos reservados» y la reserva de acciones legales frente a plagio, reproducción no autorizada y falsa atribución. |
| Web, «Metodología» (`documentacion_publica/docs/metodo.md` 2.0.1) | Ya corregida (T-463): el código «se puede leer en GitHub, para que cualquiera pueda revisarlo. Su uso, copia o modificación requiere permiso escrito del autor». |
| `paquetes/deslinde/README.md` y `pyproject.toml` | «Paquete privado (D-94). La licencia la fija #744; hasta entonces, sin licencia de uso.» |
| Registro de la propiedad intelectual (T-281, #995) | Presentado el 23-11 como «Programa de ordenador» (Deslinde 1.0), con copia identificativa, memoria y declaración de uso de IA (`docs/PLAN.md`). El paquete se genera con `herramientas/preparar_paquete_pi.py`; los ficheros presentados no se guardan en el proyecto. |
| D-196 (22-11) | El proyecto sigue público en GitHub; Deslinde se protege con la licencia propietaria y el registro. El código de Deslinde y su definición formal son públicos, también en el historial; las versiones antiguas siguen bajo Apache-2.0. Se cancela el proyecto aparte «de publicación» (T-445). |

**No comprobado desde aquí:** la licencia que muestran en Zenodo los dos depósitos y qué ficheros contienen (Zenodo no
es accesible desde la sesión en la nube). Conviene mirarlo en la web de Zenodo antes de decidir.

## 2. Contradicciones

1. **«Verificable» frente a «sin ningún derecho de uso».** Verificar un mapa es volver a ejecutar el programa y ver que
   sale lo mismo. Hoy eso exige tu permiso por escrito. Lo que se puede hacer sin permiso es leer el código, que no es
   lo mismo que comprobar el resultado. La página de Metodología ya lo dice con honradez; la portada no.
2. **Las excepciones apuntan a un sitio que no existe.** El apartado 3 abre cosas «en el repositorio público de
   publicación», que se canceló el 22-11 (D-196, T-445). Queda en el aire si los mismos ficheros, aquí, están abiertos o
   cerrados. Los datos se salvan porque `datos_abiertos/README.md` declara su propia licencia; las reglas y el
   validador, no.
3. **«Reglas y validador en CC BY 4.0», pero nadie sabe cuáles son.** Ningún fichero dice que esté bajo esa excepción, y
   las reglas viven dentro del paquete de Deslinde (`paquetes/deslinde/src/deslinde/reglas/`), que su propio README
   declara «sin licencia de uso». Además, CC BY 4.0 dice expresamente que no da derechos de patente («Patent and
   trademark rights are not licensed under this Public License»): es una licencia pensada para obras, no para código.
4. **El README de Deslinde está desfasado.** Habla de «paquete privado (D-94)» y de una licencia pendiente (#744), cuando
   D-196 lo dejó público con la licencia general.
5. **Lo cerrado protege menos de lo que parece.** Todo lo publicado hasta el 14-11 sigue bajo Apache-2.0, que permite
   copiarlo, modificarlo, distribuirlo y usarlo comercialmente. Según D-196, eso incluye código de Deslinde en el
   historial y, según el README, el depósito de Huesca del 9-11 en Zenodo. Quien quiera aprovecharse puede partir de
   ahí; quien quiera comprobar honradamente, no puede usar lo de hoy.
6. **Qué hay en Zenodo se cuenta de dos formas.** El README dice que «cada depósito contiene el código fuente del
   repositorio en esa versión»; `docs/PUBLICACION_ZENODO.md` dice que desde D-146 se suben solo los mapas firmados, con
   CC BY 4.0, y «no: motor, código del proyecto ni ZIP del repositorio». Lo más probable es que el README describa el
   depósito de Huesca del 9-11 (anterior al 14-11, por tanto bajo Apache-2.0) y no los siguientes, pero hay que
   comprobarlo en Zenodo.
7. **La cita dice «software reproducible»** (`CITATION.cff`) y enlaza a una licencia que no deja reproducirlo.
8. **El pie de la web reserva todos los derechos** en páginas que también ofrecen datos en CC BY 4.0, sin mencionar la
   excepción (la página de auditoría y registro sí la matiza).
9. **El nombre del titular aparece de dos formas**: corta en `LICENSE` y `CITATION.cff`, completa en el pie de la web.
   No es grave, pero conviene unificarlo cuando se toque la licencia.

## 3. Las tres opciones

### A · Cerrada, como hoy

- **Qué pasa hoy:** es la situación actual (`LICENSE` 1.1.0).
- **Qué permite:** leer el código en GitHub. Los datos y mapas siguen en CC BY 4.0.
- **Qué no permite:** ejecutar, copiar, modificar o repartir el código sin tu permiso por escrito, para nadie y para
  ningún fin.
- **Qué recibes:** el máximo control sobre lo nuevo, sin trabajo. Cada comprobación externa pasa por ti, caso a caso.
- **Qué pasa si eliges esta:** hay que quitar «verificable» de la portada y de la cita, porque no es verdad; el kit de
  reproducción (T-472) y la revisión externa (T-474) solo funcionan con un permiso escrito a cada persona. Las
  contradicciones 2 a 8 siguen y hay que corregirlas igual.
- **Licencia concreta:** la propia del proyecto (`LICENSE`). No hay enlace oficial externo.

### B · Se puede leer y ejecutar para comprobar o investigar; sin uso comercial ni copia

- **Qué pasa hoy:** no existe; habría que cambiar `LICENSE` para el código.
- **Licencia concreta:** **PolyForm Strict 1.0.0**, <https://polyformproject.org/licenses/strict/1.0.0>.
- **Qué permite (texto de la licencia):** hacer con el programa todo lo que haría falta tu permiso «for any permitted
  purpose, other than distributing the software or making changes or new works based on the software». Son fines
  permitidos: «Any noncommercial purpose»; el uso personal «for research, experiment, and testing for the benefit of
  public knowledge, personal study…»; y el uso por «any charitable organization, educational institution, public
  research organization, public safety or health organization, environmental protection organization, or government
  institution». O sea: una universidad, un centro público de investigación, un periodista o un particular pueden
  descargarlo y ejecutarlo para comprobar que los mapas salen iguales.
- **Qué no permite:** repartir copias del programa ni hacer versiones cambiadas o derivadas («other than distributing
  the software or making changes or new works»). Tampoco ceder la licencia a otro («These terms do not allow you to
  sublicense or transfer»). Los usos comerciales quedan fuera porque solo se permiten los fines citados.
- **Otras cosas que dice:** da también licencia de patentes para usar el programa, que se pierde si el usuario te
  reclama por patentes; si alguien incumple y se le avisa por escrito, tiene 32 días para corregirlo o pierde la
  licencia; el programa se ofrece «as is», sin garantía. No impide que des a otros licencias distintas («or prevent the
  licensor from granting licenses to anyone else»): puedes seguir vendiendo o cediendo permisos aparte.
- **Ojo:** la licencia no define qué es «comercial»; habrá casos dudosos (una consultora que lo usa para un informe
  pagado). Y al no permitir cambios, alguien que quiera probar una variante del método tendría que pedirte permiso.
- **Variante más abierta:** **PolyForm Noncommercial 1.0.0**,
  <https://polyformproject.org/licenses/noncommercial/1.0.0>. Los mismos fines, pero además permite repartir copias y
  hacer cambios («an additional copyright license to distribute copies» y «to make changes and new works… for any
  permitted purpose»), siempre que quien reciba una copia reciba también los términos. No encaja con «sin copia».
- **Qué recibes:** «verificable» pasa a ser verdad sin pedirte nada caso a caso; el kit (T-472) y la revisión externa
  (T-474) pueden darse a cualquiera; sigues sin competidores comerciales que lo reutilicen legalmente y conservas el
  registro de la propiedad intelectual tal cual.
- **Qué pasa si no se elige:** la licencia sigue chocando con «verificable» y los bloques F (validación externa) no
  llegan a su meta.

### C · Se abren las reglas y el validador; el motor sigue cerrado

- **Qué pasa hoy:** en parte ya está escrito (apartado 3: «Reglas y contratos… CC BY 4.0»), pero no se sabe qué ficheros
  son ni existe el sitio donde se publicarían (contradicciones 2 y 3).
- **Licencia concreta:** **Apache-2.0**, <https://www.apache.org/licenses/LICENSE-2.0>, para las reglas y el validador
  separados en su propio paquete. El motor sigue con `LICENSE` (opción A).
- **Qué permite (texto de la licencia):** «reproduce, prepare Derivative Works of, publicly display, publicly perform,
  sublicense, and distribute» las reglas y el validador, también con fines comerciales (no tiene ninguna limitación de
  uso comercial), más una licencia de patentes. Quien reparta copias debe incluir la licencia y los avisos (sección 4).
  Cualquiera podría comprobar que un mapa publicado cumple las reglas: población dentro del margen, distritos de una
  pieza, municipios sin partir.
- **Qué no permite:** nada sobre el motor; sigue cerrado. Por tanto, nadie puede comprobar que el mapa sea el que el
  motor elige de verdad, solo que es válido.
- **Qué recibes:** una comprobación parcial y honrada («el mapa cumple las reglas») sin abrir el motor. Pero exige
  separar las reglas del núcleo de Deslinde, que hoy van juntas: es trabajo de código, no solo de papel.
- **Qué pasa si no se elige:** queda la excepción del apartado 3 a medias, que conviene corregir o borrar en cualquier
  caso.

### Resumen

| | A · Cerrada | B · Comprobar sin copiar | C · Reglas abiertas |
|---|---|---|---|
| Alguien de fuera puede repetir un mapa | Solo con permiso escrito | Sí, si no es para negocio | No |
| Alguien puede comprobar que un mapa cumple las reglas | Solo con permiso | Sí | Sí |
| Alguien puede copiar o repartir el motor | No | No | No |
| Uso comercial del motor | No | No | No |
| «Investigación verificable» es cierto | No | Sí | En parte |
| Trabajo para aplicarla | Corregir textos | Cambiar `LICENSE` y textos | Separar código y cambiar textos |

## 4. Recomendación: B (PolyForm Strict 1.0.0 para el código)

Es la única que hace verdad «verificable» sin regalar el motor. Permite exactamente lo que necesitan el kit y los
revisores (descargar y ejecutar) y prohíbe lo que quieres evitar (repartir copias, versiones derivadas, negocio). Es una
licencia publicada y estable, con nombre propio, que un revisor reconoce sin tener que leer un texto hecho a medida.
No toca los datos ni los mapas, que siguen en CC BY 4.0, ni el registro de la propiedad intelectual.

La opción C protege lo mismo que B pero comprueba menos y cuesta más; tiene sentido solo si no quieres que nadie
ejecute el motor. La A obliga a retirar «verificable».

Si eliges B, la PR que la aplique tendría que, como mínimo: cambiar `LICENSE` (con su versión anterior en `legacy/`),
cerrar las contradicciones 2 a 9 de esta página, decidir qué se hace con la excepción de reglas y validador, y poner la
cita y el pie de la web en coherencia. Esta PR no hace nada de eso.

## 5. Cómo se comprobaron los textos de las licencias

Las webs de PolyForm y de Creative Commons no son accesibles desde la sesión en la nube. Las citas salen de copias de
los textos oficiales:

- PolyForm Strict 1.0.0: repositorio oficial del proyecto PolyForm en GitHub, etiqueta 1.0.0
  (sha256 `9eb48619fbc193ab7bb327b090cfcc703000265b83e670f81f231d0b1c43c56e`).
- PolyForm Noncommercial 1.0.0: lista oficial de licencias SPDX
  (sha256 `ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8`).
- CC BY 4.0 (exclusión de patentes): misma cláusula 2.b.2 en el texto SPDX de CC BY-NC-ND 4.0; la de CC BY 4.0 conviene
  confirmarla en <https://creativecommons.org/licenses/by/4.0/legalcode.es>.
- Apache-2.0: leída en <https://www.apache.org/licenses/LICENSE-2.0>.
