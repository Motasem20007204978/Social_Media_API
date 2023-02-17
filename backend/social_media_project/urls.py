from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from django.conf import settings
from django.conf.urls.static import static
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
        "api/v1/",
        include(
            [
                path("posts/", include("posts_app.urls")),
                path("auth/", include("auth_app.urls")),
                path("notifications/", include("notifications_app.urls")),
                path("", include("users_app.urls")),
                path("api-auth/", include("rest_framework.urls")),
            ]
        ),
    ),
    path("api/prometheus", include("django_prometheus.urls")),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
