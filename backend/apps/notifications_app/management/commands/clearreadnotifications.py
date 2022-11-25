from django.utils import timezone
from django.core.management.base import BaseCommand
from ...models import Notification


class Command(BaseCommand):
    """django command to delete notifications after one day from seeing them"""

    def handle(self, *args, **options):
        seen_notifs = Notification.objects.filter(
            modified=timezone.now() - timezone.timedelta(days=1),
            seen=True,
        )  # Queryset to get seen notifications
        seen_notifs.delete()
