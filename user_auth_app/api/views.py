from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from user_auth_app.api.serializers import LoginSerializer, ProfilRegistrationSerializer
from user_auth_app.models import Profile


class ProfilRegistrationView(generics.CreateAPIView):
    serializer_class = ProfilRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = self.create_user(serializer.validated_data)
            profile = self.create_profile(user, serializer.validated_data)
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "fullname": profile.fullname,
                "email": user.email,
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"An internal server error occurred. {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create_user(self, validated_data):
        return User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"]
        )

    def create_profile(self, user, validated_data):
        return Profile.objects.create(
            user=user,
            fullname=validated_data["fullname"]
        )
    
class ProfilLoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def authenticateUser(self, serializer):
        return authenticate(
            username = serializer.validated_data["email"],
            password = serializer.validated_data["password"]
        )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = self.authenticateUser(serializer)

            if user:
                profile = Profile.objects.filter(user=user).first()
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    "token": token.key,
                    "fullname": profile.fullname,
                    "email": user.email,
                    "user_id": user.id
                }, status=status.HTTP_200_OK)
            
            return Response({
                "error": "Invalid email or password"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"error": f"An internal server error occurred. {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

