import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create an admin superuser if none exists'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Superuser already exists, skipping.')
            return

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@etu.edu.sl')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@ETU2024')

        user = User.objects.create_superuser(username=username, email=email, password=password)
        user.role = 'admin'
        user.first_name = 'Admin'
        user.last_name = 'ETU'
        user.save(update_fields=['role', 'first_name', 'last_name'])
        self.stdout.write(f'Superuser "{username}" created with role=admin.')
