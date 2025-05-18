from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.validators import validate_email

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user_auth_app.api.serializers import LoginSerializer, MemberSerializer, ProfilResponseSerializer, ProfilRegistrationSerializer
from user_auth_app.models import Profile


class ProfilRegistrationView(generics.CreateAPIView):
    """
    View for user registration.
    
    Creates a new user and associated profile when provided with valid registration data.
    Returns an authentication token and basic user information on successful registration.
    """
    serializer_class = ProfilRegistrationSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register new user",
        description="Creates a new user account with the provided information",
        tags=["User"],
        responses={
            201: ProfilResponseSerializer,
            400: OpenApiResponse(description="Invalid request data"),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            self.validate_serializer(serializer)
            user = self.create_user(serializer.validated_data)
            profile = self.create_profile(user, serializer.validated_data)

            token, created = Token.objects.get_or_create(user=user)
            response_data = self.create_response_data(token, profile, user)
            response_serializer = ProfilResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError:
            return Response({"error": "Invalid request data"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "An internal server error occurred!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def validate_serializer(self, serializer):
        """
        Validate the registration data.
        """
        if not serializer.is_valid():
            raise ValidationError()

    def create_user(self, validated_data):
        """
        Create a new user with the provided data.
        """
        try:
            created_user = User.objects.create_user(
                username=validated_data["email"],
                email=validated_data["email"],
                password=validated_data["password"]
            )
            return created_user
        except Exception:
            raise Exception()

    def create_profile(self, user, validated_data):
        """
        Create a new profile associated with the user.
        """
        try:
            new_profile = Profile.objects.create(
                user=user,
                fullname=validated_data["fullname"]
            )
            return new_profile
        except Exception:
            user.delete()
            raise Exception()

    def create_response_data(self, token, profile, user):
        """
        Create the response data structure.
        """
        return {
            "token": token.key,
            "fullname": profile.fullname,
            "email": user.email,
            "user_id": profile.id
        }


class ProfilLoginView(generics.GenericAPIView):
    """
    View for user authentication.
    
    Authenticates a user with email and password credentials and returns an authentication token.
    """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Login user",
        description="Authenticates a user with email and password and returns an authentication token",
        tags=["User"],
        responses={
            200: ProfilResponseSerializer,
            400: OpenApiResponse(description="Invalid email or password"),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = self.authenticate_user(serializer)
            if user:
                profile = Profile.objects.filter(user=user).first()
                token, created = Token.objects.get_or_create(user=user)
                response_data = self.create_response_data(token, profile, user)
                response_serializer = ProfilResponseSerializer(response_data)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            return Response({"error": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"An internal server error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def authenticate_user(self, serializer):
        """
        Authenticate a user with email and password.
        """
        return authenticate(
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"]
        )

    def create_response_data(self, token, profile, user):
        """
        Create the response data structure.
        """
        return {
            "token": token.key,
            "fullname": profile.fullname,
            "email": user.email,
            "user_id": profile.id
        }


class EmailCheckView(APIView):
    """
    View for checking if an email address is associated with a registered user.

    Returns user profile information if the email exists in the system.
    """
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Check email existence",
        description="Verify if an email address belongs to a registered user and return profile information",
        tags=["User"],
        responses={
            200: MemberSerializer,
            400: OpenApiResponse(description="Missing email or invalid email format"),
            404: OpenApiResponse(description="User not found"),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def get(self, request):
        email = request.query_params.get("email")
        if not email:
            return Response({"error": "Email address is missing"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_email(email)
        except Exception:
            return Response({"error": "Wrong email format!"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
            profile = Profile.objects.get(user=user)
            return Response(self.create_response_data(user, profile))
        except User.DoesNotExist:
            return Response({"error": "User do not exist!"}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "An internal server error occurred!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create_response_data(self, user, profile):
        """
        Create the response data structure
        """
        return {
            "id": profile.id,
            "email": user.email,
            "fullname": profile.fullname
        }
