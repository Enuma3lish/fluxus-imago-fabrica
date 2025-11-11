"""
Utility functions
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from .models import AuditLog


def custom_exception_handler(exc, context):
    """Custom exception handler for DRF"""
    response = exception_handler(exc, context)

    if response is not None:
        response.data['status_code'] = response.status_code

    return response


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_audit_log(user, action, resource_type, resource_id, description='', request=None, metadata=None):
    """Create audit log entry"""
    audit_data = {
        'user': user,
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'description': description,
        'metadata': metadata or {},
    }

    if request:
        audit_data['ip_address'] = get_client_ip(request)
        audit_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')

    return AuditLog.objects.create(**audit_data)
