#!/bin/sh
set -eu

: "${MYWEBAPP_HOST:=0.0.0.0}"
: "${MYWEBAPP_PORT:=3000}"
: "${MYWEBAPP_DB_HOST:=db}"
: "${MYWEBAPP_DB_PORT:=3306}"
: "${MYWEBAPP_DB_NAME:=mywebapp}"
: "${MYWEBAPP_DB_USER:=mywebapp}"
: "${MYWEBAPP_DB_PASSWORD:=mywebapp-secret}"
: "${MYWEBAPP_DB_CONNECT_TIMEOUT:=5}"
: "${MYWEBAPP_DB_WAIT_ATTEMPTS:=30}"
: "${MYWEBAPP_DB_WAIT_INTERVAL:=2}"

attempt=1
while [ "$attempt" -le "$MYWEBAPP_DB_WAIT_ATTEMPTS" ]; do
    if python /app/scripts/migrate.py \
        --host "$MYWEBAPP_HOST" \
        --port "$MYWEBAPP_PORT" \
        --db-host "$MYWEBAPP_DB_HOST" \
        --db-port "$MYWEBAPP_DB_PORT" \
        --db-name "$MYWEBAPP_DB_NAME" \
        --db-user "$MYWEBAPP_DB_USER" \
        --db-password "$MYWEBAPP_DB_PASSWORD" \
        --db-connect-timeout "$MYWEBAPP_DB_CONNECT_TIMEOUT"; then
        break
    fi

    if [ "$attempt" -eq "$MYWEBAPP_DB_WAIT_ATTEMPTS" ]; then
        echo "Database migration failed after ${MYWEBAPP_DB_WAIT_ATTEMPTS} attempts." >&2
        exit 1
    fi

    echo "Database is not ready yet, retrying (${attempt}/${MYWEBAPP_DB_WAIT_ATTEMPTS})..." >&2
    attempt=$((attempt + 1))
    sleep "$MYWEBAPP_DB_WAIT_INTERVAL"
done

exec python -m mywebapp serve \
    --host "$MYWEBAPP_HOST" \
    --port "$MYWEBAPP_PORT" \
    --db-host "$MYWEBAPP_DB_HOST" \
    --db-port "$MYWEBAPP_DB_PORT" \
    --db-name "$MYWEBAPP_DB_NAME" \
    --db-user "$MYWEBAPP_DB_USER" \
    --db-password "$MYWEBAPP_DB_PASSWORD" \
    --db-connect-timeout "$MYWEBAPP_DB_CONNECT_TIMEOUT"
