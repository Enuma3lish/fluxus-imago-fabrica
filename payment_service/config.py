"""
Configuration for Payment Service
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # App Settings
    app_name: str = "Payment Service"
    debug: bool = True

    # ECPay Settings
    ecpay_merchant_id: str
    ecpay_hash_key: str
    ecpay_hash_iv: str
    ecpay_payment_url: str = "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"
    ecpay_query_url: str = "https://payment-stage.ecpay.com.tw/Cashier/QueryTradeInfo/V5"
    ecpay_return_url: str = "http://localhost:8501"
    ecpay_callback_url: str = "http://localhost:8001/payment/ecpay/callback"

    # Service URLs
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:8501"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
