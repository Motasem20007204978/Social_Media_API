from django.contrib import admin
from django.urls import path, include, re_path

# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path(
        "schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # path(
    #     "schema/redoc/",
    #     SpectacularRedocView.as_view(url_name="schema"),
    #     name="redoc",
    # ),
    path("admin/", admin.site.urls),
    path("users/", include("users_app.urls")),
    path("posts/", include("posts_app.urls")),
    path("chats/", include("chats_app.urls")),
    path("notifications/", include("notifications_app.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("", include("django_prometheus.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
