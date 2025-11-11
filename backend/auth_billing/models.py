"""
Database models for Auth & Billing
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
import uuid


class User(AbstractUser):
    """Custom User model extending Django's AbstractUser"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.username})"


class Plan(models.Model):
    """Subscription Plans"""
    BILLING_CYCLE_CHOICES = [
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('yearly', _('Yearly')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=BILLING_CYCLE_CHOICES,
        default='monthly'
    )
    features = models.JSONField(default=dict, help_text=_('Plan features as JSON'))
    max_users = models.IntegerField(default=1, help_text=_('Maximum users allowed'))
    max_storage_gb = models.IntegerField(default=10, help_text=_('Storage limit in GB'))
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plans'
        verbose_name = _('Plan')
        verbose_name_plural = _('Plans')
        ordering = ['sort_order', 'price']

    def __str__(self):
        return f"{self.name} - {self.get_billing_cycle_display()}"


class Subscription(models.Model):
    """User Subscriptions"""
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('cancelled', _('Cancelled')),
        ('expired', _('Expired')),
        ('pending', _('Pending')),
        ('trial', _('Trial')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    trial_end_date = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'end_date']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        """Check if subscription is currently active"""
        from django.utils import timezone
        return (
            self.status == 'active' and
            self.start_date <= timezone.now() <= self.end_date
        )


class Order(models.Model):
    """Orders for subscriptions and one-time purchases"""
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
        ('cancelled', _('Cancelled')),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', _('Credit Card')),
        ('atm', _('ATM Transfer')),
        ('cvs', _('Convenience Store')),
        ('barcode', _('Barcode')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='orders',
        blank=True,
        null=True
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        related_name='orders',
        blank=True,
        null=True
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='TWD')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True
    )
    payment_id = models.CharField(max_length=100, blank=True)
    payment_data = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'orders'
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['payment_id']),
        ]

    def __str__(self):
        return f"Order {self.order_number} - {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number (ECPay limit: 20 characters)
            # Format: YYMMDDHHmmss + 6-char random = 16 chars total
            from django.utils import timezone
            import random
            import string

            timestamp = timezone.now().strftime('%y%m%d%H%M%S')  # 12 chars: YYMMDDHHmmss
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))  # 6 chars
            self.order_number = f"{timestamp}{random_suffix}"  # Total: 18 chars (safe for ECPay)
        super().save(*args, **kwargs)


class Invoice(models.Model):
    """Invoices for completed orders"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='invoice'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='TWD')
    issued_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    pdf_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'invoices'
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['user', 'issued_at']),
            models.Index(fields=['invoice_number']),
        ]

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number (keeping under 20 chars for consistency)
            # Format: INV + YYMMDDHHmmss + 5-char random = 20 chars total
            from django.utils import timezone
            import random
            import string

            timestamp = timezone.now().strftime('%y%m%d%H%M%S')  # 12 chars
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))  # 5 chars
            self.invoice_number = f"INV{timestamp}{random_suffix}"  # Total: 20 chars
        super().save(*args, **kwargs)


class AuditLog(models.Model):
    """Audit logs for tracking user actions"""
    ACTION_CHOICES = [
        ('create', _('Create')),
        ('update', _('Update')),
        ('delete', _('Delete')),
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('payment', _('Payment')),
        ('subscription', _('Subscription')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        blank=True,
        null=True
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]

    def __str__(self):
        user_email = self.user.email if self.user else 'Anonymous'
        return f"{user_email} - {self.action} {self.resource_type} at {self.timestamp}"
