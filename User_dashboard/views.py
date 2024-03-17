from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import models
from django.contrib import messages
from Hotel.models import *

# Create your views here.

@login_required
def dasboard(request):
    booking = Booking.objects.filter(user=request.user,payment_status="Paid")
    total_spent = Booking.objects.filter(user=request.user,payment_status="Paid").aggregate(amount=models.Sum('total'))

    context = {
        "bookings":booking,
        "total_spent":total_spent
    }

    return render(request,"user_dashboard/dashboard.html",context)


@login_required 
def bookings(request):
    bookings = Booking.objects.filter(user=request.user,payment_status="Paid")
    context = {
        'bookings':bookings
    }
    return render(request,"user_dashboard/bookings.html",context) 


@login_required 
def booking_details(request,booking_id):
    booking = Booking.objects.get(booking_id=booking_id,user=request.user,payment_status="Paid")
    context = {
        'booking':booking 
    }
    return render(request,"user_dashboard/booking_details.html",context)
    

@login_required 
def notifications(request):
    notifications = Notifications.objects.filter(user= request.user,seen=False)

    context = {
        'notifications':notifications 
    }
    return render(request,"user_dashboard/notifications.html",context)


@login_required
def mark_as_read(request,id):
    noti = Notifications.objects.get(id=id)
    noti.seen = True 
    noti.save() 
    messages.success(request, "Notification marked as read!")

    return redirect("user_dashboard:notifications")