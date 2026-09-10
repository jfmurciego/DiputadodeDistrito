# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.1.0
# NOMBRE DE VERSIÓN: Procedimiento modular reproducible
# FECHA: 2026-09-11
# ESTADO: candidato
# ANTERIOR: legacy/2026-09-11_github_pre_modulos/Dockerfile
FROM python:3.11.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.lock /app/requirements.lock
RUN python -m pip install --no-cache-dir --upgrade pip==25.2 \
 && python -m pip install --no-cache-dir -r /app/requirements.lock
COPY . /app
RUN chmod +x /app/procedimiento.sh
ENTRYPOINT ["/app/procedimiento.sh"]
