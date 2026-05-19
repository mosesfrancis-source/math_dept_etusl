web: gunicorn etu_project.wsgi --log-file -
release: python manage.py migrate --noinput && python manage.py ensure_superuser
