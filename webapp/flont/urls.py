from django.urls import path
from . import views

app_name = "flont"

urlpatterns = [
    path("", views.landing_page, name="landing_page"),
    path("search", views.search, name="search"),
    path("endpoint", views.endpoint, name="endpoint"),
]
