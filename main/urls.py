from django.urls import path
from main.views import (
    show_main, add_review_ajax, delete_review_ajax, bulk_delete_reviews_ajax,
    get_reviews_json, register, login_user, logout_user, edit_review
)
from main.calorie_views import (
    calorie_count, search_food, barcode_food, entries_collection_api,
    entry_detail_api, summary_api, week_summary_api, profile_api,
)

from main.portion_views import (
    portion_guidance,
    portion_create,
    portion_edit,
    portion_delete,
)

from main.catalog_views import food_catalog


app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("calorie-count/", calorie_count, name="calorie_count"),
    path("api/food-search/", search_food, name="food_search"),
    path("api/foods/search/", search_food, name="foods_search"),
    path("api/foods/barcode/<str:code>/", barcode_food, name="food_barcode"),
    path("api/entries/", entries_collection_api, name="entries"),
    path("api/entries/<int:entry_id>/", entry_detail_api, name="entry_detail"),
    path("api/summary/", summary_api, name="summary"),
    path("api/summary/week/", week_summary_api, name="summary_week"),
    path("api/profile/", profile_api, name="profile"),
    path("reviews/create-ajax/", add_review_ajax, name="add_review_ajax"),
    path("reviews/delete-ajax/<uuid:id>/", delete_review_ajax, name="delete_review_ajax"),
    path("reviews/bulk-delete-ajax/", bulk_delete_reviews_ajax, name="bulk_delete_reviews_ajax"),
    path("reviews/<uuid:reviews_id>/edit/", edit_review, name="edit_review"),
    path("api/reviews/", get_reviews_json, name="get_reviews_json"),
    path("portion-guidance/", portion_guidance, name="portion_guidance"),
    path("portion-guidance/create/", portion_create, name="portion_create"),
    path("portion-guidance/<int:guide_id>/edit/", portion_edit, name="portion_edit"),
    path("portion-guidance/<int:guide_id>/delete/", portion_delete, name="portion_delete"),
    path("catalog/", food_catalog, name="food_catalog"),
    
    path("register/", register, name="register"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
]
