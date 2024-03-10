from django.urls import path 
from .views import *

app_name="user_dashboard"

urlpatterns = [
    path("",dasboard,name="dashboard"),
]
