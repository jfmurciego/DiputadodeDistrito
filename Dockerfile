# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.2.0
# NOMBRE DE VERSIÓN: Procedimiento modular con entorno GerryChain aislado
# FECHA: 2026-09-20
# ESTADO: candidato
# ANTERIOR: legacy/2026-09-11_github_pre_modulos/Dockerfile
FROM python:3.11.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.lock /app/requirements.lock
COPY requirements-ensemble.lock /app/requirements-ensemble.lock
RUN python -m pip install --no-cache-dir --upgrade pip==25.2 \
 && python -m pip install --no-cache-dir -r /app/requirements.lock \
 && python -m venv /opt/ddd-gerrychain \
 && /opt/ddd-gerrychain/bin/python -m pip install --no-cache-dir --upgrade pip==25.2 \
 && /opt/ddd-gerrychain/bin/python -m pip install --no-cache-dir -r /app/requirements-ensemble.lock
COPY . /app
RUN chmod +x /app/procedimiento.sh
ENTRYPOINT ["/app/procedimiento.sh"]
