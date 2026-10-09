import time

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render
from django.utils.crypto import salted_hmac
from django.utils.deprecation import MiddlewareMixin


class SubmissionThrottleMiddleware(MiddlewareMixin):
    """Bound POST attempts per endpoint and direct client IP in fixed windows.

    Forwarded IP headers are deliberately ignored. Configure limits at the edge
    when a reverse proxy hides the real client address.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method != "POST" or not request.resolver_match:
            return None
        route = request.resolver_match.view_name
        policy = settings.SUBMISSION_RATE_LIMITS.get(route)
        if not policy:
            return None
        limit, window = policy
        now = int(time.time())
        identity = salted_hmac("submission-throttle", request.META.get("REMOTE_ADDR", "unknown")).hexdigest()
        key = f"submission:{route}:{identity}:{now // window}"
        if cache.add(key, 1, timeout=window):
            attempts = 1
        else:
            try:
                attempts = cache.incr(key)
            except ValueError:
                # The entry may have expired between add() and incr().
                cache.add(key, 1, timeout=window)
                attempts = 1
        if attempts <= limit:
            return None
        retry_after = window - now % window
        response = render(request, "429.html", {"retry_after": retry_after}, status=429)
        response["Retry-After"] = str(retry_after)
        response["Cache-Control"] = "no-store"
        return response
