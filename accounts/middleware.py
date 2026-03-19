import logging


from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log requests and annotate API responses.


    This middleware is run for every request (after Django's built-in
    AuthenticationMiddleware). It is designed to:


    - Log the incoming request method and path for debugging / auditing.
    - Add a consistent header to API responses (e.g. X-Request-ID) when provided.


    This is a lightweight example of a "REST API middleware" layer that sits
    between the HTTP request and view execution.
    """

    def process_request(self, request):
        # Log a short summary of every incoming request.
        logger.debug(
            "Incoming request: %s %s from %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
        )

        # If the request contains a request ID header, store it on the request for later use.
        request.request_id = request.META.get("HTTP_X_REQUEST_ID")

        # Returning None continues normal processing; returning a response would short-circuit.
        return None

    def process_response(self, request, response):
        # Echo back the request ID in the response headers when present.
        if hasattr(request, "request_id") and request.request_id:
            response["X-Request-ID"] = request.request_id
        return response
