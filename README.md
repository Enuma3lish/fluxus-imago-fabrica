# Fluxus Imago Fabrica

Multi-service architecture for user management, subscriptions, and payment processing.

## Architecture Overview

```
┌─────────────────┐
│   Streamlit     │  Frontend (Port 8501)
│   (Frontend)    │
└────────┬────────┘
         │
         ├─────────────────────────────────────┐
         │                                     │
         ▼                                     ▼
┌─────────────────┐                  ┌─────────────────┐
│  Django + DRF   │                  │    FastAPI      │
│  Auth & Billing │◄─────────────────┤  Payment Svc    │
│   (Port 8000)   │                  │   (Port 8001)   │
└────────┬────────┘                  └────────┬────────┘
         │                                     │
         ├──────────────┬──────────────┬──────┴────┐
         ▼              ▼              ▼           ▼
┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ PostgreSQL  │  │  Redis   │  │  Celery  │  │  ECPay   │
│  (PG_AB)    │  │  Cache   │  │  Worker  │  │   API    │
└─────────────┘  │  Broker  │  └──────────┘  └──────────┘
                 └──────────┘
```

## Services

### 1. **Backend (Django 5 + DRF)** - Port 8000
- User authentication & authorization
- User CRUD operations
- Subscription management
- Order management
- Admin panel (Django Admin)
- PostgreSQL ORM

### 2. **Payment Service (FastAPI)** - Port 8001
- ECPay payment gateway integration
- Payment webhook handling
- Async payment processing with Celery
- Invoice generation

### 3. **Frontend (Streamlit)** - Port 8501
- User authentication UI
- Subscription plans display
- Order creation & payment flow
- User dashboard
- Payment result pages

### 4. **Infrastructure**
- **PostgreSQL (PG_AB)**: Main database for Users, Orders, Subscriptions, Plans, Invoices, AuditLogs
- **PostgreSQL (PG_ADMIN)**: Read-only replica (same DB in MVP)
- **Redis**: Cache, Rate Limiting, Celery Broker & Result Backend
- **Celery**: Async task processing for payments and notifications

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
### ECpay credit card test
4311-9522-2222-2222
### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd fluxus-imago-fabrica
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start all services with Docker Compose:
```bash
docker-compose up -d
```

4. Run Django migrations:
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

5. Access services:
- Streamlit Frontend: http://localhost:8501
- Django API: http://localhost:8000
- Django Admin: http://localhost:8000/admin
- FastAPI Payment Service: http://localhost:8001
- FastAPI Docs: http://localhost:8001/docs

## Development Setup (Without Docker)

### 1. Backend (Django + DRF)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8000
```

### 2. Payment Service (FastAPI)
```bash
cd payment_service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### 3. Celery Worker
```bash
cd backend
celery -A config worker --loglevel=info
```

### 4. Frontend (Streamlit)
```bash
cd frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## API Endpoints

### Django + DRF (Backend)

#### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/refresh/` - Refresh JWT token

#### Users
- `GET /api/users/` - List users (admin only)
- `GET /api/users/{id}/` - Get user details
- `POST /api/users/` - Create user
- `PUT /api/users/{id}/` - Update user
- `DELETE /api/users/{id}/` - Delete user
- `GET /api/users/me/` - Get current user

#### Subscriptions
- `GET /api/subscriptions/` - List user subscriptions
- `POST /api/subscriptions/` - Create subscription
- `GET /api/subscriptions/{id}/` - Get subscription details
- `PATCH /api/subscriptions/{id}/status/` - Update subscription status

#### Plans
- `GET /api/plans/` - List available plans
- `GET /api/plans/{id}/` - Get plan details

#### Orders
- `GET /api/orders/` - List user orders
- `POST /api/orders/` - Create order
- `GET /api/orders/{id}/` - Get order details

### FastAPI (Payment Service)

- `POST /payment/ecpay/create/` - Create ECPay payment
- `POST /payment/ecpay/callback/` - ECPay payment callback
- `GET /payment/ecpay/return/` - ECPay return page
- `GET /payment/invoice/{order_id}/` - Get invoice

## Database Schema

### Users
- id, username, email, password, is_active, is_staff, date_joined, last_login

### Plans
- id, name, description, price, billing_cycle, features, is_active

### Subscriptions
- id, user_id, plan_id, status, start_date, end_date, auto_renew, created_at

### Orders
- id, user_id, plan_id, amount, status, payment_method, payment_id, created_at

### Invoices
- id, order_id, invoice_number, amount, issued_at, paid_at, pdf_url

### AuditLogs
- id, user_id, action, resource_type, resource_id, ip_address, timestamp

## Environment Variables

See `.env.example` for all required environment variables.

## ECPay Integration

The payment service integrates with ECPay (綠界科技) for payment processing in Taiwan:
- Credit Card
- ATM Transfer
- CVS (Convenience Store)
- Barcode Payment

### ECPay Test Environment
- Merchant ID: Test merchant ID from ECPay
- HashKey & HashIV: Provided by ECPay
- Test Card: See ECPay documentation

## Security Features

- JWT-based authentication
- Rate limiting (Redis-based)
- CORS configuration
- SQL injection protection (Django ORM)
- XSS protection
- CSRF protection
- Secure password hashing (bcrypt)
- Audit logging

## Monitoring & Logging

- Celery Flower (task monitoring): http://localhost:5555
- Django logs: `backend/logs/`
- FastAPI logs: `payment_service/logs/`
- Redis monitoring: `redis-cli MONITOR`

## Testing

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

## Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Submit a pull request

## License

MIT License
