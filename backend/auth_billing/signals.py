"""
Django signals for automatic actions
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Order, Invoice, Subscription


@receiver(post_save, sender=Order)
def create_invoice_on_order_completion(sender, instance, created, **kwargs):
    """Automatically create invoice when order is completed"""
    if instance.status == 'completed' and instance.paid_at:
        # Check if invoice already exists
        if not hasattr(instance, 'invoice'):
            # Calculate tax (5% Taiwan business tax)
            from decimal import Decimal
            tax_amount = instance.amount * Decimal('0.05')
            total_amount = instance.amount + tax_amount

            Invoice.objects.create(
                order=instance,
                user=instance.user,
                amount=instance.amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                currency=instance.currency,
                paid_at=instance.paid_at
            )


@receiver(post_save, sender=Order)
def activate_subscription_on_payment(sender, instance, created, **kwargs):
    """Activate subscription when order is completed"""
    if instance.status == 'completed' and instance.paid_at and instance.subscription:
        subscription = instance.subscription
        if subscription.status == 'pending':
            subscription.status = 'active'
            subscription.save()
