#!/usr/bin/env bash
set -o errexit

python -m pip install -r requirements-production.txt
python manage.py collectstatic --noinput --settings=config.settings.production
