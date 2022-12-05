import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "social_media_project.settings")

app = Celery("social_media_project")
app.config_from_object("django.conf:settings", namespace="CELERY")
# namespace for preventing overlap with settings variable and config celery settings with CELERY_ prefixe
app.autodiscover_tasks()  # look for celery tasks from apps installed in settings
# automatically discovers tasks.py files in apps


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


"""
celery is a destributed tasks queue for asyncronization tasks
such as:
- sending email
- sending notifications
- resizing & editing images
- updates
- taking backups
- denormalisation
- data sync duties
- building a profile

message brokers can be used with celery:
- rabbitmq --> most used
- redis
- amazon sqs
"""

from datetime import timedelta

app.conf.beat_schedule = {
    "delete-inactivated-users": {
        "task": "delete_inactivated_users",
        "schedule": timedelta(days=1),
    },
    "delete-expired-tokens": {
        "task": "delete_expired_tokens",
        "schedule": timedelta(days=2),
    },
    "clear-read-notifications": {
        "task": "clear_read_notifications",
        "schedule": timedelta(days=2),
    },
}

# celery beat to schedule tasks with three types:
# 1- timedelta schedules in seconds
# 2- crontab schedules in specific day and time of week
# 3- solar schedules in like sunset at palestine

# how to check validators and get results before the task completes
#    wait for success status for the task
