from urllib import request
from .serializers import NotificationSerialzier
from rest_framework.mixins import ListModelMixin, UpdateModelMixin, RetrieveModelMixin
from rest_framework.generics import GenericAPIView
from .models import Notification
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

# Create your views here.
class PublicView(GenericAPIView):
    serializer_class = NotificationSerialzier
    queryset = Notification.objects.all()

    def check_user_permissions(self, request):
        username = request.resolver_match.kwargs.get("username")
        if request.user.username != username:
            return self.permission_denied(request)


@extend_schema_view(
    get=extend_schema(
        description="get user notifications",
        operation_id="list notifications",
        parameters=[
            OpenApiParameter(
                name="fields",
                description="select fields you want to be represented, otherwise it will return all fields",
            ),
        ],
    ),
)
class ListNotifications(PublicView, ListModelMixin):
    def filter_queryset(self, queryset):
        queryset = queryset.filter(receiver=self.request.user)
        return request

    def get(self, request, *args, **kwargs):
        self.check_user_permissions(request)
        return self.list(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        description="takes username and notification id, check them if valid, and return the notification data",
        operation_id="get notification data",
        parameters=[
            OpenApiParameter(
                name="fields",
                description="select fields you want to be represented, otherwise it will return all fields",
            ),
        ],
    ),
    patch=extend_schema(
        description="mark notification as read",
        operation_id="see notification",
        parameters=[
            OpenApiParameter(
                name="fields",
                description="select fields you want to be represented, otherwise it will return all fields",
            ),
        ],
    ),
)
class MarkNotificationRead(PublicView, UpdateModelMixin, RetrieveModelMixin):
    def check_user_permissions(self, request):
        super().check_user_permissions(request)
        notif_id = request.resolver_match.kwargs.get("notif_id")
        received_notif = Notification.objects.filter(receiver=request.user, id=notif_id)
        if not received_notif:
            return self.permission_denied(request)

    def get(self, request, **kwargs):
        self.check_user_permissions(request)
        return self.retrieve(request, **kwargs)

    def patch(self, request, *args, **kwargs):
        self.check_user_permissions(request)
        return self.partial_update(request, *args, **kwargs)
