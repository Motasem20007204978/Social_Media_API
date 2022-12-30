from django.urls import path
from .views import *
from .social_auth_views import *

urlpatterns = [
    path("register", RegisterAPIView.as_view(), name="user-create"),
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
    path("token/refresh", RefreshAccess.as_view(), name="refresh-access"),
    path("users/list", ListUsersView.as_view(), name="search-users"),
    path(
        "user/<str:username>/information",
        ProfileView.as_view(),
        name="user-info",
    ),
    path("password/change", ChangePasswordView.as_view(), name="change-password"),
    path("following/<str:username>", FollowView.as_view(), name="following"),
    path("blocking/<str:username>", BlockView.as_view(), name="blocking"),
    path("logout", Logout.as_view(), name="logout"),
]
