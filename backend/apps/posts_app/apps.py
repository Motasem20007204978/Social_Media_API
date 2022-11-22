from django.apps import AppConfig


class PostsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "posts_app"

    def ready(self):
        import posts_app.signals
