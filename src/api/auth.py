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
