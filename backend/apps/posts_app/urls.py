from django.urls import path
from .views import (
    PostsView,
    PostDetailView,
    ModifyComment,
    CommentPostView,
    LikeView,
)
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path("", PostsView.as_view(), name="posts"),
    path("likes-objects", LikeView.as_view(), name="like-post_comment_reply"),
    path("<str:post_id>", PostDetailView.as_view(), name="post-detail"),
    path(
        "<str:post_id>/comments",
        CommentPostView.as_view(),
        name="comment-post-or-reply-comment",
    ),
    path(
        "<str:post_id>/comments/<str:comment_or_reply_id>",
        ModifyComment.as_view(),
        name="modify-comment",
    ),
]

# urlpatterns = format_suffix_patterns(urlpatterns)
