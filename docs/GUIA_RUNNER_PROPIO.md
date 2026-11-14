# Guía del runner propio de GitHub Actions (Linux y Windows)

**Versión:** 1.0.0  
**Fecha:** 2026-11-14  
**Estado:** candidato

Tarea T-274 parte A (D-93). Solo documentación: no cambia workflows, catálogo, contratos ni territorios. El cambio de
`runs-on` (parte B) va después de T-220. Sin secretos ni rutas personales: los valores entre `<…>` los pone quien registra.

## 1. Cuándo y para qué
- El repositorio de trabajo es privado (D-91): los minutos de Actions de pago salen de la cuota. Un runner autoalojado
  (self-hosted) del propietario ejecuta la CI y las Campañas sin consumir minutos; los artefactos pesados van a R2 (ARC).
- Solo en el repositorio privado. **Nunca** se registra un runner en un repositorio público (D-93): un PR de un tercero
  podría ejecutar código en la máquina del propietario.

## 2. Requisitos de la máquina
- 64 bits, 4 vCPU o más y 16 GB de RAM como mínimo para la CI; las Campañas (motor M04/M05) piden lo que se mida en
  `.claude/rules/diagnostico-local.md`. Disco 100 GB libres. Salida HTTPS a github.com, api.github.com,
  *.actions.githubusercontent.com, objects/pipelines de Actions, PyPI y `boe.es`. Sin entrada abierta: el runner solo sale.
- Python y dependencias: las que instala el propio workflow (`actions/setup-python`). `PYTHONHASHSEED=0` lo fija el workflow.
- Un runner = un trabajo a la vez. Para paralelismo, varios runners en el mismo equipo (carpetas y usuarios distintos).

## 3. Obtener el token de registro
Repositorio privado → Settings → Actions → Runners → New self-hosted runner. Elige el sistema y copia el token de registro
(caduca en una hora; se usa una vez; no se guarda en ningún fichero versionado). Alternativa por REST (permiso de
administración del repositorio): `gh api -X POST repos/<owner>/<repo>/actions/runners/registration-token --jq .token`.

## 4. Linux (Ubuntu 24.04, servicio systemd)
```bash
sudo adduser --disabled-password --gecos "" ghrunner        # usuario sin privilegios, sin sudo
sudo -iu ghrunner
mkdir actions-runner && cd actions-runner
# Descarga la versión vigente que muestra la página «New self-hosted runner» (comprueba el sha256 que indica)
curl -fsSLo runner.tar.gz <URL_DEL_PAQUETE_LINUX_X64>
echo "<SHA256_PUBLICADO>  runner.tar.gz" | sha256sum -c -
tar xzf runner.tar.gz
./config.sh --url https://github.com/<owner>/<repo> --token <TOKEN> \
  --name ddd-linux-01 --labels ddd,linux --unattended --replace
exit                                                        # volver al usuario con sudo
cd /home/ghrunner/actions-runner
sudo ./svc.sh install ghrunner && sudo ./svc.sh start && sudo ./svc.sh status
```
Dependencias del sistema: `sudo ./bin/installdependencies.sh` (una vez, como root). El servicio arranca con el equipo y se
reinicia solo.

## 5. Windows (PowerShell como administrador, servicio)
```powershell
mkdir C:\actions-runner; cd C:\actions-runner
Invoke-WebRequest -Uri <URL_DEL_PAQUETE_WINDOWS_X64> -OutFile runner.zip
(Get-FileHash runner.zip -Algorithm SHA256).Hash        # comparar con el sha256 publicado
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory("$PWD\runner.zip", "$PWD")
.\config.cmd --url https://github.com/<owner>/<repo> --token <TOKEN> `
  --name ddd-windows-01 --labels ddd,windows --unattended --replace --runasservice
```
`--runasservice` lo instala como servicio de Windows. Usa una cuenta local sin privilegios de administrador
(`--windowslogonaccount <cuenta>` y `--windowslogonpassword` pedido en el momento, nunca guardado). Los workflows actuales
usan `bash`: instala Git for Windows (trae `bash`) o ejecuta solo en Linux hasta la parte B; el runner Windows queda
registrado pero sin trabajos hasta que se le dirijan.

## 6. Etiquetas
El runner lleva automáticamente `self-hosted`, el sistema (`Linux`/`Windows`) y la arquitectura (`X64`). Se añaden
`ddd` (todos los del proyecto) y `linux`/`windows`. Los workflows pedirán `[self-hosted, ddd]` (D-93; Linux por defecto,
`[self-hosted, ddd, windows]` para lo específico). Etiquetas extra opcionales: `pesado` (máquina grande, para M04/M05) y
`ci` (máquina pequeña). Se cambian sin reinstalar: `./config.sh remove` y volver a registrar, o desde Settings → Runners.

## 7. Seguridad (repositorio privado)
1. Solo repositorio privado; confirmar en Settings que el grupo de runners no lo comparte con repositorios públicos
   (Organization → Runner groups: «Selected repositories»).
2. En Settings → Actions → General: «Fork pull request workflows» desactivado o «Require approval for all outside
   collaborators». Ningún workflow `pull_request_target` con checkout del código de la PR.
3. Usuario del servicio sin sudo, sin credenciales personales (ni SSH, ni `gh` con sesión, ni navegador con sesiones). Solo el
   `GITHUB_TOKEN` de cada trabajo y los secretos del repositorio (R2, etc.), que llegan por entorno y no se escriben a disco.
4. Los runners autoalojados **no** son efímeros por defecto: el espacio de trabajo y las cachés persisten entre trabajos.
   Cada workflow ya hace checkout limpio; el mantenimiento (§10) borra `_work`. Para más aislamiento: `--ephemeral`
   (un trabajo por registro) con un supervisor que reregistre, o una máquina virtual restaurada desde instantánea.
5. Máquina dedicada o VM, aislada de la red doméstica o de trabajo; disco cifrado; actualizaciones del sistema automáticas.
6. Limitar a quien puede lanzar workflows (permisos del repositorio) y mantener `CODEOWNERS`/protección de rama.
7. Registrar el runner con el token de un solo uso; revocar (`config.sh remove`) al retirar la máquina.

## 8. Dejar `runs-on` detrás de una variable (solo descripción; parte B)
Idea, para aplicar tras T-220 y en una PR propia: una variable de repositorio `DDD_RUNNER` (Settings → Secrets and variables
→ Actions → Variables) y, en cada job, `runs-on: ${{ fromJSON(vars.DDD_RUNNER || '"ubuntu-24.04"') }}`. Con la variable vacía
sigue `ubuntu-24.04` (hoy); con `["self-hosted","ddd"]` pasa todo al runner propio, y volver atrás es borrar la variable,
sin PR. Notas: la variable no existe en forks; los workflows reutilizables (`_reutilizable-*`) reciben el valor desde quien
los llama; los tests de seguridad de workflows (`test_workflow_safety`) tendrán que aceptar la expresión. Ahora hay 84 jobs con
`ubuntu-24.04` y 1 con `ubuntu-latest`.

## 9. Coste
- Runner propio: 0 minutos de Actions, a cambio de electricidad, hardware y mantenimiento. GitHub no cobra por el runner
  autoalojado en el plan actual; la cuota de **artefactos** sigue aplicando (T-271): lo pesado, a R2.
- Mientras no esté registrado, Actions de pago es el puente temporal (D-93).

## 10. Mantenimiento
- Actualización del agente: automática; si el servicio queda en «offline» tras una versión nueva, reiniciar el servicio.
- Limpieza semanal de `_work` y de cachés de pip; vigilar el disco (las Campañas generan GB).
- Parches del sistema y reinicio programado fuera del horario de Campañas.
- Reemplazo: `./config.sh remove --token <TOKEN_DE_BAJA>` y registrar el nuevo con otro nombre.
- Un runner caído deja los trabajos en cola (no fallan): la parte B incluirá cómo volver a `ubuntu-24.04` con una variable.

## 11. Verificación (tras registrar)
1. Settings → Actions → Runners: el runner aparece **Idle** con las etiquetas `self-hosted, Linux|Windows, X64, ddd`.
2. Servicio activo: `sudo ./svc.sh status` (Linux) o `Get-Service "actions.runner.*"` (Windows).
3. Prueba mínima en una rama desechable, fuera de `.github/workflows/` de producción: un workflow `workflow_dispatch` con
   `runs-on: [self-hosted, ddd]` que ejecute `uname -a; python3 --version; df -h .` y termine. Debe quedar en verde en el
   runner propio y mostrar su nombre en el log («Runner name»).
4. Comprobar que ninguna ejecución de un repositorio público lo usa (§7.1) y que el usuario del servicio no tiene sudo.
5. Dar de alta el hecho en el tablero (`docs/ESTADO.md`) lo hace el Coordinador.
