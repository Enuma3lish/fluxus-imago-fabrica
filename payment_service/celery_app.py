"""
Celery app for Payment Service
"""
from celery import Celery
from config import get_settings
import httpx
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

# Initialize Celery
app = Celery(
    'payment_service',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Taipei',
    enable_utc=True,
)


@app.task(bind=True, max_retries=3)
def process_payment_callback(self, order_number: str, payment_data: dict):
    """
    Process payment callback asynchronously

    Args:
        order_number: Order number
        payment_data: Payment data from ECPay
    """
    try:
        # Call Django backend to process payment
        with httpx.Client() as client:
            response = client.post(
                f"{settings.backend_url}/api/orders/process-payment/",
                json={
                    "order_number": order_number,
                    "payment_data": payment_data,
                    "status": "completed"
                },
                timeout=30.0
            )
            response.raise_for_status()

        logger.info(f"Payment callback processed for order: {order_number}")
        return {"success": True, "order_number": order_number}

    except Exception as e:
        logger.error(f"Failed to process payment callback: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
