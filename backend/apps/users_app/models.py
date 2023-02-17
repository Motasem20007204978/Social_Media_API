from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from .validators import username_validator, name_validator
from django.utils.translation import gettext_lazy as _
from posts_app.path_generation import PathAndRename, uuid4
from rest_framework.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import smart_bytes
from django_extensions.db.models import ModificationDateTimeField
from .user_manager import Manager
from django.contrib.auth.models import update_last_login
from django.utils.http import urlsafe_base64_decode
from rest_framework.generics import get_object_or_404

# Create your models here.


class User(AbstractUser):
    # additional features
    PROVIDERS = [
        ("email", "email"),
        ("google", "google"),
        ("twitter", "twitter"),
        ("github", "github"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    provider = models.CharField(max_length=10, choices=PROVIDERS, default="email")
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
    profile_pic = models.ImageField(
        upload_to=PathAndRename("profile_pic/"),
        blank=True,
        null=True,
        verbose_name="profile picture",
        default="default-image.jpg",
    )
    birth_date = models.DateField(null=True, blank=True)
    CHOICES = [("undefined", "-----"), ("male", "male"), ("female", "female")]
    gender = models.CharField(
        max_length=10,
        choices=CHOICES,
        default="undefined",
    )
    bio = models.TextField(
        blank=True,
        verbose_name="short description",
        null=True,
        help_text="write short description about your self",
    )
    is_active = models.BooleanField(
        _("active"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    is_online = models.BooleanField(
        _("online"),
        default=False,
        help_text=_("Designater whether user is online or not to use in websocket"),
    )
    objects = Manager()
    updated_at = ModificationDateTimeField(_("updated at"))

    USERNAME_FIELD = "email"  # for authentication
    REQUIRED_FIELDS = ("username", "first_name", "last_name")

    @property
    def full_name(self) -> str:
        return super().get_full_name()

    @property
    def followings_count(self) -> int:
        return self.followings.count()

    @property
    def followers_count(self):
        return self.followers.count()

    @property
    def blockings_count(self) -> int:
        return self.blockings.count()

    @property
    def blockers_count(self):
        return self.blockers.count()

    def check_password(self, raw_password: str) -> bool:
        if not super().check_password(raw_password):
            raise ValidationError("user password is incorrect")
        return True

    @staticmethod
    def get_user_from_uuid(uuid):
        uid = urlsafe_base64_decode(uuid).decode()
        user = get_object_or_404(User, id=uid)
        return user

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

    def check_token_validation(self, token):
        if not default_token_generator.check_token(self, token):
            raise ValidationError("token is invalid or expired")

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

    def validate_unique(self, **kwargs):
        return super().validate_unique(**kwargs)

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

    def validate_unique(self, **kwargs):
        try:
            return super().validate_unique(**kwargs)
        except:
            raise ValidationError("cannot follow the already followed user")


class Block(Common):
    from_user = ForeignUser(
        related_name="blockings",
    )
    to_user = ForeignUser(
        related_name="blockers",
    )

    @staticmethod
    def check_block_reation(source, target):
        block_list = Block.objects.filter(
            Q(from_user=source, to_user=target) | Q(from_user=target, to_user=source)
        )
        return block_list.exists()

    class Meta:
        unique_together = ["from_user", "to_user"]
        db_table = "blocking_db"

    def clean(self) -> None:
        try:
            return super().clean()
        except:
            raise ValidationError("connot block yourself")

    def validate_unique(self, **kwargs):
        try:
            return super().validate_unique(**kwargs)
        except:
            raise ValidationError("cannot block the already blocked user")
