from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import getpass

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a new user'

    def add_arguments(self, parser):
        parser.add_argument('--superuser', action='store_true', help='Create a superuser')

    def handle(self, *args, **options):
        self.stdout.write('Creating a new user...')

        # get email
        while True:
            email = input('Email: ').strip()
            if not email:
                self.stderr.write('Email cannot be empty.')
                continue
            try:
                validate_email(email)
            except ValidationError:
                self.stderr.write('Invalid email format.')
                continue
            
            if User.objects.filter(email=email).exists():
                self.stderr.write(f'User with email {email} already exists.')
                continue
            break

        # get names
        while True:
            first_name = input('First Name: ').strip()
            if not first_name:
                self.stderr.write('First name cannot be empty.')
                continue
            break

        while True:
            last_name = input('Last Name: ').strip()
            if not last_name:
                self.stderr.write('Last name cannot be empty.')
                continue
            break

        # get password
        while True:
            password = getpass.getpass('Password: ')
            if not password:
                self.stderr.write('Password cannot be empty.')
                continue
            
            if len(password) < 8:
                self.stderr.write('Password must be at least 8 characters long.')
                continue

            password_confirm = getpass.getpass('Confirm Password: ')
            if password != password_confirm:
                self.stderr.write('Passwords do not match.')
                continue
            break

        try:
            is_superuser = options['superuser']
            
            if is_superuser:
                user = User.objects.create_superuser(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                self.stdout.write(self.style.SUCCESS(f'Superuser "{email}" created successfully!'))
            else:
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True # Active by default when created via command
                )
                self.stdout.write(self.style.SUCCESS(f'User "{email}" created successfully!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating user: {e}'))
