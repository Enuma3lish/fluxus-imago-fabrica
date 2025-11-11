"""
Custom middleware for rate limiting and other features
"""
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from .utils import get_client_ip


class RateLimitMiddleware:
    """Rate limiting middleware using Redis"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip rate limiting for admin
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # Get client identifier (IP or user ID)
        if request.user.is_authenticated:
            identifier = f"user:{request.user.id}"
        else:
            identifier = f"ip:{get_client_ip(request)}"

        # Check rate limits
        minute_key = f"rate_limit:minute:{identifier}"
        hour_key = f"rate_limit:hour:{identifier}"

        minute_count = cache.get(minute_key, 0)
        hour_count = cache.get(hour_key, 0)

        # Check if limits exceeded
        if minute_count >= settings.RATE_LIMIT_PER_MINUTE:
            return JsonResponse(
                {'error': 'Rate limit exceeded. Please try again later.'},
                status=429
            )

        if hour_count >= settings.RATE_LIMIT_PER_HOUR:
            return JsonResponse(
                {'error': 'Hourly rate limit exceeded. Please try again later.'},
                status=429
            )

        # Increment counters
        if minute_count == 0:
            cache.set(minute_key, 1, 60)  # 1 minute TTL
        else:
            cache.incr(minute_key)

        if hour_count == 0:
            cache.set(hour_key, 1, 3600)  # 1 hour TTL
        else:
            cache.incr(hour_key)

        response = self.get_response(request)
        return response
