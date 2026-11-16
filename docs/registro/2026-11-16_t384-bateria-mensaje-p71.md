## 2026-11-16 — T-384 — El error de paquete P10 ausente remite a P70/P71

- Causa: `BATERIA_FALTA_PAQUETE_P10` mandaba al Operador a «VER Verificación del motor» con `archivar_p10=<run>`; ese workflow y esa entrada ya no existen (P80, D-132).
- Cambio: `herramientas/bateria_motor.py` 1.4.3 (copia 1.4.2 en `legacy/`): el mensaje remite a «P70 Archivo · P71 archivar · paquete de fuentes de un territorio» con el territorio, sin run id ni parámetros técnicos (D-130). Solo cambia el texto. Igual para `BATERIA_PAQUETE_P10_CORRUPTO`.
- Pruebas: nuevo `test_t298_espejo_ine.…test_falta_paquete_remite_a_p71` (ambos mensajes citan P70/P71 y no contiene `bateria-motor`, `archivar_p10` ni «VER Verificación del motor»).
- Riesgos: ninguno. No lanza ni publica.
