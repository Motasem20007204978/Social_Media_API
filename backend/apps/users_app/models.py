from uuid import uuid4
from django.db import models
from django.contrib.auth.models import AbstractUser
from .validators import is_real_email, username_validator, name_validator
from django.utils.translation import gettext_lazy as _
from posts_app.models import PathAndRename
from rest_framework.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import smart_bytes
from django_extensions.db.models import ModificationDateTimeField
from .user_manager import Manager
from django.contrib.auth.models import update_last_login

# Create your models here.


class User(AbstractUser):
    # additional features
    PROVIDERS = [
        ("email", "email"),
        ("facebook", "facebook"),
        ("google", "google"),
        ("twitter", "twitter"),
        ("github", "github"),
    ]
    id = models.UUIDField(max_length=30, primary_key=True, default=uuid4)
    provider = models.CharField(
        max_length=10, choices=PROVIDERS, default=PROVIDERS[0][0]
    )
    username = models.CharField(
        unique=True,
        max_length=30,
        help_text=_("username can contain (A-Z, a-z, 0-9, _)"),
        validators=[username_validator],
    )
    email = models.EmailField(
        unique=True,
        verbose_name="email address",
    )

    first_name = models.CharField(
        _("first name"),
        max_length=30,
        validators=[name_validator],
    )
    last_name = models.CharField(
        _("last name"),
        max_length=30,
        validators=[name_validator],
    )
    is_active = models.BooleanField(
        _("active"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    objects = Manager()
    updated_at = ModificationDateTimeField(_("updated at"))

    USERNAME_FIELD = "email"  # for authentication
    REQUIRED_FIELDS = ("username", "first_name", "last_name")

    @property
    def full_name(self) -> str:
        return super().get_full_name()

    def check_password(self, raw_password: str) -> bool:
        if not super().check_password(raw_password):
            raise ValidationError("user password is incorrect")
        return True

    def check_email_activation(self):
        if not self.is_active:
            raise ValidationError(
                _(
                    "user is inactive (cannot be signed in)"
                    " please check your email and active"
                )
            )

    def generate_uuid(self):
        uidb64 = urlsafe_base64_encode(smart_bytes(self.id))
        return uidb64

    def generate_token(self):
        token = default_token_generator.make_token(self)
        return token

    def check_token(self, token):
        if not default_token_generator.check_token(self, token):
            return False
        return True

    def activate(self):
        self.is_active = True
        self.save()

    def update_login(self):
        update_last_login(None, user=self)

    class Meta(AbstractUser.Meta):
        ordering = ["-date_joined"]
        db_table = "users_db"


class ForeignUser(models.ForeignKey):
    def __init__(self, *args, **kwargs) -> None:
        kwargs["to"] = "User"
        kwargs["on_delete"] = models.CASCADE
        super().__init__(*args, **kwargs)


class Common(models.Model):
    def __str__(self):
        return f"{self.from_user} -> {self.to_user}"

    def clean(self) -> None:
        if self.from_user == self.to_user:
            raise
        return super().clean()

    def validate_unique(self, exclude):
        return super().validate_unique(exclude)

    class Meta:
        abstract = True


class Follow(Common):
    from_user = ForeignUser(
        related_name="followings",
    )
    to_user = ForeignUser(
        related_name="followers",
    )

    class Meta:
        unique_together = ["from_user", "to_user"]
        db_table = "following_db"

    def clean(self) -> None:
        try:
            return super().clean()
        except:
            raise ValidationError("connot follow yourself")

    def validate_unique(self, exclude=[]):
        try:
            return super().validate_unique(exclude)
        except:
            raise ValidationError("cannot follow the already followed user")


class Block(Common):
    from_user = ForeignUser(
        related_name="blockings",
    )
    to_user = ForeignUser(
        related_name="blockers",
    )

    class Meta:
        unique_together = ["from_user", "to_user"]
        db_table = "blocking_db"

    def clean(self) -> None:
        try:
            return super().clean()
        except:
            raise ValidationError("connot block yourself")

    def validate_unique(self, exclude=[]):
        try:
            return super().validate_unique(exclude)
        except:
            raise ValidationError("cannot block the already blocked user")


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    profile_pic = models.ImageField(
        upload_to=PathAndRename("profile_pic/"),
        blank=True,
        null=True,
        verbose_name="profile picture",
    )
    birth_date = models.DateField(null=True, blank=True)
    CHOICES = [("U", "-----"), ("M", "male"), ("F", "female")]
    gender = models.CharField(
        max_length=1,
        choices=CHOICES,
        default=CHOICES[0][0],
    )

    bio = models.TextField(
        blank=True,
        verbose_name="short description",
        null=True,
        help_text="write short description about your self",
    )

    class Meta:
        db_table = "porfiles_db"
