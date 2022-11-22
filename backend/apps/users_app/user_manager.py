from django.contrib.auth.models import UserManager


class Manager(UserManager):
    def create_superuser(self, **fields):
        fields.setdefault("is_active", True)
        user = super().create_superuser(**fields)
        return user

    def create_social_user(self, **fields):
        fields.setdefault("is_active", True)
        user = self.create_user(**fields)
        return user
