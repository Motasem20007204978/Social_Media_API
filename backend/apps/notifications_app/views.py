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
    http_method_names = ['get']

    def filter_queryset(self, queryset): 
        queryset = queryset.filter(receiver=self.request.user)
        return request
    ...

class MarkNorificationRead(PublicView, UpdateModelMixin): 
    http_method_names = ['update']

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)