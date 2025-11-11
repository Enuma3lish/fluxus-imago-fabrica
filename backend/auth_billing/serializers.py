"""
DRF Serializers for API
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User, Plan, Subscription, Order, Invoice, AuditLog


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'avatar', 'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for user update"""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone', 'avatar']


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), username=email, password=password)
            if not user:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")

        attrs['user'] = user
        return attrs


class PlanSerializer(serializers.ModelSerializer):
    """Serializer for Plan model"""
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'billing_cycle',
            'features', 'max_users', 'max_storage_gb', 'is_active',
            'is_popular', 'sort_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model"""
    user = UserSerializer(read_only=True)
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'plan', 'plan_id', 'status', 'start_date',
            'end_date', 'auto_renew', 'trial_end_date', 'cancelled_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'cancelled_at']


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating subscription"""
    plan_id = serializers.UUIDField(required=True)

    class Meta:
        model = Subscription
        fields = ['plan_id', 'auto_renew']

    def validate_plan_id(self, value):
        if not Plan.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive plan.")
        return value


class SubscriptionStatusSerializer(serializers.Serializer):
    """Serializer for updating subscription status"""
    status = serializers.ChoiceField(choices=Subscription.STATUS_CHOICES)
    auto_renew = serializers.BooleanField(required=False)


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model"""
    user = UserSerializer(read_only=True)
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'plan', 'amount', 'currency',
            'status', 'payment_method', 'payment_id', 'payment_data',
            'notes', 'ip_address', 'created_at', 'updated_at', 'paid_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'user', 'created_at', 'updated_at', 'paid_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating order"""
    plan_id = serializers.UUIDField(required=True)
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES)

    class Meta:
        model = Order
        fields = ['plan_id', 'payment_method', 'notes']

    def validate_plan_id(self, value):
        if not Plan.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive plan.")
        return value

    def create(self, validated_data):
        plan_id = validated_data.pop('plan_id')
        plan = Plan.objects.get(id=plan_id)
        order = Order.objects.create(
            user=self.context['request'].user,
            plan=plan,
            amount=plan.price,
            **validated_data
        )
        return order


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model"""
    user = UserSerializer(read_only=True)
    order = OrderSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'order', 'user', 'amount',
            'tax_amount', 'total_amount', 'currency', 'issued_at',
            'paid_at', 'pdf_url', 'notes', 'metadata'
        ]
        read_only_fields = ['id', 'invoice_number', 'issued_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'action', 'resource_type', 'resource_id',
            'description', 'ip_address', 'user_agent', 'metadata', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']
