# Deslinde 1.0 — protección documental y acciones (2026-11-13)

Estado: propuesta documental separada del motor productivo. No modifica `ddd_motor2/`, `LICENSE` ni el generador de mapas.

## 1. Atribución inmediata

- `CITATION.cff` identifica a Jesús Murciego como autor citado del proyecto.
- `NOTICE` identifica Deslinde 1.0, su código y su documento formal.
- `LICENSE` actualmente es Apache-2.0. Este aviso no revoca licencias anteriores ni prohíbe usos permitidos por ellas. Tampoco desconoce derechos de otras personas que hayan contribuido.
- Conservar los enlaces de versiones y commits originales como prueba del historial.

## 2. Generar paquete de evidencia sin exponer secretos

Desde el repositorio local, en la rama donde esté esta herramienta:

```bash
python3 herramientas/expediente_deslinde.py --salida /tmp/Deslinde-1.0-evidencia.zip
python3 herramientas/expediente_deslinde.py --salida /tmp/Deslinde-1.0-evidencia.zip --verificar
```

Resultado: ZIP reproducible del código fuente seleccionado (motor, módulos, núcleo, herramientas y documentación), `EVIDENCIA/MANIFEST_SHA256.json` con SHA-256 de cada archivo, `EVIDENCIA/MEMORIA_REGISTRO.md` y archivo externo `Deslinde-1.0-evidencia.zip.sha256`. El contenido del ZIP procede exclusivamente del commit Git HEAD, no de archivos locales sin confirmar.

**No subir el ZIP a un repositorio público ni compartirlo indiscriminadamente.** Conservar una copia privada e inmutable junto al `SHA256`, fecha, commit y justificante de depósito. La memoria exige completar manualmente titularidad, colaboradores, decisiones creativas, fecha e intervención de IA. Antes del registro, comprobar que el paquete contiene la totalidad del código fuente de la obra concreta que se desea registrar.

## 3. Inscripción oficial de software

En el Registro de la Propiedad Intelectual que corresponda, seleccionar «programa de ordenador», preparar:
- Código fuente completo de la obra a inscribir.
- Ejecutable o justificación de por qué no existe un binario independiente (Deslinde se invoca como código Python).
- Memoria descriptiva con finalidad, lenguaje, entorno, diagrama de flujo y relación de ficheros.
- Declaración responsable y comprobable de autoría, titularidad y participación creativa humana; explicar el uso de herramientas de IA si existieron.
- Pago de la tasa y conservación del resguardo con número de expediente.

Referencia oficial: https://www.cultura.gob.es/cultura/areas/propiedadintelectual/mc/rpi/registro-obras/como-registrar/progordenador.html
Solicitud en Madrid: https://sede.comunidad.madrid/inscripciones-registro/inscrip-derechos-propiedad-intelectual

**No se ha presentado ninguna inscripción.** La firma, las declaraciones y el registro los debe formalizar la persona titular.

## 4. Si aparece una copia que incumple la licencia

- Conservar URL exacta, fecha, capturas, ZIP del repositorio sospechoso, identificadores Git y comparación de código; no denunciar sin verificar derechos y permiso de reutilización.
- Identificar la infracción concreta: supresión de avisos Apache/NOTICE, atribución falsa, incumplimiento de distribución o uso de material no cubierto por licencia.
- Enviar aviso de subsanación con pruebas; si procede, usar la guía de GitHub para reclamaciones copyright: https://docs.github.com/es/site-policy/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice

## 5. Decisión de explotación futura (NO ejecutada)

Con Apache-2.0, la copia y explotación comercial **están permitidas con condiciones**. Si se quiere prohibirlas en nuevas versiones, requiere un nuevo régimen de licencias para las partes sobre las que el titular pueda decidir, comprobando derechos de todos los colaboradores y dependencias; las versiones ya publicadas bajo Apache-2.0 siguen disponibles bajo esa licencia. No modificar `LICENSE` sin una decisión expresa de la persona titular.
