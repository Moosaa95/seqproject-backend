# Django REST Framework Backend

A professional Django REST Framework backend setup with best practices.

## Features

- Django 6.0 with Django REST Framework
- Environment-based configuration using python-decouple
- CORS headers configured for frontend integration
- PostgreSQL-ready database configuration
- Professional project structure
- Security settings for development and production
- Media and static files handling
- Comprehensive .gitignore

## Project Structure

```
backend/
├── api/                    # Main API application
│   ├── migrations/
│   ├── serializers.py     # DRF serializers
│   ├── urls.py            # API URL routing
│   └── views.py           # API views and viewsets
├── config/                 # Project configuration
│   ├── settings.py        # Django settings
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py
├── media/                  # User-uploaded files
├── static/                 # Static files
├── staticfiles/            # Collected static files
├── .env                    # Environment variables (not in git)
├── .env.example           # Example environment configuration
├── .gitignore
├── manage.py
└── requirements.txt
```

## Setup Instructions

### 1. Prerequisites

- Python 3.12+
- pip
- Virtual environment (already created at ../venv)

### 2. Install Dependencies

```bash
# Activate virtual environment
source ../venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- `SECRET_KEY`: Django secret key (generate a new one for production)
- `DEBUG`: Set to False in production
- `ALLOWED_HOSTS`: Add your domain names
- `DB_*`: Database configuration (PostgreSQL for production)
- `CORS_ALLOWED_ORIGINS`: Frontend URLs

### 4. Database Setup

For development (SQLite - default):
```bash
python manage.py migrate
```

For production (PostgreSQL):
1. Update `.env` with PostgreSQL credentials
2. Run migrations: `python manage.py migrate`

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

The API will be available at:
- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/
- Health Check: http://localhost:8000/api/health/

## API Endpoints

### Health Check
- **GET** `/api/health/` - Check API status

### Admin
- **URL** `/admin/` - Django admin interface

## Development Workflow

### Creating a New App

```bash
python manage.py startapp your_app_name
```

Then add to `INSTALLED_APPS` in `config/settings.py`.

### Creating Models

1. Define models in `your_app/models.py`
2. Create migrations: `python manage.py makemigrations`
3. Apply migrations: `python manage.py migrate`

### Creating API Endpoints

1. Create serializers in `api/serializers.py`
2. Create views/viewsets in `api/views.py`
3. Register routes in `api/urls.py`

### Example ViewSet

```python
# api/views.py
from rest_framework import viewsets
from .models import YourModel
from .serializers import YourModelSerializer

class YourModelViewSet(viewsets.ModelViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
```

```python
# api/urls.py
router.register(r'your-model', views.YourModelViewSet, basename='your-model')
```

## Production Deployment

### 1. Environment Variables

Update `.env` for production:
```
DEBUG=False
SECRET_KEY=<generate-strong-secret-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=strong_password
DB_HOST=localhost
DB_PORT=5432
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 2. Collect Static Files

```bash
python manage.py collectstatic
```

### 3. Security Checklist

```bash
python manage.py check --deploy
```

### 4. WSGI Server

Use Gunicorn or uWSGI for production:

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Django REST Framework Configuration

The project includes:
- Pagination (10 items per page)
- Search and ordering filters
- JSON and Browsable API renderers
- Session and Basic authentication (add JWT for production)
- AllowAny permissions (change to IsAuthenticated for production)

## CORS Configuration

CORS is configured for frontend integration:
- Allowed origins: localhost:3000, localhost:5173, localhost:8080
- Credentials: Enabled
- Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS

Update `CORS_ALLOWED_ORIGINS` in `.env` for production.

## Database

### Development
- SQLite (default)
- File: `db.sqlite3`

### Production
- PostgreSQL (recommended)
- Configure in `.env`

## Testing

```bash
# Run tests
python manage.py test

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## Useful Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic

# Check for issues
python manage.py check
```

## Dependencies

See `requirements.txt` for full list. Main packages:
- Django 6.0
- djangorestframework
- django-cors-headers
- python-decouple
- psycopg2-binary (PostgreSQL adapter)
- pillow (Image handling)

## License

[Your License Here]

## Contributing

[Contributing Guidelines]
