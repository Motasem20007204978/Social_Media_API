from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import (
    extend_schema_serializer,
    OpenApiExample,
)
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(label="email", write_only=True)

    def create(self, validated_data):
        return validated_data


class PasswordField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs["write_only"] = True
        kwargs["max_length"] = 150
        kwargs["style"] = {"input_type": "password"}
        kwargs["trim_whitespace"] = False
        super().__init__(**kwargs)


class ResetPasswordSerializer(serializers.Serializer):
    password = PasswordField(label="new password")
    confirm_password = PasswordField(label="password again")

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
        path_params = request.resolver_match.kwargs
        user = User.get_user_from_uuid(path_params["uuid"])
        user.check_token_validation(path_params["token"])
        user.check_email_activation()
        attrs["user"] = user
        return attrs


login_response = {
    "refresh": "string",
    "access": "string",
    "refresh_token_timeout": 20000,
    "access_token_timeout": 3600,
    "user": {
        "username": "string",
        "name": "string",
        "email": "string",
    },
}


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="success login",
            value=login_response,
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
