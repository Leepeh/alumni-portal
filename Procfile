release: python manage.py migrate --no-input && python manage.py collectstatic --no-input
web: gunicorn alumni_portal.wsgi --log-file -
