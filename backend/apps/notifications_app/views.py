from urllib import request
from django.shortcuts import render
from .serializers import NotificationSerialzier
from rest_framework.mixins import ListModelMixin, UpdateModelMixin
from rest_framework.generics import GenericAPIView
from .models import Notification
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)

# Create your views here.
class PublicView(GenericAPIView):
    serializer_class = NotificationSerialzier
    queryset = Notification.objects.all()


@extend_schema_view(
    get=extend_schema(
        description="get user notifications",
        operation_id="list notifications",
    ),
)
class ListNotifications(PublicView, ListModelMixin):
    def filter_queryset(self, queryset):
        queryset = queryset.filter(receiver=self.request.user)
        return request

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


@extend_schema_view(
    patch=extend_schema(
        description="mark notification as read",
        operation_id="see notification",
    ),
)
class MarkNotificationRead(PublicView, UpdateModelMixin):
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
