from django.urls import path

from .views import *

app_name= 'Hotel'

urlpatterns = [
    path("",home,name='home'),
    path("hotel/<slug>",hotel_detail,name='hotel_detail'),
    path("detail/<slug:slug>/room-type/<slug:rt_slug>",room_type_detail,name="room_type_detail"),
    path("selected_rooms/",selected_rooms,name="selected_rooms")
]
