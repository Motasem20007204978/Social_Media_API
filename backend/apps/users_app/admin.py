from django.contrib import admin
from .models import User, Follow, Profile, Block

# Register your models here.

admin.site.empty_value_display = "???"
admin.site.site_title = "Social Media"
admin.site.site_header = "Social Media Project"


@admin.register(User)
class StoreAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "date_joined", "is_active"]
    list_filter = ["is_active"]
    search_fields = [
        "username",
        "email",
    ]  # search as %<anything>% usernames or emails that contains <anything>
    list_display_links = ["username", "email"]
    list_per_page = 10
    date_hierarchy = "date_joined"
    ordering = ["username"]
    ...


@admin.register(Follow, Block)
class FollowAdmin(admin.ModelAdmin):
    list_display = ["from_user", "to_user"]
    list_filter = ["from_user", "to_user"]
    search_fields = ["from_user", "to_user"]
    list_display_links = ["from_user", "to_user"]
    list_per_page = 10
    ...


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "gender", "created_at"]
    list_filter = ["gender"]

    def created_at(self, obj):
        return obj.user.date_joined

    ...
