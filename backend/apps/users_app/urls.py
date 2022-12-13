from django.urls import path
from rest_framework_simplejwt.views import token_blacklist, token_refresh

from .views import *

urlpatterns = [
    path("", ListRegisterUserView.as_view(), name="user-list-create"),
    path(
        "email/reset-activation-link/",
        ResetEmailVerification.as_view(),
        name="reset-email-activation",
    ),
    path(
        "email/activate/<str:uuid>/<str:token>/",
        VerifyEmail.as_view(),
        name="activate-email",
    ),
    path("signin", LoginView.as_view(), name="signin-user"),
    path("login-with-google", LoginWithGoogleView.as_view(), name="google-login"),
    path("refresh", token_refresh, name="refresh-access"),
    path("password/forgot", ForgetPassowrd.as_view(), name="forget-password"),
    path(
        "password/reset/<str:uuid>/<str:token>",
        ResetPassword.as_view(),
        name="reset-password",
    ),
    path("password/change", ChangePasswordView.as_view(), name="change-password"),
    path("logout", token_blacklist, name="logout"),
    path("<str:username>", ProfileView.as_view(), name="user-info"),
    path("following/<str:username>", FollowView.as_view(), name="following"),
    path("blocking/<str:username>", BlockView.as_view(), name="blocking"),
]
