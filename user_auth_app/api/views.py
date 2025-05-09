
from django.contrib.auth.models import User

from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from user_auth_app.api.serializers import ProfilRegistrationSerializer
from user_auth_app.models import Profile


class ProfileRegistrationView(generics.CreateAPIView):
    serializer_class = ProfilRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data.get("password")
        repeated_password = serializer.validated_data.get("repeated_password")
        if password != repeated_password:
            raise ValidationError({"password": "The passwords do not match!"})

        try:
            user = User.objects.create_user(
                username=serializer.validated_data["email"],
                email=serializer.validated_data["email"],
                password=password
            )

            profile = Profile.objects.create(
                user=user,
                fullname=serializer.validated_data["fullname"]
            )

            token, created = Token.objects.get_or_create(user=user)

            return Response({
                "token": token.key,
                "fullname": profile.fullname,
                "email": user.email,
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({"error": "An internal server error occured."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
