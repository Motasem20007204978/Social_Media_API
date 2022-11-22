from typing import Any
from rest_framework.response import Response
from rest_framework.generics import (
    CreateAPIView,
    ListCreateAPIView,
    get_object_or_404,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
    DestroyAPIView,
    GenericAPIView,
)
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from .models import Block
from users_app.models import Follow
from .serializers import (
    FollowSerializer,
    GoogleLoginSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    EmailSerializer,
    ProfileSerializer,
    ResetPasswordSerializer,
    BlockSesrializer,
)
from django.utils.translation import gettext_lazy as _
from .utils import get_user_from_uuid, activation_url, User
from rest_framework.views import APIView
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework_simplejwt.views import TokenObtainPairView
import requests
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .tasks import send_activation

# Create your views here.


class ListUsers(PageNumberPagination):
    page_size = 10


@extend_schema_view(
    get=extend_schema(
        description="get users by search with username or part of username, it get only first 10 users of matching username",
        operation_id="list users",
        parameters=[
            OpenApiParameter(
                name="username", description="search by username", type=str
            ),
        ],
    ),
    post=extend_schema(
        operation_id="Register",
        description="Register a new user",
        responses={
            201: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="success registration and needs verifying",
                examples=[
                    OpenApiExample(
                        name="Registering User Response",
                        value={"message": "string"},
                        status_codes=["201"],
                        response_only=True,
                        description="after registering success, the system will send you activation email in your box",
                    ),
                ],
            ),
        },
    ),
)
class ListRegisterUserView(ListCreateAPIView):

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    queryset = User.objects.all()
    pagination_class = ListUsers
    http_method_names = ["get", "post"]

    def get_queryset(self):
        filters = self.request.GET.dict()
        if filters.get("username", ""):
            self.queryset = self.queryset.filter(
                username__contains=filters.get("username")
            )
        return self.queryset

    @method_decorator(cache_page(timeout=60 * 60 * 24, key_prefix="get-users"))
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"message": "user must be authenticated"}, status=401)
        return super().get(request, *args, **kwargs)

    def post(self, request):
        super().post(request)
        data = {"email": request.data.get("email")}
        send_activation.delay(data)
        return Response(
            {
                "message": _(
                    "user registerd successfully"
                    ", we sent emial verification link in your inbox"
                )
            },
            status=201,
        )


class EmailActivationData(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmailSerializer


class ResetEmailVerification(EmailActivationData):
    @extend_schema(
        operation_id="reset verification",
        description="reset email verification token and resent email activation link",
        responses={
            100: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="email activation link is sent",
                examples=[
                    OpenApiExample(
                        name="reset activation response",
                        description="after reset, check your inbox to verifying your account",
                        value={"message": "email activation link is reset and sent"},
                        status_codes=["100"],
                    )
                ],
            )
        },
    )
    def post(self, request):
        super().post(request)
        send_activation.delay(request.data)
        return Response({"messaga": "check your email"}, status=100)


@extend_schema_view(
    get=extend_schema(
        operation_id="verify email",
        description="email verification by token",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="success verification",
                examples=[
                    OpenApiExample(
                        name="email verification",
                        value={"message": "string"},
                        status_codes=["200"],
                        description="after verifying the account, you can login and use services",
                    )
                ],
            )
        },
    )
)
class VerifyEmail(GenericAPIView):

    permission_classes = [AllowAny]

    def get(self, request, uuid, token):
        user = get_user_from_uuid(uuid)
        if not user.check_token(token):
            return Response({"error": "invalid token or expired"}, status=400)
        if not user.is_active:
            user.activate()
            user.update_login()
            return Response({"activation": "Email successfully confirmed"}, status=200)
        return Response({"error": "user is already verified"}, status=301)


@extend_schema_view(
    post=extend_schema(
        operation_id="Login",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="login data",
                examples=[
                    OpenApiExample(
                        name="ok",
                        description="Login Response",
                        value={
                            "refresh": "string",
                            "access": "string",
                            "user": {
                                "username": "string",
                                "name": "string",
                                "email": "string",
                            },
                        },
                    )
                ],
            )
        },
    )
)
class LoginView(TokenObtainPairView):

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


class LoginWithGoogleView(CreateAPIView):

    serializer_class = GoogleLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema_view(
    post=extend_schema(
        operation_id="forget password",
        responses={
            100: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="forget password responses reset password email link",
                examples=[
                    OpenApiExample(
                        name="forgetting password response",
                        value={
                            "message": "check email reset password link",
                        },
                        description="reset password link will be sent as email message at your inbox",
                        status_codes=["100"],
                    )
                ],
            )
        },
    )
)
class ForgetPassowrd(EmailActivationData):
    def post(self, request):
        super().post(request)
        data = {
            "email": request.data["email"],
            "url_name": "reset-password",
        }
        send_activation.delay(data)
        return Response({"messaga": "check your email to reset password"}, status=100)


@extend_schema_view(
    post=extend_schema(
        operation_id="reset password",
        responses={
            201: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="reset password and save the new",
                examples=[
                    OpenApiExample(
                        name="resetting password response",
                        value={
                            "message": "new password is set successfully",
                        },
                        description="reset password is done",
                        status_codes=["201"],
                    )
                ],
            )
        },
    )
)
class ResetPassword(CreateAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return Response({"success": "user password is reset successfully"}, status=201)


@extend_schema_view(
    get=extend_schema(
        operation_id="get user data",
        description="get user data by username_validator",
    ),
    patch=extend_schema(
        operation_id="updata user data",
        description="update user data by username_validator, iff the authenticated user is the name's user",
    ),
    delete=extend_schema(
        operation_id="delete user",
        description="delete user data by username_validator, iff the authenticated user is the name's user",
        responses={
            204: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="success deletion",
                examples=[
                    OpenApiExample(
                        name="delete user",
                        description="after deleting your account, you should register a new one",
                        value={"message": "string"},
                        status_codes=["204"],
                    )
                ],
            )
        },
    ),
)
class ProfileView(RetrieveUpdateDestroyAPIView):

    serializer_class = ProfileSerializer
    lookup_field = "username"
    queryset = User.objects.all()
    http_method_names = ["get", "patch", "delete"]

    @method_decorator(cache_page(timeout=60 * 60 * 24, key_prefix="get-user-by-id"))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if self.get_object() != request.user:
            return Response({"message": "user cannot delete another user"}, status=401)
        return super().delete(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        kwargs["hell"] = "hell"
        if self.get_object() != request.user:
            return Response({"message": "user cannot update another user"}, status=401)
        return super().patch(request, *args, **kwargs)


@extend_schema_view(
    post=extend_schema(
        operation_id="change password",
        responses={
            201: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="password changed",
                examples=[
                    OpenApiExample(
                        name="change password",
                        description="Change password",
                        value={
                            "message": "password changed",
                        },
                        status_codes=["201"],
                    )
                ],
            ),
        },
    )
)
class ChangePasswordView(CreateAPIView):

    serializer_class = ChangePasswordSerializer

    def post(self, request):
        super().post(request)
        return Response({"message": "user passowrd is set successfully"}, status=201)


@extend_schema_view(
    post=extend_schema(
        operation_id="follow a user",
        responses={
            201: ProfileSerializer,
        },
    ),
    delete=extend_schema(
        operation_id="unfollow a user",
        responses={
            204: ProfileSerializer,
        },
    ),
)
class FollowView(DestroyAPIView, CreateAPIView):

    serializer_class = FollowSerializer

    @property
    def target(self):
        followee_username = self.request.resolver_match.kwargs["username"]
        target = get_object_or_404(User, username=followee_username)
        return target

    def get_object(self):
        return get_object_or_404(
            Follow, from_user=self.request.user, to_user=self.target
        )

    def post(self, request, *args, **kwargs):
        super().post(request)
        return redirect(
            reverse("user-info", kwargs={"username": request.user.username})
        )

    def delete(self, request, *args, **kwargs):
        super().delete(request)
        return redirect(
            reverse("user-info", kwargs={"username": request.user.username})
        )


@extend_schema_view(
    post=extend_schema(
        operation_id="Block a User",
        responses={
            201: ProfileSerializer,
        },
    ),
    delete=extend_schema(
        operation_id="Unblock a User",
        responses={
            204: ProfileSerializer,
        },
    ),
)
class BlockView(FollowView):
    serializer_class = BlockSesrializer

    def get_object(self):
        return get_object_or_404(
            Block, from_user=self.request.user, to_user=self.target
        )
