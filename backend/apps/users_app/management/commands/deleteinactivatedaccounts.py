from django.utils import timezone
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    """django command to delete inactivated accounts after one day form creation"""

    def handle(self, *args, **options):
        inactive_users = User.objects.filter(
            date_joined__lt=timezone.now() - timezone.timedelta(days=1), is_active=False
        )  # Queryset to get users that have created an account but didn't activate them in a day.
        inactive_users.delete()
