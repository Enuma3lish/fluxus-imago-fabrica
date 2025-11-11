"""
DRF Views for API endpoints
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import User, Plan, Subscription, Order, Invoice, AuditLog
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, LoginSerializer, PlanSerializer,
    SubscriptionSerializer, SubscriptionCreateSerializer,
    SubscriptionStatusSerializer, OrderSerializer, OrderCreateSerializer,
    InvoiceSerializer, AuditLogSerializer
)
from .utils import create_audit_log


class RegisterView(APIView):
    """User registration endpoint"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=UserCreateSerializer, responses={201: UserSerializer})
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            create_audit_log(
                user=user,
                action='create',
                resource_type='user',
                resource_id=str(user.id),
                description='User registered',
                request=request
            )
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """User login endpoint"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)

            create_audit_log(
                user=user,
                action='login',
                resource_type='user',
                resource_id=str(user.id),
                description='User logged in',
                request=request
            )

            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """User logout endpoint"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            create_audit_log(
                user=request.user,
                action='logout',
                resource_type='user',
                resource_id=str(request.user.id),
                description='User logged out',
                request=request
            )
            logout(request)
            return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(description='List all users (admin only)'),
    retrieve=extend_schema(description='Get user details'),
    update=extend_schema(description='Update user'),
    partial_update=extend_schema(description='Partially update user'),
    destroy=extend_schema(description='Delete user'),
)
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User CRUD operations"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'is_verified', 'is_staff']
    search_fields = ['email', 'username', 'first_name', 'last_name']

    def get_serializer_class(self):
        if self.action == 'update' or self.action == 'partial_update':
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['list', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user details"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password"""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()

            create_audit_log(
                user=request.user,
                action='update',
                resource_type='user',
                resource_id=str(request.user.id),
                description='Password changed',
                request=request
            )

            return Response({'message': 'Password changed successfully.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance):
        create_audit_log(
            user=self.request.user,
            action='delete',
            resource_type='user',
            resource_id=str(instance.id),
            description=f'User {instance.email} deleted',
            request=self.request
        )
        instance.delete()


@extend_schema_view(
    list=extend_schema(description='List all available plans'),
    retrieve=extend_schema(description='Get plan details'),
)
class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Plan (read-only)"""
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['billing_cycle', 'is_popular']
    search_fields = ['name', 'description']


@extend_schema_view(
    list=extend_schema(description='List user subscriptions'),
    retrieve=extend_schema(description='Get subscription details'),
    create=extend_schema(description='Create new subscription'),
)
class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for Subscription management"""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'auto_renew']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Subscription.objects.all()
        return Subscription.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return SubscriptionCreateSerializer
        return SubscriptionSerializer

    def perform_create(self, serializer):
        plan = Plan.objects.get(id=serializer.validated_data['plan_id'])

        # Calculate dates
        start_date = timezone.now()
        if plan.billing_cycle == 'monthly':
            end_date = start_date + timezone.timedelta(days=30)
        elif plan.billing_cycle == 'quarterly':
            end_date = start_date + timezone.timedelta(days=90)
        else:  # yearly
            end_date = start_date + timezone.timedelta(days=365)

        subscription = serializer.save(
            user=self.request.user,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            status='pending'
        )

        create_audit_log(
            user=self.request.user,
            action='subscription',
            resource_type='subscription',
            resource_id=str(subscription.id),
            description=f'Subscription created for plan {plan.name}',
            request=self.request
        )

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update subscription status"""
        subscription = self.get_object()
        serializer = SubscriptionStatusSerializer(data=request.data)

        if serializer.is_valid():
            old_status = subscription.status
            subscription.status = serializer.validated_data['status']

            if 'auto_renew' in serializer.validated_data:
                subscription.auto_renew = serializer.validated_data['auto_renew']

            if subscription.status == 'cancelled':
                subscription.cancelled_at = timezone.now()

            subscription.save()

            create_audit_log(
                user=request.user,
                action='update',
                resource_type='subscription',
                resource_id=str(subscription.id),
                description=f'Subscription status changed from {old_status} to {subscription.status}',
                request=request
            )

            return Response(SubscriptionSerializer(subscription).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(description='List user orders'),
    retrieve=extend_schema(description='Get order details'),
    create=extend_schema(description='Create new order'),
)
class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Order management"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_method']
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        order = serializer.save()

        create_audit_log(
            user=self.request.user,
            action='create',
            resource_type='order',
            resource_id=str(order.id),
            description=f'Order {order.order_number} created',
            request=self.request
        )


@extend_schema_view(
    list=extend_schema(description='List user invoices'),
    retrieve=extend_schema(description='Get invoice details'),
)
class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Invoice (read-only)"""
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Invoice.objects.all()
        return Invoice.objects.filter(user=self.request.user)


@extend_schema_view(
    list=extend_schema(description='List audit logs (admin only)'),
    retrieve=extend_schema(description='Get audit log details (admin only)'),
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AuditLog (read-only, admin only)"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action', 'resource_type']
