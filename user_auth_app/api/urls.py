

from django.urls import path

from user_auth_app.api.views import ProfileRegistrationView


urlpatterns = [
    path('registration/', ProfileRegistrationView.as_view(), name="registration")
]