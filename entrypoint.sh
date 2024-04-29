#!/bin/bash

set -e

# Wait for the database to be ready, if necessary (using wait-for-it.sh or similar)

alembic upgrade head

exec gunicorn src.entrypoints.api.app:app
