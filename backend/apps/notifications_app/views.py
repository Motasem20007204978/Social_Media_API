from urllib import request
from django.shortcuts import render
from .serializers import NotificationSerialzier
from rest_framework.mixins import ListModelMixin, UpdateModelMixin
from rest_framework.generics import GenericAPIView
from .models import Notification

# Create your views here.


class PublicView(GenericAPIView):
    serializer_class = NotificationSerialzier
    queryset = Notification.objects.all()


class ListNotifications(PublicView, ListModelMixin):
    def filter_queryset(self, queryset):
        queryset = queryset.filter(receiver=self.request.user)
        return request

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class MarkNotificationRead(PublicView, UpdateModelMixin):
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
