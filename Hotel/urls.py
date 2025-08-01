from django.urls import path

from .views import *

app_name= 'Hotel'

urlpatterns = [
    path("",home,name='home'),
    path("hotel/<slug>",hotel_detail,name='hotel_detail'),
    path("detail/<slug:slug>/room-type/<slug:rt_slug>",room_type_detail,name="room_type_detail"),
    path("selected_rooms/",selected_rooms,name="selected_rooms"),
    path("checkout/<booking_id>/",checkout,name="checkout"),
    path("update_room_status/",update_room_status,name="update_room_status"),

    # Admin custom views for reports
    # path('reports/', views.reports_view, name='hotel_reports'),
    # path('reports/api/bookings/', views.bookings_api, name='bookings_api'),
    # path('reports/api/users/', views.users_api, name='users_api'),
    # path('reports/api/hotels/', views.hotels_api, name='hotels_api'),
    # path('reports/api/room-types/', views.room_types_api, name='room_types_api'),

    



    #payments routes 
    path("api/create_checkout_session/<booking_id>/",create_checkout_session,name='api_checkout_session'),
    path('success/<booking_id>/',payment_success, name='success'),
    path('failed/<booking_id>/',payment_failed, name='failed'),
]
