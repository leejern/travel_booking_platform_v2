from django.urls import path 

from .views import *  
app_name="booking" 

urlpatterns =[ 
    path("check_room_availabilty", check_room_availabilty, name="check_room_availabilty"),
    path("add_to_selection/", add_to_selection, name="add_to_selection"),
]