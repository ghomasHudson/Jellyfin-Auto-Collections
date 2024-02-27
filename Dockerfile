FROM ubuntu:22.04 as base

LABEL org.opencontainers.image.source https://github.com/mzrimsek/jellyfin-auto-collections

ENV DEBIAN_FRONTEND noninteractive
ENV RUNNING_IN_DOCKER true

RUN apt-get update && apt-get install -y python3.10 wget

RUN wget -O /tmp/script.py https://bootstrap.pypa.io/get-pip.py
RUN python3.10 /tmp/script.py

RUN pip install youtube-dl

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