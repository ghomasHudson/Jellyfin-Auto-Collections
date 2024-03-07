FROM python:3.10-alpine as base

LABEL org.opencontainers.image.source https://github.com/ghomasHudson/jellyfin-auto-collections

ENV RUNNING_IN_DOCKER true

RUN apk update
RUN apk add git

RUN pip install git+https://github.com/ytdl-org/youtube-dl.git@master#egg=youtube_dl
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