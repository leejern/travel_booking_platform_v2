from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import models
from Hotel.models import *

# Create your views here.

@login_required
def dasboard(request):
    booking = Booking.objects.filter(user=request.user,payment_status="Paid")
    total_spent = Booking.objects.filter(user=request.user,payment_status="Paid").aaggregate(amount=models.Sum('total'))

    context = {
        "bookings":booking,
        "total_spent":total_spent
    }

    return render(request,"user_dashboard/base.html",context)