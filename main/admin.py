from django.contrib import admin

from main.models import Reviews


@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "star", "date")
    list_filter = ("star", "date")
    search_fields = ("customer_name", "content")
    readonly_fields = ("id", "profile_picture", "date")
