#####################
# BUILD ENVIRONMENT #
#####################

FROM caddy:2.8.4-alpine AS caddy

#####################
# FINAL ENVIRONMENT #
#####################

FROM debian:bookworm-slim

# Identify the maintainer of an image
LABEL maintainer="contact@pool.energy"

# Define github token argument (used by pip install)
ARG GITHUB_TOKEN

# Update the image to the latest packages
RUN apt-get update && apt-get upgrade -y

# Install packages
RUN apt-get install python3-virtualenv libpq-dev git vim procps net-tools iputils-ping cron -y

EXPOSE 8000
EXPOSE 8001

WORKDIR /root

COPY ./requirements.txt /root
RUN virtualenv -p python3 venv
RUN ./venv/bin/pip install -r requirements.txt

COPY ./src /root/api
COPY ./docker/entrypoint.sh /entrypoint.sh
COPY ./docker/caddy/Caddyfile /etc/Caddyfile
COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

CMD ["bash", "/entrypoint.sh"]
