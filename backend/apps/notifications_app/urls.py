from django.urls import path
from .views import ListNotifications, MarkNotificationRead

urlpatterns = [
    path("<str:username>", ListNotifications.as_view(), name="get_notifications"),
    path(
        "<str:username>/<str:notif_id>",
        MarkNotificationRead.as_view(),
        name="mark_notification_as_read",
    ),
]
