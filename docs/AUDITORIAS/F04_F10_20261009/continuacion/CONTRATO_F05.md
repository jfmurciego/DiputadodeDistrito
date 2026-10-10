# F05 — adquisición y consumo offline

Versión1.0.0; 2026-10-10; base7ce06043fe74102196152ad07ad17f47b1779a6b. Sin cambio funcional necesario.

Adquisición oficial: herramientas/adquirir_fuentes_oficiales.py y herramientas/adquirir_fuentes_ine.py, reservada; no invocadas. Recuperación: herramientas/almacen_fuentes_local.py:recover importa exclusivamente archivos ya descargados y validados. Consumo canónico: consume resuelve identidad exacta y verifica archivo/receipt, sin adquisición ni fallback de red. Selección local: herramientas/seleccionar_paquete_fuentes.py valida manifest y bytes congelados; no adquiere si no hay candidato válido. Un rechazo se conserva como bloqueo.

Prueba dirigida nuevas entradas: verificar_offline.py con socket.connect, create_connection y DNS prohibidos; selección5 PASS y20 rechazos PASS por territorio/años/digest contradictorio. El validador canónico se ejecutó en los5 y conservó BLOCKED por receipt ausente/incompleto, sin modificar catálogo. Los14 resultados previos se reutilizan exactamente; no se repiten ensayos cerrados.

Regresión ZIP: tests/test_almacen_fuentes_local.py,1 passed,5 subtests passed,10 skipped por almacén explícito no configurado. Esas10 no se presentan como pruebas nuevas ni se reejecutan sobre entradas F01–F03. Warning esperado por duplicado ZIP intencional. Logs completos logs/contrato-almacen.*, offline-nuevas.*.
