from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Follow, Profile, User, Block
from .utils import get_user_from_uuid
from drf_spectacular.utils import (
    extend_schema_serializer,
    OpenApiExample,
)
from drf_base64.fields import Base64ImageField
from drf_writable_nested.serializers import WritableNestedModelSerializer
from drf_queryfields.mixins import QueryFieldsMixin
from .utils import check_block_relation
from rest_framework_simplejwt.settings import api_settings


def repr_data(value):
    data = {
        "id": value.id,
        "username": value.username,
        "name": value.full_name,
    }
    return data


OBJECT = {"id": "string", "username": "string", "name": "string"}


class RelatedFollowers(serializers.RelatedField):
    def to_representation(self, value):
        return repr_data(value.from_user)


class RelatedFollowings(RelatedFollowers):
    def to_representation(self, value):
        return repr_data(value.to_user)


class RelatedBlockers(RelatedFollowers):
    ...


class RelatedBlockings(RelatedFollowings):
    ...


class NestedProfileSerializer(serializers.ModelSerializer):

    profile_pic = Base64ImageField()

    class Meta:
        model = Profile
        exclude = ("user",)


fields_representation = {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "username": "stirng",
    "email": "user@example.com",
    "first_name": "string",
    "last_name": "string",
    "profile": {
        "profile_pic": "example.com/media/profile_pictires/pic.jpg",
        "birth_date": "2000-03-23",
        "gender": "male",
        "bio": "string",
    },
    "followers_count": 44,
    "followers": [OBJECT],
    "followings_count": 22,
    "followings": [OBJECT],
    "blockers_count": 12,
    "blockers": [OBJECT],
    "blockings_count": 10,
    "blockings": [OBJECT],
    "date_joined": "2022-12-12T12:18:43.499990Z",
    "updated_at": "2022-12-12T12:18:43.776489Z",
}


@extend_schema_serializer(
    exclude_fields=[*fields_representation.keys()],
    examples=[
        OpenApiExample(
            name="profile data",
            value=fields_representation,
            response_only=True,
            status_codes=[200],
        )
    ],
)
class ProfileSerializer(QueryFieldsMixin, WritableNestedModelSerializer):

    followers = RelatedFollowers(many=True, read_only=True)
    followings = RelatedFollowings(many=True, read_only=True)
    profile = NestedProfileSerializer()
    blockers = RelatedBlockers(many=True, read_only=True)
    blockings = RelatedBlockings(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "profile",
            "followers_count",
            "followers",
            "followings_count",
            "followings",
            "blockers_count",
            "blockers",
            "blockings_count",
            "blockings",
            "date_joined",
            "updated_at",
        )
        read_only_fields = (
            "username",
            "email",
            "full_name",
            "date_joined",
            "updated_at",
        )

        extra_kwargs = {
            "first_name": {"write_only": True, "required": False},
            "last_name": {"write_only": True, "required": False},
        }


class PasswordField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs["write_only"] = True
        kwargs["max_length"] = 150
        kwargs["style"] = {"input_type": "password"}
        kwargs["trim_whitespace"] = False
        super().__init__(**kwargs)


class RegisterSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    password = PasswordField()

    again_pass = PasswordField(label="Again password")

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "full_name",
            "date_joined",
            "again_pass",
        ]
        read_only_fields = ["full_name", "date_joined"]
        extra_kwargs = {
            "first_name": {"write_only": True, "min_length": 5},
            "last_name": {"write_only": True, "min_length": 5},
            "again_pass": {"write_only": True},
        }

    def create(self, validated_data):
        # user model catch again_pass value, although it has not again_pass field
        validated_data.pop("again_pass")

        # for hashing password
        password = validated_data.pop("password")
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user

    def validate(self, attrs):
        if attrs["password"] == attrs["again_pass"]:
            return super().validate(attrs)
        raise serializers.ValidationError("passwords are not be the same")


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(label="email", write_only=True)

    def create(self, validated_data):
        return validated_data


class ResetPasswordSerializer(serializers.Serializer):
    password = PasswordField(label="new password")
    pass_again = PasswordField(label="password again")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = validated_data.pop("user")
        user.set_password(password)
        user.update_login()
        user.save()
        return user

    def validate(self, attrs):
        if attrs["password"] != attrs["pass_again"]:
            raise serializers.ValidationError("passowrds must be same")
        request = self.context["request"]
        user = get_user_from_uuid(request.resolver_match.kwargs["uuid"])
        user.check_email_activation()
        attrs["user"] = user
        return attrs


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="success login",
            value={
                "refresh": "string",
                "access": "string",
                "refresh_token_timeout": 20000,
                "access_token_timeout": 3600,
                "user": {
                    "username": "string",
                    "name": "string",
                    "email": "string",
                },
            },
            response_only=True,
            status_codes=[200],
        )
    ],
)
class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["refresh_token_timeout"] = api_settings.REFRESH_TOKEN_LIFETIME
        data["access_token_timeout"] = api_settings.ACCESS_TOKEN_LIFETIME
        data["user"] = {
            "username": self.user.username,
            "name": self.user.full_name,
            "email": self.user.email,
        }
        return data


from .google_auth import google_login_data
from django.utils.crypto import get_random_string
from decouple import config


class GoogleLoginSerializer(serializers.Serializer):
    def login(self, data):
        serializer = LoginSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def to_representation(self, instance):
        data = {
            "email": instance.email,
            "password": config("LOGIN_WITH_SOCIAL_MEDIA_PASS"),
        }
        return self.login(data)

    def create(self, validated_data):
        user = User.objects.filter(email=validated_data["email"])
        if user:
            return user[0]

        data = {
            "provider": "google",
            "username": get_random_string(20),
            "email": validated_data["email"],
            "first_name": validated_data["given_name"],
            "last_name": validated_data["family_name"],
            "password": config("LOGIN_WITH_SOCIAL_MEDIA_PASS"),
        }
        user = User.objects.create_social_user(**data)
        return user

    def validate(self, attrs):
        data = google_login_data()
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = PasswordField(label="old password")
    new_password = PasswordField(label="new passowrd")

    def create(self, validated_data):
        new_pass = validated_data.get("new_password", "")
        request = self.context.get("request", "")
        request.user.set_password(new_pass)
        request.user.save()
        return request.user

    def validate(self, data):
        request = self.context.get("request", "")
        old_pass = data.get("old_password", "")
        request.user.check_password(old_pass)
        request.user.check_email_activation()
        return data


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="respone data",
            value={
                "from_user": {"username": "string", "full_name": "string"},
                "to_user": {"username": "string", "full_name": "string"},
            },
        )
    ]
)
class FollowSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = {
            "from_user": {
                "username": instance.from_user.username,
                "full_name": instance.from_user.full_name,
            },
            "to_user": {
                "username": instance.to_user.username,
                "full_name": instance.to_user.full_name,
            },
        }
        return data

    class Meta:
        model = Follow
        fields = ("from_user", "to_user")
        read_only_fields = ("from_user", "to_user")

    def create(self, validated_data):
        print(validated_data)
        to_user = User.objects.get(username=validated_data.pop("username"))
        validated_data["to_user"] = to_user
        return super().create(validated_data)

    def validate(self, attrs):
        request = self.context.get("request")
        sender = request.user
        attrs["from_user"] = sender
        username = request.resolver_match.kwargs.get("username")
        attrs["username"] = username
        receiver = get_object_or_404(User, username=username)
        if check_block_relation(sender, receiver):
            raise serializers.ValidationError("you connot follow this user", code=404)
        return attrs


class BlockSesrializer(FollowSerializer):
    class Meta:
        model = Block
        fields = ("from_user", "to_user")
        read_only_fields = ("from_user", "to_user")
