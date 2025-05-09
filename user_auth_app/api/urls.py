

from django.urls import path

from user_auth_app.api.views import ProfilLoginView, ProfilRegistrationView


urlpatterns = [
    path('registration/', ProfilRegistrationView.as_view(), name="registration"),
    path('login/', ProfilLoginView.as_view(), name="login"),
]