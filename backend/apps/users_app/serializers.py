from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Follow, Profile, User, Block
from .utils import get_user_from_uuid
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from drf_base64.fields import Base64ImageField
from drf_writable_nested.serializers import WritableNestedModelSerializer


def repr_data(value):
    data = {
        "id": value.id,
        "username": value.username,
        "name": value.full_name,
    }
    return data


@extend_schema_field(OpenApiTypes.OBJECT)
class RelatedFollowers(serializers.RelatedField):
    def to_representation(self, value):
        return repr_data(value.from_user)


@extend_schema_field(OpenApiTypes.OBJECT)
class RelatedFollowings(serializers.RelatedField):
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


class ProfileSerializer(WritableNestedModelSerializer):

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
            "followers",
            "followings",
            "blockers",
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

    def to_representation(self, instance):
        represntation = super().to_representation(instance)
        p_representation = represntation.pop("profile")
        for k, v in p_representation.items():
            represntation[k] = v
        return represntation


class PasswordField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs["write_only"] = True
        kwargs["max_length"] = 150
        kwargs["style"] = {"input_type": "password"}
        kwargs["trim_whitespace"] = False
        super().__init__(**kwargs)


class RegisterSerializer(serializers.ModelSerializer):

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
            "first_name": {"write_only": True},
            "last_name": {"write_only": True},
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


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
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

    ...


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


class FollowSerializer(serializers.ModelSerializer):
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
        attrs["from_user"] = request.user
        username = request.resolver_match.kwargs.get("username")
        attrs["username"] = username
        get_object_or_404(User, username=username)
        return attrs


class BlockSesrializer(FollowSerializer):
    class Meta:
        model = Block
        fields = ("from_user", "to_user")
        read_only_fields = ("from_user", "to_user")
        ...
