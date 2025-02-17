#####################
# BUILD ENVIRONMENT #
#####################

FROM caddy:2.9.1-alpine AS caddy

#####################
# FINAL ENVIRONMENT #
#####################

FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
        python3-venv python3-dev libpq-dev gcc \
        git vim procps net-tools iputils-ping cron

EXPOSE 8000
EXPOSE 8001

WORKDIR /root

COPY ./requirements.txt .

RUN python3 -m venv venv
RUN ./venv/bin/pip install -r requirements.txt

WORKDIR /root/api

COPY ./src .
COPY ./docker/entrypoint.sh /entrypoint.sh
COPY ./docker/caddy/Caddyfile /etc/Caddyfile
COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

CMD ["/bin/bash", "/entrypoint.sh"]
