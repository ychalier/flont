from django.urls import path
from . import views

app_name = "flont"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("search", views.search, name="search"),
    path("endpoint", views.endpoint, name="endpoint"),
    path("graph/<short_iri>", views.graph, name="graph"),
]
