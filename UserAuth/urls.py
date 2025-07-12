from django.urls import path

from .views import *

app_name= 'UserAuth'

urlpatterns = [
    path("sign-up",registerView,name='sign-up'),
    path("sign-in",loginViewTemp,name='sign-in'),
    path("logout",logoutView,name='logout'),
]
