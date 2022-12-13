from os import stat
from .serializers import *
from rest_framework.response import Response
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView,
    DestroyAPIView,
    get_object_or_404,
)
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_cookie, vary_on_headers
from django.views.decorators.cache import cache_page
from django.contrib.auth import get_user_model


@extend_schema_view(
    get=extend_schema(
        description="get home posts or a user's posts",
        operation_id="list posts",
        parameters=[
            OpenApiParameter(name="username", description="list by username", type=str),
            OpenApiParameter(name="fields", description="select fields to represent"),
        ],
    ),
    post=extend_schema(
        operation_id="Create Post",
        description="Create a Post",
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

    @method_decorator(
        decorator=cache_page(
            timeout=60 * 60 * 24, cache="default", key_prefix="get-posts"
        ),
        name="get_posts",
    )
    def get(self, request, *args, **kwargs):
        if self.specific_user:
            if self.specific_user in request.user.blockings.all():
                return Response(
                    data={"invalid_access": "this user is blocked"}, status=404
                )
        return super().get(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        description="get home posts or a user's posts",
        operation_id="get post by id",
        parameters=[
            OpenApiParameter(name="fields", description="select fields to represent")
        ],
    ),
    patch=extend_schema(
        operation_id="Patch Post",
        description="Patch a Post",
    ),
    delete=extend_schema(
        operation_id="Delete Post",
        description="Delete a Post",
    ),
)
class PostDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = PostFeedSerializer
    http_method_names = ["get", "patch", "delete"]

    # instead of passing lookup field in url and make all changes on it
    def get_object(self):
        pid = self.request.resolver_match.kwargs.get("post_id")
        return get_object_or_404(Post, pk=pid)

    @method_decorator(
        cache_page(timeout=60 * 60 * 24, key_prefix="get-post-by-id"), name="get_post"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @property
    def user_own_post_permission(self):
        return self.request.user == self.get_object().user

    def patch(self, request, *args, **kwargs):
        if self.user_own_post_permission:
            return super().partial_update(request, *args, **kwargs)
        return Response(
            {"update not allowed": "this post can be updated only by its user"}
        )

    def delete(self, request, *args, **kwargs):
        if self.user_own_post_permission:
            return super().delete(request, *args, **kwargs)
        return Response(
            {"update not allowed": "this post can be deleted only by its user"}
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="likes details",
        description="list of details for likes related to a post, a comment, or a reply",
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
        description="unlike a post, comment or reply",
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

    def post(self, request, **kwargs):
        return super().post(request)

    def delete(self, request, **kwargs):
        super().delete(request)
        return super().get(request)


@extend_schema_view(
    get=extend_schema(
        operation_id="get comments",
        description="get comments for a post",
        parameters=[
            OpenApiParameter(
                name="comment_id", description="get replies for a comment", type=str
            ),
        ],
    ),
    post=extend_schema(
        operation_id="Create Comment",
        description="create a comment for a post",
        parameters=[
            OpenApiParameter(
                name="comment_id", description="create a reply for a comment", type=str
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

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="Comment Details",
        description="get details for a comment or a reply by id",
    ),
    patch=extend_schema(
        operation_id="Patch a Comment", description="patch comment or reply"
    ),
    delete=extend_schema(
        operation_id="Delete Comment", description="delete comment or reply by id"
    ),
)
class ModifyComment(RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()
    http_method_names = ["get", "patch", "delete"]

    def get_object(self):
        obj_id = self.request.resolver_match.kwargs.get("comment_or_reply_id")
        obj = get_object_or_404(Comment, id=obj_id)
        return obj

    @property
    def delete_permission(self):
        obj = self.get_object()
        permessions = [obj.user, obj.post.user]
        if obj.parent:
            permessions.append(obj.parent.user)
            ...
        return self.request.user in permessions

    def delete(self, request, **kwargs):
        if self.delete_permission:
            return super().delete(request)
        return Response(
            {
                "delete not allowed": "this comment can be deletd only by its user or its post`s user"
            }
        )

    def patch(self, request, **kwargs):
        if self.get_object().user == request.user:
            super().patch(request)
            return self.get(request)
        return Response(
            {"updating not allowed": "this comments can be updated only by its user"}
        )
