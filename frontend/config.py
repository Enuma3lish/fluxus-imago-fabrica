"""
Configuration for Streamlit Frontend
"""
import os
from decouple import config

# API URLs
BACKEND_URL = config('BACKEND_URL', default='http://localhost:8000')
PAYMENT_SERVICE_URL = config('PAYMENT_SERVICE_URL', default='http://localhost:8001')

# API Endpoints
API_AUTH_REGISTER = f"{BACKEND_URL}/api/auth/register/"
API_AUTH_LOGIN = f"{BACKEND_URL}/api/auth/login/"
API_AUTH_LOGOUT = f"{BACKEND_URL}/api/auth/logout/"
API_AUTH_REFRESH = f"{BACKEND_URL}/api/auth/refresh/"

API_USERS_ME = f"{BACKEND_URL}/api/users/me/"
API_PLANS = f"{BACKEND_URL}/api/plans/"
API_SUBSCRIPTIONS = f"{BACKEND_URL}/api/subscriptions/"
API_ORDERS = f"{BACKEND_URL}/api/orders/"
API_INVOICES = f"{BACKEND_URL}/api/invoices/"

API_PAYMENT_CREATE = f"{PAYMENT_SERVICE_URL}/payment/ecpay/create/"
API_PAYMENT_INVOICE = f"{PAYMENT_SERVICE_URL}/payment/invoice/"

# Session keys
SESSION_USER = 'user'
SESSION_ACCESS_TOKEN = 'access_token'
SESSION_REFRESH_TOKEN = 'refresh_token'

# Page config
PAGE_TITLE = "Fluxus Imago Fabrica"
PAGE_ICON = "🎨"
LAYOUT = "wide"
