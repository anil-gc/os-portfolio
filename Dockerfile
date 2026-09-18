FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-production.txt ./
RUN pip install --no-cache-dir -r requirements-production.txt \
    && useradd --uid 10001 --create-home portfolio
COPY --chown=portfolio:portfolio manage.py ./
COPY --chown=portfolio:portfolio config ./config
COPY --chown=portfolio:portfolio apps ./apps
COPY --chown=portfolio:portfolio frontend/data/demo.json ./demo.json
RUN mkdir -p /app/staticfiles /app/media && chown -R portfolio:portfolio /app/staticfiles /app/media
USER portfolio
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--access-logfile", "-"]
