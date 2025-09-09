from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework import authentication
from rest_framework import exceptions
from .models import Launcher


class TokenAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        auth = request.headers.get('Authorization')
        if not auth:
            return None
        if not auth.startswith('Bearer '):
            return None
        token = auth.split('Bearer ')[-1]
        launcher = Launcher.objects.filter(qrcode_token=token)
        if launcher.exists():
            return launcher[0], launcher[0]
        else:
            raise exceptions.AuthenticationFailed()


class TokenAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = TokenAuthentication
    name = 'TokenAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'Token',
        }
