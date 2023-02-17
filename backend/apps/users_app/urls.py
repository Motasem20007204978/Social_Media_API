from django.urls import path
from .views import *

urlpatterns = [
    path("register", RegisterAPIView.as_view(), name="user-create"),
    path("users/list", ListUsersView.as_view(), name="search-users"),
    path(
        "user/<str:username>/information",
        ProfileView.as_view(),
        name="user-info",
    ),
    path("following/<str:username>", FollowView.as_view(), name="following"),
    path("blocking/<str:username>", BlockView.as_view(), name="blocking"),
]
