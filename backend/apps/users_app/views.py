from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.generics import (
    CreateAPIView,
    ListCreateAPIView,
    ListAPIView,
    get_object_or_404,
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
    BasicDataSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    EmailSerializer,
    ProfileSerializer,
    ResetPasswordSerializer,
    BlockSesrializer,
)
from django.utils.translation import gettext_lazy as _
from .utils import get_user_from_uuid, check_block_relation, User
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from .tasks import send_activation
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

# Create your views here.


class ListUsers(PageNumberPagination):
    page_size = 10


class AbstractAPIView(GenericAPIView):
    serializer_class = BasicDataSerializer
    queryset = User.objects.all()


@extend_schema_view(
    get=extend_schema(
        description="takes username or fields and return users' data according to username or fields to be returned",
        operation_id="list users",
        parameters=[
            OpenApiParameter(
                name="username", description="search by username", type=str
            ),
            OpenApiParameter(
                name="fields",
                description="select fields you want to be represented, otherwise it will return all fields",
            ),
        ],
    ),
)
class ListUsersView(AbstractAPIView, ListAPIView):
    pagination_class = ListUsers
    http_method_names = ["get"]

    def get_queryset(self):
        filters = self.request.GET.dict()
        if filters.get("username", ""):
            self.queryset = self.queryset.filter(
                username__contains=filters.get("username")
            )
        return self.queryset

    def filter_queryset(self, queryset):
        curr_user = self.request.user
        usernames = [
            user.username
            for user in queryset.all()
            if check_block_relation(curr_user, user)
        ]
        queryset = queryset.exclude(username__in=usernames)
        return queryset

    @method_decorator(cache_page(timeout=60 * 60 * 24, key_prefix="get-users"))
    @method_decorator(
        vary_on_headers(
            "Authorization",
        )
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@extend_schema_view(
    post=extend_schema(
        operation_id="Register",
        description="takes user data and stores it, then returns a message ensures that the registration successful if the data valid",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="Registering User Response",
                        value={
                            "message": "registration success, check your email to verify account"
                        },
                    ),
                ],
            ),
        },
    ),
)
class RegisterAPIView(AbstractAPIView, CreateAPIView):
    permission_classes = [AllowAny]
    http_method_names = ["post"]

    def post(self, request):
        super().post(request)
        return Response(
            {
                "message": _(
                    "user registerd successfully"
                    ", we sent emial verification link in your inbox"
                )
            },
        )


class EmailActivationData(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmailSerializer


class ResetEmailVerification(EmailActivationData):
    @extend_schema(
        operation_id="reset verification",
        description="takes email and resends email activation link with uuid and token for the user",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="reset activation response",
                        value={"message": "email activation link is reset and sent"},
                    )
                ],
            )
        },
    )
    def post(self, request):
        super().post(request)
        data = {"email": request.data["email"]}
        send_activation.delay(data)
        return Response({"messaga": "check your email"}, status=200)


@extend_schema_view(
    get=extend_schema(
        operation_id="verify email",
        description="takes uuid and token to check and return a message ensures the successful verification process",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="success verification if parameters are valid",
                examples=[
                    OpenApiExample(
                        name="email verification",
                        value={"message": "Email successfully confirmed"},
                    )
                ],
            )
        },
    )
)
class VerifyEmail(GenericAPIView):

    permission_classes = [AllowAny]

    def get_object(self):
        uuid = self.request.resolver_match.kwargs.get("uuid", "")
        user = get_user_from_uuid(uuid)
        return user

    def check_token_validation(self, user, token):
        return user.check_token_validation(token)

    def perform_activation(self, user):
        if user.is_active:
            return Response({"message": "user is already verified"})
        return user.activate()

    def get(self, request, token, **kwargs):
        user = self.get_object()
        self.check_token_validation(user, token)
        self.perform_activation(user)
        return Response({"activation": "Email successfully confirmed"})


@extend_schema_view(
    post=extend_schema(
        operation_id="Login",
        description="takes user credentials (email and password) and returns login data if the credentials is valid",
    )
)
class LoginView(TokenObtainPairView):

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


@extend_schema_view(
    post=extend_schema(
        operation_id="forget password",
        description="takes user's email and return a message enshure that is an activation link is sent to your email inbox to reset password",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="forgetting password response",
                        value={
                            "message": "check email reset password link",
                        },
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
        return Response({"messaga": "check your email to reset password"})


@extend_schema_view(
    post=extend_schema(
        operation_id="reset password",
        description="takes uuid and token from sent email as a parameters and check if the parameters is valid, then it takes new password to be reset to the users' account",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="resetting password response",
                        value={
                            "message": "new password is set successfully",
                        },
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
        return Response({"success": "user password is reset successfully"})


@extend_schema_view(
    get=extend_schema(
        operation_id="get user data",
        description="get user data by username_validator",
        parameters=[
            OpenApiParameter(
                name="fields",
                description="select fields you want to be represented, otherwise it will return all fields",
            ),
        ],
    ),
    patch=extend_schema(
        operation_id="updata user data",
        description="update user data by username_validator, iff the authenticated user is the name's user",
        parameters=[
            OpenApiParameter(
                name="fields",
                description="select fields you want to be represented, otherwise it will return all fields",
            ),
        ],
    ),
    delete=extend_schema(
        operation_id="delete user",
        description="takes username and delete the user, iff the authenticated user is the name's user",
        responses={
            204: OpenApiResponse(
                examples=[
                    OpenApiExample(
                        name="delete user",
                    ),
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

    def check_owner_permissions(self):
        if self.request.user != self.get_object():
            self.permission_denied(self.request)

    def delete(self, request, *args, **kwargs):
        self.check_owner_permissions()
        return super().delete(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        self.check_owner_permissions()
        return super().patch(request, *args, **kwargs)


@extend_schema_view(
    post=extend_schema(
        operation_id="change password",
        description="takes the old password to check if it is correct for the curren person, and then reset the old with new password",
        responses={
            201: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="change password",
                        value={
                            "message": "password changed",
                        },
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
        description="takes the username of user to be followed to make following process, and then returns the user following lists",
    ),
    delete=extend_schema(
        operation_id="unfollow a user",
        description="takes the username of the user to be unfollowed to make unfollowing process",
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
        obj = get_object_or_404(
            Follow, from_user=self.request.user, to_user=self.target
        )
        return obj


@extend_schema_view(
    post=extend_schema(
        operation_id="Block a User",
    ),
    delete=extend_schema(
        operation_id="Unblock a User",
    ),
)
class BlockView(FollowView):
    serializer_class = BlockSesrializer

    def get_object(self):
        return get_object_or_404(
            Block, from_user=self.request.user, to_user=self.target
        )


@extend_schema_view(post=extend_schema(operation_id="refresh"))
class RefreshAccess(TokenRefreshView):
    ...


@extend_schema_view(
    post=extend_schema(
        operation_id="logout",
        description="takes refresh token and blacklists it into blacklist table",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="success logout",
                        value={
                            "message": "the refresh token is blacklisted and you connot use it forever"
                        },
                    )
                ],
            )
        },
    )
)
class Logout(TokenBlacklistView):
    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return Response(
            data={
                "message": "the refresh token is blacklisted and you connot use it forever"
            }
        )
