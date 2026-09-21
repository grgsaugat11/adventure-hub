from django.urls import path

from . import views

app_name = "destinations"

urlpatterns = [
    path("", views.region_list, name="list"),
    path("<slug:slug>/", views.region_detail, name="detail"),
]