#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed_skills
python manage.py seed

# Automatically create superuser if environment variables are provided
if [[ -n "${DJANGO_SUPERUSER_USERNAME}" && -n "${DJANGO_SUPERUSER_PASSWORD}" ]]; then
    python manage.py createsuperuser --noinput || true
fi
