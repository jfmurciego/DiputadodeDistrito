## 2026-11-24 — T-449 — Autonómicas de Castilla-La Mancha 2023: copia archivada como fuente no oficial y doble vuelta por municipio

- Causa: el portal de la Junta ya no sirve `Resultados_CLM_2023.xlsx` (301 a `/system/404`). El run 45283716584 midió su copia en la Wayback
  (captura 20261023040608, sha256 7591997d…47ca, 322.602 B) sin subirla. El propietario (24-11, vía Planificador: «sí a todo») la aprueba
  como fuente NO oficial, cuadrada con el Observatorio, en R2 fuera de `fuentes/` y con la doble vuelta por municipio sobre el run 43745006294.
- Cambio:
  - `herramientas/espejo_fuente_oficial.py` 1.3.0:
    - el modo URL directa admite `tipo: copia_archivada` (con `oficial: false`, `url_original` y `captura`);
    - `copias_archivadas_destino` admite `fuentes-archivadas`: con la principal copia, las copias y su manifiesto van a
      `fuentes-archivadas/<organismo>/<año>/`. Un original del conjunto (p. ej. el PDF) no va ahí y queda «no_subido». Nunca una copia
      va a `fuentes/` (D-198).
    - Una entrada `copia_archivada` no puede declararse oficial (aut08 lleva `oficial: false` explícito).
  - `configuracion/espejos_fuentes_oficiales.json` 1.3.0: aut08 en modo URL directa (URL de la Wayback, huella y bytes fijados).
  El espejo no usa `rutas_r2`: la clave va codificada en la herramienta, así que la subida no depende de T-443.
  - `herramientas/calendario_autonomicas.py` 1.1.0: `SUSTITUCIONES` (aut08 2023: URL de la Wayback y proveedor «copia archivada del fichero
    oficial, fuente no oficial»). `fuente_sha256` sigue siendo la del Observatorio, porque es la fuente del calendario. CSV regenerado: solo
    cambia esa fila.
  - `herramientas/adaptador_clm_2023.py` 1.0.0, nuevo. Verifica el volcado de la hoja «Municipios_Resultados»
    (`fuentes/castilla_la_mancha_autonomicas_2023/municipios_resultados.csv`, sha256 6d44efc5…, el del manifiesto del run 45283716584) y
    `fuentes/observatorio_autonomicas/hauteskundea_08-202305.json` (sha256 0443c79e…, «provisional», no oficial). Cuadre EXACTO o falla:
    - votos por candidatura y provincia;
    - CERA por provincia;
    - D'Hondt con el 3 %: 33 escaños (17/12/4).
  - `datos/resultados/doble_vuelta_autonomicas/aut08/202305/` (`doble_vuelta_votos_aut.py`, nivel municipio, run 43745006294):
    1.070.325 votos en 33 distritos; CERA (2.558 votos) fuera de distritos.
  - `herramientas/bloques_autonomicas.py` 1.3.0: aut08 en `VIGENTES`. «UNIDAS PODEMOS CLM» entra en el criterio aprobado de coaliciones con
    Podemos/IU/Sumar (Izquierdas). Tablas de bloques y alias regeneradas: solo se añaden filas de aut08.
- Pruebas: `tests/test_adaptador_clm_2023.py`, con los totales literales del Observatorio, D'Hondt a mano, huella alterada y no cuadre.
  `tests/test_t449_espejo_fuente_oficial.py` 1.0.3:
  - copia directa;
  - `fuentes-archivadas`;
  - `fuentes` rechazado para copias.

  Calendario, bloques, doble vuelta, P75 y gobernanza, en verde con Python 3.11. `test_t427…test_reagregacion…` falla igual en `main`, por
  shapely en el entorno.
- Pendiente:
  - subida a R2 con el P10 «Espejo de fuente oficial» aut08 (Operador, frase del propietario);
  - P75 de aut08 después;
  - `rutas_r2` (T-443) aún no conoce la raíz `fuentes-archivadas/`.
