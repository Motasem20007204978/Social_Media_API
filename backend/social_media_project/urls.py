from django.contrib import admin
from django.urls import path, include, re_path

# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
    SpectacularJSONAPIView,
)
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = [
    path("schema", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path(
        "swagger-ui/",
        SpectacularSwaggerView.as_view(),
        name="swagger-ui",
    ),
    path(
        "redoc/",
        SpectacularRedocView.as_view(),
        name="redoc",
    ),
    path("admin/", admin.site.urls),
    path(
        "api/v1/",
        include(
            [
                path("", include("users_app.urls")),
                path("posts/", include("posts_app.urls")),
                path("notifications/", include("notifications_app.urls")),
                path("api-auth/", include("rest_framework.urls")),
            ]
        ),
    ),
    path("", include("django_prometheus.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
