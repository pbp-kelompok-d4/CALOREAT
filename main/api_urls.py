from django.urls import path
from main import api_views

app_name = "api"
urlpatterns = [
    path("reviews/", api_views.review_list, name="review-list"),
    path("reviews/<uuid:review_id>/", api_views.review_detail, name="review-detail"),
]
