from django.contrib import admin
from .models import Post, Comment, Like, Attachment
from django.contrib.admin.filters import SimpleListFilter

# Register your models here.


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "created_at"]
    search_fields = ["user"]
    list_filter = ["user"]
    list_display_links = ["user"]
    list_per_page = 10


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    ...


admin.site.register(Like)

# https://stackoverflow.com/questions/12215751/can-i-make-list-filter-in-django-admin-to-only-show-referenced-foreignkeys
class PostFilter(SimpleListFilter):
    title = "post"
    parameter_name = "post"

    def lookups(self, request, model_admin):
        posts = set([r.comment.post for r in model_admin.model.objects.all()])
        return [(p.id, p) for p in posts]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(comment__post=self.value())
        return queryset


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):

    ...
