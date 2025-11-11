"""
Celery tasks for async processing
"""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Subscription, Order
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_expired_subscriptions():
    """Check and update expired subscriptions"""
    now = timezone.now()
    expired_subscriptions = Subscription.objects.filter(
        status='active',
        end_date__lt=now
    )

    count = 0
    for subscription in expired_subscriptions:
        subscription.status = 'expired'
        subscription.save()
        count += 1

        # Send expiration notification
        send_subscription_expiration_email.delay(subscription.id)

    logger.info(f"Updated {count} expired subscriptions")
    return count


@shared_task
def send_subscription_expiration_email(subscription_id):
    """Send email notification for subscription expiration"""
    try:
        subscription = Subscription.objects.get(id=subscription_id)
        send_mail(
            subject='Your subscription has expired',
            message=f'Dear {subscription.user.username},\n\n'
                    f'Your subscription to {subscription.plan.name} has expired.\n'
                    f'Please renew your subscription to continue using our services.',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[subscription.user.email],
            fail_silently=False,
        )
        logger.info(f"Sent expiration email to {subscription.user.email}")
    except Exception as e:
        logger.error(f"Failed to send expiration email: {str(e)}")


@shared_task
def send_payment_confirmation_email(order_id):
    """Send email confirmation for successful payment"""
    try:
        order = Order.objects.get(id=order_id)
        send_mail(
            subject='Payment Confirmation',
            message=f'Dear {order.user.username},\n\n'
                    f'Your payment of ${order.amount} has been received successfully.\n'
                    f'Order Number: {order.order_number}\n\n'
                    f'Thank you for your purchase!',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[order.user.email],
            fail_silently=False,
        )
        logger.info(f"Sent payment confirmation to {order.user.email}")
    except Exception as e:
        logger.error(f"Failed to send payment confirmation: {str(e)}")


@shared_task
def process_payment_callback(order_id, payment_data):
    """Process payment callback from payment service"""
    try:
        order = Order.objects.get(id=order_id)
        order.status = 'completed'
        order.payment_data = payment_data
        order.paid_at = timezone.now()
        order.save()

        # Send confirmation email
        send_payment_confirmation_email.delay(str(order_id))

        logger.info(f"Processed payment for order {order.order_number}")
        return True
    except Exception as e:
        logger.error(f"Failed to process payment callback: {str(e)}")
        return False
