

from django.urls import path

from user_auth_app.api.views import ProfilRegistrationView


urlpatterns = [
    path('registration/', ProfilRegistrationView.as_view(), name="registration")
]