from django.urls import path 
from .views import *

app_name="user_dashboard"

urlpatterns = [
    path("",dasboard,name="dashboard"),
    path("bookings/",bookings,name="bookings"),
    path("booking_details/<booking_id>",booking_details,name="booking_details")
]
