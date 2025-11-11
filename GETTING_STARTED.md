# Getting Started with Fluxus Imago Fabrica

This guide will help you set up and run the Fluxus Imago Fabrica application.

## Prerequisites

Before you begin, make sure you have the following installed:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **Git**

For local development without Docker:
- **Python 3.11+**
- **PostgreSQL 15+**
- **Redis 7+**

## Quick Start with Docker (Recommended)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fluxus-imago-fabrica
```

### 2. Run Setup Script

The easiest way to get started is to run the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

This script will:
- Create a `.env` file from `.env.example`
- Create necessary directories
- Start PostgreSQL and Redis
- Run database migrations
- Create a superuser account
- Create sample subscription plans
- Start all services

### 3. Configure ECPay Credentials

Edit the `.env` file and add your ECPay credentials:

```env
ECPAY_MERCHANT_ID=your-merchant-id
ECPAY_HASH_KEY=your-hash-key
ECPAY_HASH_IV=your-hash-iv
```

For testing, you can use ECPay's test credentials. Visit [ECPay Developer Portal](https://developers.ecpay.com.tw/) to get test credentials.

### 4. Access the Application

Once the setup is complete, you can access:

- **Streamlit Frontend**: http://localhost:8501
- **Django API**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/docs/
- **FastAPI Payment Service**: http://localhost:8001
- **FastAPI Docs**: http://localhost:8001/docs
- **Celery Flower**: http://localhost:5555

## Manual Setup (Without Docker)

### 1. Set Up PostgreSQL

```bash
# Create database
createdb fluxus_db

# Or use psql
psql -U postgres
CREATE DATABASE fluxus_db;
\q
```

### 2. Set Up Redis

```bash
# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp ../.env.example ../.env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create static files
python manage.py collectstatic

# Start server
python manage.py runserver 8000
```

### 4. Payment Service Setup

In a new terminal:

```bash
cd payment_service

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start service
uvicorn main:app --reload --port 8001
```

### 5. Celery Worker Setup

In a new terminal:

```bash
cd backend
source venv/bin/activate

# Start Celery worker
celery -A config worker --loglevel=info

# In another terminal, start Celery beat
celery -A config beat --loglevel=info
```

### 6. Frontend Setup

In a new terminal:

```bash
cd frontend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Streamlit
streamlit run app.py
```

## Usage Guide

### For Users

#### 1. Register an Account

1. Open http://localhost:8501
2. Click on the "Register" tab
3. Fill in your details:
   - Username
   - Email
   - Password
4. Click "Register"

#### 2. Browse Plans

1. Log in to your account
2. Navigate to "Plans" from the sidebar
3. Browse available subscription plans
4. Click "Subscribe" on your desired plan

#### 3. Make a Payment

1. After selecting a plan, you'll be taken to the checkout page
2. Select a payment method:
   - Credit Card
   - ATM Transfer
   - Convenience Store (CVS)
   - Barcode
3. Review your order details
4. Click "Proceed to Payment"
5. You'll be redirected to ECPay to complete the payment

#### 4. View Your Subscriptions

1. Go to "Dashboard" from the sidebar
2. View your active subscriptions
3. Manage auto-renewal settings
4. Cancel subscriptions if needed

#### 5. Access Invoices

1. Navigate to "Invoices" from the sidebar
2. View all your invoices
3. Download PDF invoices (when available)

### For Administrators

#### 1. Access Admin Panel

1. Go to http://localhost:8000/admin
2. Log in with your superuser credentials

#### 2. Manage Plans

1. Click on "Plans" in the admin panel
2. Add, edit, or delete subscription plans
3. Set plan features, pricing, and billing cycles
4. Mark popular plans

#### 3. Manage Users

1. Click on "Users" in the admin panel
2. View all registered users
3. Edit user details, permissions
4. Verify user accounts

#### 4. View Orders and Subscriptions

1. Monitor all orders and their statuses
2. View subscription details
3. Handle refunds and cancellations

#### 5. Audit Logs

1. Click on "Audit Logs"
2. View all user actions
3. Track system events
4. Monitor security

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Payment service tests
cd payment_service
pytest

# Frontend tests
cd frontend
pytest
```

### Database Migrations

After making changes to models:

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### API Documentation

- Django REST API: http://localhost:8000/api/docs/
- FastAPI Payment Service: http://localhost:8001/docs

### Viewing Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f payment_service
docker-compose logs -f frontend
docker-compose logs -f celery_worker
```

### Monitoring Celery Tasks

Access Celery Flower at http://localhost:5555 to:
- Monitor task execution
- View task history
- Check worker status
- Inspect task results

## Troubleshooting

### Port Already in Use

If you get a "port already in use" error:

```bash
# Find process using the port
lsof -i :8000  # or :8001, :8501, etc.

# Kill the process
kill -9 <PID>
```

### Database Connection Error

1. Make sure PostgreSQL is running:
   ```bash
   docker-compose ps postgres
   ```

2. Check database credentials in `.env`

3. Try restarting PostgreSQL:
   ```bash
   docker-compose restart postgres
   ```

### Redis Connection Error

1. Check if Redis is running:
   ```bash
   docker-compose ps redis
   ```

2. Restart Redis:
   ```bash
   docker-compose restart redis
   ```

### Migration Errors

If you encounter migration errors:

```bash
# Reset database (WARNING: This will delete all data)
docker-compose down -v
docker-compose up -d postgres
docker-compose run --rm backend python manage.py migrate
```

### Celery Worker Not Processing Tasks

1. Check if Celery worker is running:
   ```bash
   docker-compose ps celery_worker
   ```

2. Check Celery logs:
   ```bash
   docker-compose logs celery_worker
   ```

3. Restart Celery:
   ```bash
   docker-compose restart celery_worker
   ```

## Environment Variables

Key environment variables you should configure:

### Django Settings
- `DJANGO_SECRET_KEY`: Secret key for Django (generate a new one for production)
- `DJANGO_DEBUG`: Set to `False` in production
- `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed hosts

### Database
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host (use `postgres` for Docker)
- `DB_PORT`: Database port (default: 5432)

### Redis
- `REDIS_HOST`: Redis host (use `redis` for Docker)
- `REDIS_PORT`: Redis port (default: 6379)

### ECPay
- `ECPAY_MERCHANT_ID`: Your ECPay merchant ID
- `ECPAY_HASH_KEY`: Your ECPay hash key
- `ECPAY_HASH_IV`: Your ECPay hash IV
- `ECPAY_PAYMENT_URL`: ECPay payment URL (use staging for testing)

### Service URLs
- `BACKEND_URL`: Backend API URL
- `PAYMENT_SERVICE_URL`: Payment service URL
- `FRONTEND_URL`: Frontend URL

## Production Deployment

For production deployment:

1. **Set environment variables**:
   - Change `DJANGO_DEBUG=False`
   - Set strong `DJANGO_SECRET_KEY`
   - Update `DJANGO_ALLOWED_HOSTS`
   - Use production ECPay URLs

2. **Use a reverse proxy** (Nginx):
   - Set up SSL certificates
   - Configure domain names
   - Enable HTTPS

3. **Database**:
   - Use managed PostgreSQL service
   - Set up regular backups
   - Enable connection pooling

4. **Redis**:
   - Use managed Redis service
   - Enable persistence
   - Set up password protection

5. **Monitoring**:
   - Set up application monitoring (e.g., Sentry)
   - Configure log aggregation
   - Set up alerts

6. **Security**:
   - Use secrets management (e.g., AWS Secrets Manager)
   - Enable CORS properly
   - Set up rate limiting
   - Use HTTPS everywhere

## Support

For issues or questions:
- Check the main [README.md](README.md)
- Review the API documentation
- Check Docker logs for errors
- Create an issue on GitHub

## License

MIT License
