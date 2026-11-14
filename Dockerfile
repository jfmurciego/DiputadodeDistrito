# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.3.0
# NOMBRE DE VERSIÓN: Procedimiento modular con entorno GerryChain aislado y OR-Tools
# FECHA: 2026-11-14
# ESTADO: candidato
# CAMBIOS: 1.3.0 (T-297, Deslinde 1.1) — instala ortools y sus dependencias (pines de paquetes/deslinde/requirements-deslinde.lock)
#   SIN dependencias en el entorno principal, para el candidato exacto de la competición: la CI juzga lo mismo que la
#   batería y el P30 (sin ortools, el exacto daría SIN_ORTOOLS y otra huella). El resto del entorno no cambia.
# ANTERIOR: legacy/Dockerfile_v1.2.0
FROM python:3.11.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN apt-get update \
 && apt-get install --yes --no-install-recommends git jq \
 && rm -rf /var/lib/apt/lists/*
COPY requirements.lock /app/requirements.lock
COPY requirements-gerrychain-m05.lock /app/requirements-gerrychain-m05.lock
COPY paquetes/deslinde/requirements-deslinde.lock /app/requirements-deslinde.lock
RUN python -m pip install --no-cache-dir --upgrade pip==25.2 \
 && python -m pip install --no-cache-dir -r /app/requirements.lock \
 && python -m pip install --no-cache-dir pytest==8.4.2 \
 && grep -iE '^(ortools|absl-py|immutabledict|protobuf|typing_extensions)==' /app/requirements-deslinde.lock > /tmp/exacto.txt \
 && python -m pip install --no-cache-dir --no-deps -r /tmp/exacto.txt \
 && python -m venv /opt/ddd-gerrychain \
 && /opt/ddd-gerrychain/bin/python -m pip install --no-cache-dir --upgrade pip==25.2 \
 && /opt/ddd-gerrychain/bin/python -m pip install --no-cache-dir -r /app/requirements-gerrychain-m05.lock
COPY . /app
RUN chmod +x /app/procedimiento.sh
ENTRYPOINT ["/app/procedimiento.sh"]
