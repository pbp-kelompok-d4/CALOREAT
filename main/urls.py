from django.urls import path
from main.views import *


app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("reviews/create-ajax/", add_review_ajax, name="add_review_ajax"),
    path("api/reviews/", get_reviews_json, name="get_reviews_json"),
]

## masih kosong karena belum di setting di view