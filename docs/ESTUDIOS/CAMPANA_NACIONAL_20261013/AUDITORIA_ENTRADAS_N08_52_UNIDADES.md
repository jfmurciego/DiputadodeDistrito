# Verificación diagnóstica de entrada de las 52 circunscripciones

Este incremento añade `herramientas/auditar_52_entradas_congreso_n08.py`, un único recorrido de las **52 entradas provinciales/ciudades autónomas** de N08, comprobando en cada una el SHA del manifiesto N08 fijado en código, la integridad de su artefacto, resumen, cuotas y puertas de gobierno.

Uso de sólo lectura:
```bash
python -m herramientas.auditar_52_entradas_congreso_n08 --output /tmp/n08_52_input_report.json
```

El JSON de salida se genera localmente, no modifica la fuente original ni ejecuta M04/M05/M06. Un resultado `input_checks_passed=52` significa **sólo conformidad de entradas N08**, nunca cartografía 2025 independiente CNIG/IGN acreditada, ni 407 distritos producidos, ni excepciones aprobadas. Todo expediente debe preservar esa distinción.

Hay al menos cinco provincias con bloqueo matemático necesario bajo contigüidad estricta (07, 09, 17, 34, 36); el informe lista otros avisos que puedan existir, sin pretender resolverlos. El resultado de pruebas y SHA exacto deberá citarse tras CI del commit que introduzca el diagnóstico.
