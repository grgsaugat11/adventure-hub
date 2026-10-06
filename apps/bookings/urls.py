from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("", views.booking_list, name="list"),
    path("new/<slug:slug>/", views.create, name="create"),
    path("<uuid:reference>/", views.detail, name="detail"),
    path("<uuid:reference>/cancel/", views.cancel, name="cancel"),
]
