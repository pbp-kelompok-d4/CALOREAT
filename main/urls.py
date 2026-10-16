from django.urls import path
from main.views import *


app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
]

## masih kosong karena belum di setting di view