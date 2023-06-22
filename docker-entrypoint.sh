#!/usr/bin/env bash

### Uvicorn common settings ###
UVICORN_PORT=${UVICORN_PORT:-"5000"}
UVICORN_SECURITY_GATEWAY_PORT=${UVICORN_SECURITY_GATEWAY_PORT:-"5001"}
UVICORN_RELOAD=${UVICORN_RELOAD:-"false"}
UVICORN_LOG_LEVEL=${UVICORN_LOG_LEVEL:-"info"}

### Celery common settings ###
CELERY_LOG_LEVEL=${CELERY_LOG_LEVEL:-"info"}
CELERY_MIN_WORKERS=${CELERY_MIN_WORKERS:-"1"}
CELERY_MAX_WORKERS=${CELERY_MAX_WORKERS:-"2"}

if [ $UVICORN_RELOAD == "true" ]; then
  UVICORN_START_ARGS="${UVICORN_START_ARGS} --reload"
else
  ### Not valid with --reload
  export UVICORN_WORKERS=${UVICORN_WORKERS:-"1"}
fi

function export_overriden_env() {
  # Override env variables with .env.override file
  # It will allow to have different env variables for local development and production
  FILE=".env.override"
  if [[ -f "$FILE" ]]; then
    export $(grep -v '^#' $FILE | xargs -d '\n')
  else
    echo "Override env $FILE not found"
  fi
}

function run_migrations() {
  echo "Running migration"
  alembic -c /opt/app/secbot/alembic.ini upgrade head
}

function run_app() {
  echo "Starting security bot app"
  export_overriden_env
  run_migrations
  uvicorn app.main:app --host 0.0.0.0 --port ${UVICORN_PORT} --log-level ${UVICORN_LOG_LEVEL} ${UVICORN_START_ARGS}
}

function run_security_gateway() {
  echo "Starting security bot security gateway"
  export_overriden_env
  uvicorn app.main:security_gateway_app --host 0.0.0.0 --port ${UVICORN_SECURITY_GATEWAY_PORT} --log-level ${UVICORN_LOG_LEVEL} ${UVICORN_START_ARGS}
}

function run_celery() {
  echo "Starting security bot celery worker"
  export_overriden_env
  celery -A app.main:celery_app worker --autoscale=${CELERY_MAX_WORKERS},${CELERY_MIN_WORKERS} --loglevel ${CELERY_LOG_LEVEL}
}

case $1 in
  "shell")
    bash
  ;;
  "start_app")
    run_app
  ;;
  "start_security_gateway")
    run_security_gateway
  ;;
  "start_celery")
    run_celery
  ;;
  "migrate")
    run_migrations
  ;;
  *)
    echo "Please use of next parameters to start:"
    echo "  help:      help information"
    echo "  shell:     run shell"
    echo "  migrate:   run migrations"
    echo "  start_app:     run app"
    echo "  start_celery:     run celery"
  ;;
esac
