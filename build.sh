#!/usr/bin/env bash
# build.sh for SQLite setup

set -o errexit  # exit on error

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Creating static directory if it doesn't exist..."
mkdir -p static

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running database migrations..."
python manage.py migrate

echo "Creating superuser if it doesn't exist..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

echo "Build completed successfully!"