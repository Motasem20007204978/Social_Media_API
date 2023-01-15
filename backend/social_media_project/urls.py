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
    path("api/schema", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path(
        "api/swagger-ui/",
        SpectacularSwaggerView.as_view(),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(),
        name="redoc",
    ),
    path("api/admin/", admin.site.urls),
    path(
        "api/apps/",
        include(
            [
                path("posts/", include("posts_app.urls")),
                path("notifications/", include("notifications_app.urls")),
                path("", include("users_app.urls")),
                path("api-auth/", include("rest_framework.urls")),
            ]
        ),
    ),
    path("api/", include("django_prometheus.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
