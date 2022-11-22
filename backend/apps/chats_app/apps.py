from django.apps import AppConfig


class ChatsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chats_app"

    def ready(self) -> None:
        import chats_app.signals
