from django.urls import path
from .views import *
from .oauth_views import *

urlpatterns = [
    path(
        "email/activation/reset",
        ResetEmailVerification.as_view(),
        name="reset-email-activation",
    ),
    path(
        "user/<str:uuid>/<str:token>/activate",
        VerifyEmail.as_view(),
        name="activate-user",
    ),
    path("password/forgot", ForgetPassowrd.as_view(), name="forget-password"),
    path(
        "password/<str:uuid>/<str:token>/reset",
        ResetPassword.as_view(),
        name="reset-password",
    ),
    path("login", LoginView.as_view(), name="signin-user"),
    path(
        "google/login",
        LoginGoogleAPIView.as_view(),
        name="google-login",
    ),
    path(
        "google/callback",
        LoginGoogleCallbackAPIView.as_view(),
        name="google-callback",
    ),
    path(
        "twitter/login",
        LoginTwitterView.as_view(),
        name="twitter-login",
    ),
    path(
        "twitter/callback",
        LoginTwitterCallbackView.as_view(),
        name="twitter-callback",
    ),
    path(
        "github/login",
        LoginGithubAPIView.as_view(),
        name="github-login",
    ),
    path(
        "github/callback",
        LoginGithubCallbackAPIView.as_view(),
        name="github-callback",
    ),
    path("token/refresh", RefreshAccess.as_view(), name="refresh-access"),
    path("password/change", ChangePasswordView.as_view(), name="change-password"),
    path("logout", Logout.as_view(), name="logout"),
]
