from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.validators import validate_email

from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user_auth_app.api.serializers import LoginSerializer, MemberSerializer, ProfilRegistrationSerializer
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
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"]
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


class EmailCheckView(APIView):
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        email = request.query_params.get('email')

        if not email:
            return Response({
                'error': 'Email address is missing'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_email(email)
        except Exception:
            return Response({
                'error': 'Wrong email format!'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            profile = Profile.objects.get(user=user)
            return Response({
                "id": profile.id,
                'email': user.email,
                'fullname': profile.fullname
            })
        except User.DoesNotExist:
            return Response({
                'error': 'User do not exist!'
            })
        except Profile.DoesNotExist:
            return Response({
                'error': 'Profile do not exist!'
            })
        except Exception as e:
            return Response({
                'error': 'An internal server error occurred.!'
            })
