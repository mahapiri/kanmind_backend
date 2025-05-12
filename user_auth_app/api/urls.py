

from django.urls import path

from user_auth_app.api.views import EmailCheckView, ProfilLoginView, ProfilRegistrationView


urlpatterns = [
    path('registration/', ProfilRegistrationView.as_view(), name="registration"),
    path('login/', ProfilLoginView.as_view(), name="login"),
    path('email-check/', EmailCheckView.as_view(), name="email-check"),
]