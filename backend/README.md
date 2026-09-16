# TICKBRON Backend

Django + Django REST Framework + PostgreSQL + Redis + Celery backend for TICKBRON.

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 7+

### Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Running Celery

### Worker
```bash
celery -A config worker -l info
```

### Beat (for scheduled tasks)
```bash
celery -A config beat -l info
```

## Testing

Run tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=. --cov-report=html
```

## API Documentation

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- OpenAPI Schema: http://localhost:8000/api/schema/

## Code Quality

Format code:
```bash
black .
isort .
```

Lint code:
```bash
flake8
```

## Project Structure

```
backend/
├── config/          # Django project configuration
├── manage.py       # Django management script
├── requirements.txt # Python dependencies
├── .env.example    # Environment variables template
└── README.md       # This file
```

## Security Notes

- Never commit `.env` file
- Use strong SECRET_KEY in production
- Enable DEBUG=False in production
- Configure proper CSRF and CORS settings
- Use HTTPS in production
