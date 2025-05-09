from django.contrib import admin
from rest_framework.authtoken.models import Token

from user_auth_app.models import Profile

# Register your models here.
admin.site.register(Profile)