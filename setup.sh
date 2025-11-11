#!/bin/bash

# Fluxus Imago Fabrica - Setup Script
# This script helps with initial setup and configuration

set -e

echo "🎨 Fluxus Imago Fabrica - Setup Script"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your configuration."
    echo ""
    read -p "Press enter to continue or Ctrl+C to exit and edit .env first..."
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🔧 Setting up services..."
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/logs
mkdir -p payment_service/logs
mkdir -p backend/media
mkdir -p backend/staticfiles

# Start Docker containers
echo ""
echo "🐳 Starting Docker containers..."
docker-compose up -d postgres redis

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Run Django migrations
echo ""
echo "🗄️  Running Django migrations..."
docker-compose run --rm backend python manage.py migrate

# Create superuser
echo ""
echo "👤 Creating Django superuser..."
echo "Please enter superuser credentials:"
docker-compose run --rm backend python manage.py createsuperuser

# Create sample plans
echo ""
echo "📦 Creating sample subscription plans..."
docker-compose run --rm backend python manage.py shell << EOF
from auth_billing.models import Plan

# Free Plan
Plan.objects.get_or_create(
    slug='free',
    defaults={
        'name': 'Free',
        'description': 'Perfect for trying out our service',
        'price': 0,
        'billing_cycle': 'monthly',
        'features': {
            'Storage': '1 GB',
            'Projects': '1 project',
            'Support': 'Community support'
        },
        'max_users': 1,
        'max_storage_gb': 1,
        'is_active': True,
        'sort_order': 1
    }
)

# Basic Plan
Plan.objects.get_or_create(
    slug='basic',
    defaults={
        'name': 'Basic',
        'description': 'Great for individuals and small teams',
        'price': 990,
        'billing_cycle': 'monthly',
        'features': {
            'Storage': '10 GB',
            'Projects': '5 projects',
            'Support': 'Email support'
        },
        'max_users': 1,
        'max_storage_gb': 10,
        'is_active': True,
        'sort_order': 2
    }
)

# Pro Plan
Plan.objects.get_or_create(
    slug='pro',
    defaults={
        'name': 'Pro',
        'description': 'Perfect for growing businesses',
        'price': 2990,
        'billing_cycle': 'monthly',
        'features': {
            'Storage': '100 GB',
            'Projects': 'Unlimited',
            'Support': 'Priority support',
            'API Access': 'Full API access'
        },
        'max_users': 5,
        'max_storage_gb': 100,
        'is_active': True,
        'is_popular': True,
        'sort_order': 3
    }
)

# Enterprise Plan
Plan.objects.get_or_create(
    slug='enterprise',
    defaults={
        'name': 'Enterprise',
        'description': 'For large organizations',
        'price': 9990,
        'billing_cycle': 'monthly',
        'features': {
            'Storage': 'Unlimited',
            'Projects': 'Unlimited',
            'Support': '24/7 dedicated support',
            'API Access': 'Full API access',
            'Custom Features': 'Yes'
        },
        'max_users': 50,
        'max_storage_gb': 1000,
        'is_active': True,
        'sort_order': 4
    }
)

print("✅ Sample plans created successfully!")
EOF

# Start all services
echo ""
echo "🚀 Starting all services..."
docker-compose up -d

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Services are now running:"
echo "   - Streamlit Frontend:  http://localhost:8501"
echo "   - Django Backend:      http://localhost:8000"
echo "   - Django Admin:        http://localhost:8000/admin"
echo "   - FastAPI Docs:        http://localhost:8001/docs"
echo "   - Payment Service:     http://localhost:8001"
echo "   - Celery Flower:       http://localhost:5555"
echo ""
echo "📝 Next steps:"
echo "   1. Edit .env file with your ECPay credentials"
echo "   2. Access the admin panel to manage plans and users"
echo "   3. Open the Streamlit frontend to test the application"
echo ""
echo "💡 Useful commands:"
echo "   - View logs: docker-compose logs -f [service_name]"
echo "   - Stop services: docker-compose down"
echo "   - Restart services: docker-compose restart"
echo ""
