# Architecture Documentation

## System Overview

Fluxus Imago Fabrica is a multi-service microservices architecture designed for user management, subscription billing, and payment processing with ECPay integration.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            CLIENT LAYER                                  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    Streamlit Frontend                           │    │
│  │                    (Port 8501)                                  │    │
│  │  - User Authentication UI                                       │    │
│  │  - Dashboard & Metrics                                          │    │
│  │  - Plan Selection & Checkout                                    │    │
│  │  - Order & Invoice Management                                   │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                              │                                           │
└──────────────────────────────┼───────────────────────────────────────────┘
                               │
                               │ HTTP/REST
                               │
┌──────────────────────────────┼───────────────────────────────────────────┐
│                     APPLICATION LAYER                                    │
│                              │                                           │
│              ┌───────────────┴────────────────┐                         │
│              │                                 │                         │
│              ▼                                 ▼                         │
│  ┌──────────────────────┐         ┌──────────────────────┐             │
│  │  Django + DRF        │◄────────┤  FastAPI Payment     │             │
│  │  (Port 8000)         │         │  Service (Port 8001) │             │
│  │                      │         │                      │             │
│  │ - JWT Auth           │         │ - ECPay Integration  │             │
│  │ - User CRUD          │         │ - Payment Processing │             │
│  │ - Subscription Mgmt  │         │ - Callback Handling  │             │
│  │ - Order Management   │         │ - Invoice API        │             │
│  │ - Admin Panel        │         │                      │             │
│  └──────────────────────┘         └──────────────────────┘             │
│              │                                 │                         │
└──────────────┼─────────────────────────────────┼─────────────────────────┘
               │                                 │
               │                                 │
┌──────────────┼─────────────────────────────────┼─────────────────────────┐
│       TASK PROCESSING LAYER                    │                         │
│              │                                 │                         │
│              ▼                                 ▼                         │
│  ┌──────────────────────┐         ┌──────────────────────┐             │
│  │  Celery Worker       │         │  Celery Beat         │             │
│  │                      │         │  (Scheduler)         │             │
│  │ - Payment Processing │         │                      │             │
│  │ - Email Notifications│         │ - Subscription Checks│             │
│  │ - Invoice Generation │         │ - Scheduled Tasks    │             │
│  └──────────────────────┘         └──────────────────────┘             │
│              │                                 │                         │
│              │                                 │                         │
│              └────────────┬────────────────────┘                         │
└───────────────────────────┼──────────────────────────────────────────────┘
                            │
                            │
┌───────────────────────────┼──────────────────────────────────────────────┐
│                    DATA LAYER                                            │
│                           │                                              │
│              ┌────────────┴──────────────┐                               │
│              │                           │                               │
│              ▼                           ▼                               │
│  ┌──────────────────────┐   ┌──────────────────────┐                   │
│  │  PostgreSQL 15       │   │  Redis 7             │                   │
│  │  (Port 5432)         │   │  (Port 6379)         │                   │
│  │                      │   │                      │                   │
│  │ - Users              │   │ - Cache              │                   │
│  │ - Plans              │   │ - Rate Limiting      │                   │
│  │ - Subscriptions      │   │ - Celery Broker      │                   │
│  │ - Orders             │   │ - Session Storage    │                   │
│  │ - Invoices           │   │                      │                   │
│  │ - Audit Logs         │   │                      │                   │
│  └──────────────────────┘   └──────────────────────┘                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                                     │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                         ECPay API                               │    │
│  │              (Payment Gateway - Taiwan)                         │    │
│  │                                                                 │    │
│  │  - Credit Card Processing                                       │    │
│  │  - ATM Transfer                                                 │    │
│  │  - CVS Payment                                                  │    │
│  │  - Barcode Payment                                              │    │
│  └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Frontend
- **Streamlit 1.30.0**: Python-based web framework for rapid UI development
- **streamlit-option-menu**: Enhanced navigation menu
- **requests**: HTTP client for API communication

### Backend (Django)
- **Django 5.0.1**: Web framework
- **Django REST Framework 3.14.0**: RESTful API framework
- **djangorestframework-simplejwt 5.3.1**: JWT authentication
- **django-cors-headers 4.3.1**: CORS handling
- **django-filter 23.5**: Advanced filtering
- **drf-spectacular 0.27.0**: OpenAPI documentation
- **psycopg2-binary 2.9.9**: PostgreSQL adapter
- **gunicorn 21.2.0**: WSGI HTTP server

### Payment Service (FastAPI)
- **FastAPI 0.109.0**: Modern async web framework
- **uvicorn 0.27.0**: ASGI server
- **pydantic 2.5.3**: Data validation
- **httpx 0.26.0**: Async HTTP client

### Task Queue
- **Celery 5.3.6**: Distributed task queue
- **Redis 5.0.1**: Message broker and cache
- **django-celery-beat 2.5.0**: Periodic task scheduler
- **django-celery-results 2.5.1**: Result backend

### Database
- **PostgreSQL 15**: Primary database
- **Redis 7**: Cache and message broker

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration

## Data Flow

### User Registration Flow

```
1. User fills registration form (Streamlit)
   ↓
2. POST /api/auth/register/ (Django)
   ↓
3. Create User in PostgreSQL
   ↓
4. Create Audit Log entry
   ↓
5. Return success response
   ↓
6. Display success message (Streamlit)
```

### Login Flow

```
1. User enters credentials (Streamlit)
   ↓
2. POST /api/auth/login/ (Django)
   ↓
3. Authenticate user
   ↓
4. Generate JWT tokens (access + refresh)
   ↓
5. Create Audit Log entry
   ↓
6. Return tokens + user data
   ↓
7. Store tokens in session (Streamlit)
   ↓
8. Redirect to dashboard
```

### Subscription Creation & Payment Flow

```
1. User selects plan (Streamlit)
   ↓
2. POST /api/subscriptions/ (Django)
   ↓
3. Create Subscription (status: pending)
   ↓
4. POST /api/orders/ (Django)
   ↓
5. Create Order with subscription reference
   ↓
6. POST /payment/ecpay/create/ (FastAPI)
   ↓
7. Generate ECPay payment form
   │  - Create CheckMacValue
   │  - Prepare payment parameters
   ↓
8. Return payment form data
   ↓
9. Submit form to ECPay (Client-side)
   ↓
10. User completes payment on ECPay
   ↓
11. ECPay callback: POST /payment/ecpay/callback/ (FastAPI)
   ↓
12. Verify CheckMacValue
   ↓
13. Queue Celery task: process_payment_callback
   ↓
14. Celery Worker processes payment
   │  - Update Order status to 'completed'
   │  - Update Order.paid_at timestamp
   │  - Update payment_data
   ↓
15. Django Signal: create_invoice_on_order_completion
   │  - Create Invoice with tax calculation
   ↓
16. Django Signal: activate_subscription_on_payment
   │  - Update Subscription status to 'active'
   ↓
17. Queue email notification task
   ↓
18. Send payment confirmation email
   ↓
19. User receives confirmation
```

### Rate Limiting Flow

```
1. Request arrives at Django
   ↓
2. RateLimitMiddleware intercepts
   ↓
3. Check Redis for rate limit counters
   │  - Key: rate_limit:minute:{user_id|ip}
   │  - Key: rate_limit:hour:{user_id|ip}
   ↓
4. If limit exceeded:
   │  → Return 429 (Too Many Requests)
   │
5. If within limit:
   │  - Increment counters
   │  - Continue to view
```

## Database Schema

### User Model
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    phone VARCHAR(20),
    avatar VARCHAR(100),
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    date_joined TIMESTAMP
);
```

### Plan Model
```sql
CREATE TABLE plans (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    billing_cycle VARCHAR(20) NOT NULL, -- monthly, quarterly, yearly
    features JSONB,
    max_users INTEGER DEFAULT 1,
    max_storage_gb INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT TRUE,
    is_popular BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Subscription Model
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    plan_id UUID NOT NULL REFERENCES plans(id),
    status VARCHAR(20) NOT NULL, -- active, cancelled, expired, pending, trial
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    auto_renew BOOLEAN DEFAULT TRUE,
    trial_end_date TIMESTAMP,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_status (user_id, status),
    INDEX idx_status_end_date (status, end_date)
);
```

### Order Model
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    plan_id UUID REFERENCES plans(id),
    subscription_id UUID REFERENCES subscriptions(id),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'TWD',
    status VARCHAR(20) NOT NULL, -- pending, processing, completed, failed, refunded, cancelled
    payment_method VARCHAR(20), -- credit_card, atm, cvs, barcode
    payment_id VARCHAR(100),
    payment_data JSONB,
    notes TEXT,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    INDEX idx_user_status (user_id, status),
    INDEX idx_order_number (order_number),
    INDEX idx_payment_id (payment_id)
);
```

### Invoice Model
```sql
CREATE TABLE invoices (
    id UUID PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    order_id UUID UNIQUE NOT NULL REFERENCES orders(id),
    user_id UUID NOT NULL REFERENCES users(id),
    amount DECIMAL(10, 2) NOT NULL,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'TWD',
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    pdf_url VARCHAR(200),
    notes TEXT,
    metadata JSONB,
    INDEX idx_user_issued (user_id, issued_at),
    INDEX idx_invoice_number (invoice_number)
);
```

### AuditLog Model
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(20) NOT NULL, -- create, update, delete, login, logout, payment, subscription
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    description TEXT,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_timestamp (user_id, timestamp),
    INDEX idx_action_timestamp (action, timestamp),
    INDEX idx_resource (resource_type, resource_id)
);
```

## API Endpoints

### Authentication Endpoints

```
POST   /api/auth/register/        Register new user
POST   /api/auth/login/           User login (returns JWT tokens)
POST   /api/auth/logout/          User logout
POST   /api/auth/refresh/         Refresh JWT token
```

### User Endpoints

```
GET    /api/users/                List users (admin only)
POST   /api/users/                Create user (admin only)
GET    /api/users/{id}/           Get user details
PUT    /api/users/{id}/           Update user
PATCH  /api/users/{id}/           Partial update user
DELETE /api/users/{id}/           Delete user (admin only)
GET    /api/users/me/             Get current user
POST   /api/users/change_password/ Change password
```

### Plan Endpoints

```
GET    /api/plans/                List all active plans
GET    /api/plans/{id}/           Get plan details
```

### Subscription Endpoints

```
GET    /api/subscriptions/        List user subscriptions
POST   /api/subscriptions/        Create subscription
GET    /api/subscriptions/{id}/   Get subscription details
PATCH  /api/subscriptions/{id}/update_status/  Update subscription status
```

### Order Endpoints

```
GET    /api/orders/               List user orders
POST   /api/orders/               Create order
GET    /api/orders/{id}/          Get order details
```

### Invoice Endpoints

```
GET    /api/invoices/             List user invoices
GET    /api/invoices/{id}/        Get invoice details
```

### Payment Service Endpoints

```
POST   /payment/ecpay/create/     Create ECPay payment
POST   /payment/ecpay/callback/   ECPay payment callback (webhook)
GET    /payment/ecpay/return/     ECPay return URL
GET    /payment/invoice/{order_id}/ Get invoice by order ID
POST   /payment/test/             Test payment (dev only)
```

## Security Features

### Authentication & Authorization
- JWT-based authentication with access and refresh tokens
- Token expiration and rotation
- Password hashing with bcrypt
- CSRF protection
- User role-based permissions

### Rate Limiting
- Per-minute limit: 60 requests
- Per-hour limit: 1000 requests
- IP-based for anonymous users
- User-based for authenticated users
- Redis-backed counters

### Data Protection
- SQL injection prevention (ORM)
- XSS protection
- CORS configuration
- Secure password validation
- Payment data encryption

### Audit Trail
- All user actions logged
- IP address tracking
- User agent logging
- Timestamp tracking
- Resource change tracking

## Monitoring & Logging

### Application Logs
- Django logs: `backend/logs/django.log`
- FastAPI logs: `payment_service/logs/payment_service.log`
- Celery logs: Docker logs

### Celery Monitoring
- Celery Flower: http://localhost:5555
- Real-time task monitoring
- Worker status
- Task history
- Performance metrics

### Database Monitoring
- PostgreSQL logs
- Query performance
- Connection pooling
- Index usage

### Redis Monitoring
- Redis CLI: `redis-cli MONITOR`
- Memory usage
- Key expiration
- Cache hit rate

## Deployment Considerations

### Environment Variables
All sensitive configuration in environment variables:
- Database credentials
- Redis configuration
- ECPay API keys
- JWT secrets
- Email settings

### Scaling
- Horizontal scaling of web services
- Multiple Celery workers
- Database read replicas
- Redis Sentinel for high availability

### Backup Strategy
- PostgreSQL daily backups
- Redis persistence
- Static/media file backups
- Database migration history

### Security Best Practices
- HTTPS everywhere in production
- Secret management (AWS Secrets Manager, etc.)
- Regular dependency updates
- Security headers
- Rate limiting
- DDoS protection

## Development Workflow

### Local Development
1. Copy `.env.example` to `.env`
2. Configure database and Redis
3. Run migrations
4. Create superuser
5. Start development servers

### Testing
- Unit tests for models and views
- Integration tests for API endpoints
- Payment flow testing with test credentials
- Load testing with locust

### CI/CD
- Automated testing on PR
- Docker image building
- Deployment to staging
- Production deployment

## Future Enhancements

### Planned Features
- [ ] WebSocket support for real-time notifications
- [ ] Multi-currency support
- [ ] Refund management
- [ ] Proration for plan changes
- [ ] Usage-based billing
- [ ] Analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Webhook support for third-party integrations
- [ ] Advanced reporting
- [ ] Data export functionality

### Performance Optimizations
- [ ] Database query optimization
- [ ] Redis caching strategy
- [ ] CDN integration
- [ ] Image optimization
- [ ] API response compression
- [ ] Database connection pooling

### Infrastructure Improvements
- [ ] Kubernetes deployment
- [ ] Auto-scaling configuration
- [ ] Multi-region deployment
- [ ] Disaster recovery plan
- [ ] Load balancer configuration
