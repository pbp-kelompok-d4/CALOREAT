from django.contrib import admin

from main.models import CalorieProfile, FoodEntry, Reviews


@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "star", "date")
    list_filter = ("star", "date")
    search_fields = ("customer_name", "content")
    readonly_fields = ("id", "profile_picture", "date")


@admin.register(CalorieProfile)
class CalorieProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "sex", "activity_level", "goal", "updated_at")
    search_fields = ("user__username", "user__email", "user__first_name")
    list_filter = ("sex", "activity_level", "goal")


@admin.register(FoodEntry)
class FoodEntryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "date", "meal", "grams", "kcal_100g")
    search_fields = ("name", "brand", "user__username")
    list_filter = ("date", "meal")
    date_hierarchy = "date"
