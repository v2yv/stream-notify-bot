#!/bin/sh
set -e

mkdir -p /app/data /app/logs
chown -R botuser:botuser /app/data /app/logs

exec gosu botuser "$@"
