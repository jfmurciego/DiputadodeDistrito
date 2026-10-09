# R008 — Fuentes congeladas para desarrollo rápido

**Fecha:** 2026-09-11  
**Objetivo:** eliminar la latencia del INE durante iteraciones de desarrollo sin cambiar los bytes canónicos usados por el procedimiento.

## Decisión
Durante desarrollo, los dos grandes inputs territoriales se reconstruyen desde fragmentos almacenados en `inputs/partes/`. La reconstrucción produce exactamente los dos ZIP canónicos históricos:
- `inputs/seccionado_2025.zip`
- `inputs/65034.csv.zip`

Se verifica primero el hash de cada fragmento y después el SHA-256 de cada ZIP reconstruido. La adquisición directa desde INE introducida en R006 se conserva en `herramientas/adquirir_fuentes_ine.py`, pero queda fuera de la ruta de desarrollo por razones de rendimiento. La validación/final futura volverá a utilizar fuente oficial remota como contraste independiente.

## Motivo
El servicio INE estaba consumiendo varios minutos antes incluso de iniciar el procedimiento. En fase de desarrollo esto penaliza cada iteración y no aporta valor adicional si los bytes de entrada ya están congelados, versionados y verificados por hash.

## Integridad
Hashes canónicos reconstruidos:
- `seccionado_2025.zip`: `55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4`
- `65034.csv.zip`: `91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3`

## Cambios
- configuración: 7.2.0 → 7.3.0;
- workflow: 2.4.0 → 2.5.0;
- workflow de desarrollo reconstruye los ZIP desde `inputs/partes/reconstruir_fuentes.sh` cuando M01-M03 necesitan reconstruirse;
- se mantienen las comprobaciones de `inputs/MANIFEST.sha256`;
- se conserva R006 como camino de validación/final futura.

## Regla de uso
- `iterativo`: reutiliza M01-M03 si la caché corresponde a la clave territorial vigente;
- `completo`: reconstruye los ZIP desde fragmentos y recalcula M01-M03;
- una futura ejecución de certificación/final debe reintroducir una ruta explícita de adquisición directa INE y comparar resultados contra la fuente congelada.

## Siguiente acción
Ejecutar el workflow vigente en modo `completo` una vez para crear/validar la base preparada con las fuentes reconstruidas; después, para cambios de M04/M05, usar `iterativo` y evitar reconstrucciones innecesarias.