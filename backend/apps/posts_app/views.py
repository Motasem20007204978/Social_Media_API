from urllib import request
from .serializers import *
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView,
    DestroyAPIView,
    get_object_or_404,
)
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib.auth import get_user_model


@extend_schema_view(
    get=extend_schema(
        description="returns home posts that obtain the same user and his followings posts, or takes username option if obtained \
             to check if it exists as a user's username, then return the obtained user's posts.\
                but if the user is blocked, you cannot get his posts",
        operation_id="list posts",
        tags=["posts"],
        parameters=[
            OpenApiParameter(
                name="username",
                description="get specific posts for a user by username",
                type=str,
            ),
            OpenApiParameter(
                name="fields",
                description="select fields you want to be represented, otherwise it will return all fields",
            ),
        ],
    ),
    post=extend_schema(
        operation_id="Create Post", description="Create a Post", tags=["posts"]
    ),
)
class PostsView(ListCreateAPIView):

    serializer_class = PostFeedSerializer
    queryset = Post.objects.all()
    http_method_names = ["get", "post"]

    @property
    def followings_users(self):
        follwings = self.request.user.followings.all()
        user_followings = [
            followeing_relation.to_user for followeing_relation in follwings
        ]
        user_followings.append(self.request.user)
        return user_followings

    def home_queryset(self, queryset):
        home_posts = queryset.filter(user__in=self.followings_users)
        return home_posts

    @property
    def specific_user(self):
        User = get_user_model()
        username = self.request.GET.get("username", "")
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        return user

    def user_post_queryset(self, queryset):
        return queryset.filter(user=self.specific_user)

    def filter_queryset(self, queryset):
        posts = self.home_queryset(queryset)
        if self.specific_user:
            posts = self.user_post_queryset(queryset)
        return posts

    def check_user_blocked(self, user):
        if user in self.request.user.blockings.all():
            return self.permission_denied(request, message="you blocked this user")

    @method_decorator(
        decorator=cache_page(
            timeout=60 * 60 * 24, cache="default", key_prefix="get-posts"
        ),
        name="get_posts",
    )
    def get(self, request, *args, **kwargs):
        if self.specific_user:
            self.check_user_blocked(self.specific_user)
        return super().get(request, *args, **kwargs)


class RetrieveUpdateDestroy(RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "patch", "delete"]

    def _owner_permissions(self):
        permissions = self.get_permissions()
        obj = self.get_object()
        permissions.append(obj.user)
        return permissions

    def check_user_permissions(self, permissions_plus: list = []):
        owner_permissions = self._owner_permissions()
        permissions = owner_permissions.extend(permissions_plus)
        if not self.request.user in permissions:
            return self.permission_denied(self.request)


@extend_schema_view(
    get=extend_schema(
        description="get home posts or a user's posts",
        operation_id="get post by id",
        tags=["modify-post"],
        parameters=[
            OpenApiParameter(
                name="fields",
                description="select fields you want to be represented, otherwise it will return all fields",
            )
        ],
    ),
    patch=extend_schema(
        operation_id="Patch Post", description="Patch a Post", tags=["modify_post"]
    ),
    delete=extend_schema(
        operation_id="Delete Post", description="Delete a Post", tags=["modify_post"]
    ),
)
class PostDetailView(RetrieveUpdateDestroy):
    serializer_class = PostFeedSerializer
    queryset = Post.objects.all()

    # instead of passing lookup field in url and make all changes on it
    def get_object(self):
        pid = self.request.resolver_match.kwargs.get("post_id")
        return get_object_or_404(Post, pk=pid)

    @method_decorator(
        cache_page(timeout=60 * 60 * 24, key_prefix="get-post-by-id"), name="get_post"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        self.check_user_permissions()
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.check_user_permissions()
        return super().delete(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="likes details",
        description="list of details for likes related to a post, a comment, or a reply",
        tags=["likes"],
        parameters=[
            OpenApiParameter(
                name="post_id", description="get likes by post id", type=str
            ),
            OpenApiParameter(
                name="comment_id", description="get likes by comment id", type=str
            ),
            OpenApiParameter(
                name="reply_id", description="get likes by reply id", type=str
            ),
        ],
    ),
    post=extend_schema(
        operation_id="like object",
        description="like a post, comment, or a reply",
        tags=["likes"],
        parameters=[
            OpenApiParameter(
                name="post_id", description="like a post by post id", type=str
            ),
            OpenApiParameter(
                name="comment_id", description="like a comment by comment id", type=str
            ),
            OpenApiParameter(
                name="reply_id", description="like a reply by reply id", type=str
            ),
        ],
    ),
    delete=extend_schema(
        operation_id="ullike object",
        description="takes the first id obtained and unlike a post, comment or reply",
        tags=["likes"],
        parameters=[
            OpenApiParameter(
                name="post_id", description="dislike a post by post id", type=str
            ),
            OpenApiParameter(
                name="comment_id",
                description="dislike a comment by comment id",
                type=str,
            ),
            OpenApiParameter(
                name="reply_id", description="dislike a reply by reply id", type=str
            ),
        ],
    ),
)
class LikeView(ListCreateAPIView, DestroyAPIView):

    serializer_class = LikeSerializer
    queryset = Like.objects.all()
    http_method_names = ["get", "post", "delete"]

    @property
    def get_post_id(self):
        pid = self.request.GET.get("post_id", "")
        return pid

    @property
    def get_comment_id(self):
        cid = self.request.GET.get("comment_id", "")
        return cid

    @property
    def get_reply_id(self):
        rid = self.request.GET.get("reply_id", "")
        return rid

    def get_object(self):

        if self.get_post_id:
            return get_object_or_404(
                Like, object_id=self.get_post_id, content_type="post"
            )
        elif self.get_comment_id:
            return get_object_or_404(
                Like, content_type="comment", object_id=self.get_comment_id
            )
        elif self.get_reply_id:
            return get_object_or_404(
                Like, content_type="comment", object_id=self.get_reply_id
            )

    def filter_queryset(self, queryset):
        if self.get_post_id:
            return queryset.filter(object_id=self.get_post_id, content_type="post")
        elif self.get_comment_id:
            return queryset.filter(
                content_type="comment", object_id=self.get_comment_id
            )
        elif self.get_reply_id:
            return queryset.filter(content_type="comment", object_id=self.get_reply_id)

    def check_delete_permissions(self, obj):
        if self.request.user != obj.user:
            return self.permission_denied(request)

    def delete(self, request, **kwargs):
        self.check_delete_permissions(self.get_object())
        return super().delete(request)


@extend_schema_view(
    get=extend_schema(
        operation_id="get comments",
        description="get comments for a post",
        tags=["comments-replies"],
        parameters=[
            OpenApiParameter(
                name="comment_id", description="get replies for a comment", type=str
            ),
        ],
    ),
    post=extend_schema(
        operation_id="Create Comment or Reply",
        description="if a comment_id (optional) is obtaied it takes it and make the request as a reply for this comment, \
            then returns response with parent field based on that parent is the obtained comment, \
                otherwise it takes post id and make the request as a comment without parent field",
        tags=["comments-replies"],
        parameters=[
            OpenApiParameter(
                name="comment_id",
                description="if filled with a comment id, it will create a reply for a comment",
                type=str,
            ),
        ],
    ),
)
class CommentPostView(ListCreateAPIView):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()
    http_method_names = ["get", "post"]

    @property
    def get_comment_id(self):
        comment_id = self.request.GET.get("comment_id", "")
        return comment_id

    def get_object(self):
        post_id = self.request.resolver_match.kwargs.get("post_id")
        obj = get_object_or_404(Post, id=post_id)
        comment_id = self.get_comment_id
        if comment_id:
            obj = get_object_or_404(Comment, id=comment_id)
        return obj

    def filter_queryset(self, queryset):
        obj = self.get_object()
        if self.get_comment_id:
            return queryset.filter(parent=obj)
        return queryset.filter(post=obj)

    @method_decorator(
        cache_page(timeout=60 * 60 * 24, key_prefix="get-comments"), name="get_commetns"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="Comment Details",
        description="get details for a comment or a reply by id",
        tags=["modify-comments-replies"],
    ),
    patch=extend_schema(
        operation_id="Patch a Comment",
        description="patch comment or reply",
        tags=["modify-comments-replies"],
    ),
    delete=extend_schema(
        operation_id="Delete Comment",
        description="delete comment or reply by id",
        tags=["modify-comments-replies"],
    ),
)
class ModifyComment(RetrieveUpdateDestroy):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()
    http_method_names = ["get", "patch", "delete"]

    def get_object(self):
        obj_id = self.request.resolver_match.kwargs.get("comment_or_reply_id")
        obj = get_object_or_404(Comment, id=obj_id)
        return obj

    def check_delete_permissions(self):
        obj = self.get_object()
        permissions_plus = [obj.post.user]
        return self.check_user_permissions(permissions_plus)

    def delete(self, request, **kwargs):
        self.check_delete_permissions(request)
        return super().delete(request)

    def patch(self, request, **kwargs):
        self.check_user_permissions()
        return super().patch(request)
