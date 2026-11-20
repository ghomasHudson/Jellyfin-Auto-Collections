FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source https://github.com/ghomasHudson/jellyfin-auto-collections

ENV RUNNING_IN_DOCKER=true \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app
COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends libatomic1 \
    && pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install --with-deps --only-shell chromium \
    && rm -rf /var/lib/apt/lists/*
COPY main.py .
COPY plugins/ plugins/
COPY utils/ utils/

VOLUME [ "/app/config" ]

ENTRYPOINT [ "python", "-u", "main.py", "--config", "/app/config/config.yaml" ]
