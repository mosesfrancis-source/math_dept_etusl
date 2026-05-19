import psycopg
from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    help = 'Create the PostgreSQL database if it does not exist'

    def handle(self, *args, **kwargs):
        s = connections['default'].settings_dict
        db_name = s['NAME']
        user = s['USER']
        password = s['PASSWORD']
        host = s['HOST']
        port = s['PORT']

        # Check if target database already exists
        for default_db in [db_name, 'railway', 'postgres']:
            try:
                conn = psycopg.connect(
                    dbname=default_db, user=user, password=password,
                    host=host, port=port, connect_timeout=10,
                )
                conn.close()
                if default_db == db_name:
                    self.stdout.write(f'Database "{db_name}" already exists.')
                    return
                # Connected to a different db — create the target db
                conn = psycopg.connect(
                    dbname=default_db, user=user, password=password,
                    host=host, port=port, autocommit=True,
                )
                with conn.cursor() as cur:
                    cur.execute(f'CREATE DATABASE "{db_name}"')
                conn.close()
                self.stdout.write(f'Database "{db_name}" created successfully.')
                return
            except psycopg.OperationalError:
                continue

        self.stderr.write(f'Could not connect to PostgreSQL to create "{db_name}".')
