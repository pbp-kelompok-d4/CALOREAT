from django.urls import path
from main import api_views, auth_api_views

app_name = "api"
urlpatterns = [
    path("reviews/", api_views.review_list, name="review-list"),
    path("reviews/<uuid:review_id>/", api_views.review_detail, name="review-detail"),
    
    path("auth/register/", auth_api_views.api_register, name="auth-register"),
    path("auth/login/", auth_api_views.api_login, name="auth-login"),
    path("auth/logout/", auth_api_views.api_logout, name="auth-logout"),
    path("auth/me/", auth_api_views.api_me, name="auth-me"),
]
