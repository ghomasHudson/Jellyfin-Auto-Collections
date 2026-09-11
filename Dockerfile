FROM python:3.10-alpine AS base

LABEL org.opencontainers.image.source https://github.com/ghomasHudson/jellyfin-auto-collections

ENV RUNNING_IN_DOCKER true

RUN apk update
FROM base AS build

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

FROM build AS final

WORKDIR /app
RUN addgroup -S app && adduser -S -G app app \
    && mkdir -p /app/config /app/fonts \
    && chown -R app:app /app /tmp

VOLUME [ "/app/config" ]

USER app

ENTRYPOINT [ "python3.10", "-u", "main.py", "--config", "/app/config/config.yaml" ]
