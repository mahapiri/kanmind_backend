from rest_framework import authentication, exceptions
from rest_framework.authtoken.models import Token


class BoardOwnerAuthentication(authentication.BaseAuthentication):
    pass
    # def authenticate(self, request):
    #     token = request.META.get("Token")
    #     if not token:
    #         return None
        
    #     try:
    #         user = Token.objects.get(key=token)
    #     except Token.DoesNotExist:
    #         raise exceptions.AuthenticationFailed('No user found!')
        
    #     return (user, None)