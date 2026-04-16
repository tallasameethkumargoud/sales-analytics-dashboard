import logging
import time
import uuid

logger = logging.getLogger("app")


class StructuredLoggingMiddleware:
    """
    Adds to every request:
      - request_id  → unique ID to trace across all logs
      - user_id     → who made it
      - duration_ms → how long it took
      - X-Request-ID header → returned to browser
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ─── Request Phase ─────────────────────────────────
        request.request_id = uuid.uuid4().hex[:12]
        request.start_time = time.time()

        # Safe user info (might be anonymous at this point)
        user_id = None
        username = "anonymous"
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = request.user.id
            username = request.user.username

        # Don't log static files (noisy)
        skip_paths = ("/static/", "/media/", "/favicon.ico")
        should_log = not any(request.path.startswith(p) for p in skip_paths)

        if should_log:
            logger.info(
                "request_started",
                extra={
                    "request_id": request.request_id,
                    "user_id": user_id,
                    "username": username,
                    "method": request.method,
                    "path": request.path,
                    "ip": self._get_client_ip(request),
                },
            )

        # ─── Response Phase ────────────────────────────────
        response = self.get_response(request)

        duration_ms = round((time.time() - request.start_time) * 1000, 1)

        # Re-check user (auth middleware sets it between request/response)
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = request.user.id
            username = request.user.username

        if should_log:
            log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(
                log_level,
                "request_completed",
                extra={
                    "request_id": request.request_id,
                    "user_id": user_id,
                    "username": username,
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

        # Add request_id to response header
        response["X-Request-ID"] = request.request_id
        return response

    @staticmethod
    def _get_client_ip(request):
        """Get real IP, respecting proxy headers (Railway/Nginx)."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")