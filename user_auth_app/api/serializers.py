from django.contrib.auth.models import User
from rest_framework import serializers

from board_app.models import Profile


class ProfilRegistrationSerializer(serializers.Serializer):
    fullname = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True, min_length=8)
    repeated_password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email address already exist!")
        return value
    
    def validate(self, data):
        if data.get("password") != data.get("repeated_password"):
            raise serializers.ValidationError({"passwords": "The passwords do not match!"})
        data.pop("repeated_password")
        return data
    

class ProfilResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    fullname = serializers.CharField()
    email = serializers.EmailField()
    user_id = serializers.IntegerField()
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True, min_length=8)


class MemberSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()

    class Meta: 
        model = Profile
        fields = ["id", "email", "fullname"]

    def get_email(self, obj):
        if obj.user:
            return obj.user.email
        return None
