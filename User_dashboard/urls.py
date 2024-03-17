from django.urls import path 
from .views import *

app_name="user_dashboard"

urlpatterns = [
    path("",dasboard,name="dashboard"),
    path("bookings/",bookings,name="bookings"),
    path("notifications/",notifications ,name="notifications"),
    path("mark_as_read/<id>/",mark_as_read ,name="mark_as_read"),
    path("booking_details/<booking_id>",booking_details,name="booking_details")
]
