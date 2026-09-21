from django.urls import path
from . import views

app_name = "adventures"

urlpatterns = [
    path("", views.AdventureListView.as_view(), name="list"),
    path("<slug:slug>/", views.adventure_detail, name="detail"),
]