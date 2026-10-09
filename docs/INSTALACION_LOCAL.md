# Instalación y operación local

**Versión:** 1.0.0  
**Fecha:** 2026-09-14  
**Estado:** candidato

## Objetivo

Ejecutar la plataforma desde un Mac con el mismo entorno fijado que CI, sin instalar Python, Conda, Miniforge ni dependencias geoespaciales en el sistema del usuario.

## Requisito único

Docker Desktop debe estar instalado y abierto. El lanzador no instala software, no descarga datos y no modifica el perfil del terminal.

## Preparación

Desde la raíz del repositorio:

```bash
chmod +x ddd-local.sh
./ddd-local.sh comprobar
./ddd-local.sh construir
```

La construcción descarga la imagen base y las dependencias fijadas en `requirements.lock`. Solo es necesaria de nuevo cuando cambien el Dockerfile o las dependencias.

## Operaciones sin cálculo territorial

Comprobar la admisión de un contrato:

```bash
./ddd-local.sh admitir aragon
```

Ejecutar la suite automática:

```bash
./ddd-local.sh probar
```

## Ejecución explícita

```bash
./ddd-local.sh ejecutar aragon M01 M08 --autorizar
```

También se puede pasar una ruta YAML relativa al repositorio. Los resultados se escriben en la ruta `io.runs.dir` declarada por el contrato.

El argumento `--autorizar` evita una ejecución accidental. El lanzador no reconstruye ni descarga fuentes automáticamente: las entradas declaradas por el contrato deben existir antes de ejecutar.

## Método de trabajo

1. Desarrollar y probar localmente.
2. Conservar resultados pesados fuera de Git cuando no sean productos canónicos.
3. Agrupar cambios relacionados en un solo paquete.
4. Hacer un único push cuando la suite local pase.
5. Usar GitHub Actions como certificación final, no como entorno de ensayo iterativo.
