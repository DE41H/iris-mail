from django.conf import settings

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'; "
    "form-action 'self' https://accounts.google.com"
)
PERMISSIONS = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"

class SecurityHeaders:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not settings.DEBUG:
            response.setdefault("Content-Security-Policy", CSP)
            response.setdefault("Permissions-Policy", PERMISSIONS)
        return response
