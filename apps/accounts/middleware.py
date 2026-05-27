from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    EXEMPT_URLS = ["/cuentas/login/"]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and request.path not in self.EXEMPT_URLS:
            return redirect(f"{reverse('accounts:login')}?next={request.path}")
        return self.get_response(request)