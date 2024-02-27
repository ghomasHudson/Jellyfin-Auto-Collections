FROM python:3.10 as base

LABEL org.opencontainers.image.source https://github.com/mzrimsek/jellyfin-auto-collections

ENV RUNNING_IN_DOCKER true

RUN pip install youtube-dl
RUN pip install lxml

FROM base as build

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

FROM build as final

WORKDIR /app
COPY --from=build /app /app

RUN mkdir /app/config
VOLUME [ "/app/config" ]

ENTRYPOINT [ "python3.10", "main.py"]