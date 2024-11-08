#!/bin/bash

set -e

export CHIA_ROOT=/data/chia/${CHIA_NETWORK:=mainnet}
export POOL_CONFIG_PATH="/data/config.yaml"
export POOL_LOG_DIR=${POOL_LOG_DIR:=/data/pool_log}

../venv/bin/python manage.py collectstatic --no-input
../venv/bin/python manage.py migrate

caddy start --config /etc/Caddyfile

exec ../venv/bin/gunicorn \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 poolenergyapi.asgi:application
