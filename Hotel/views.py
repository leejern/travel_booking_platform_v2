from decimal import Decimal
import json
from django.http import HttpResponseBadRequest, JsonResponse
from django.conf import settings
from django.shortcuts import *
from UserAuth.models import User 
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from datetime import datetime as dt
import stripe


from .models import *
# Create your views here.
def home(request):
    hotels = Hotel.objects.filter(status="Live") 

    context = {
        "hotels":hotels
    }
    return render(request,"hotel/index.html",context) 


def hotel_detail(request,slug):
    hotel = Hotel.objects.get(slug=slug)
    rtype=RoomType.objects.filter(hotel=hotel,)

    context = {
        "hotel":hotel, 
        "rtype":rtype
    }
    return render(request,"hotel/hotel_page.html",context) 



def room_type_detail(request,slug,rt_slug): 
    hotel=Hotel.objects.get(slug=slug) 
    room_type=RoomType.objects.get(hotel=hotel,slug=rt_slug)
    rtype=RoomType.objects.filter(hotel=hotel,)
    rooms= Room.objects.filter(room_type=room_type,is_available=True)


    id = request.GET.get("hotel-id")
    checkin = request.GET.get("checkin")
    checkout = request.GET.get("checkout")
    adults = request.GET.get("adults")
    children = request.GET.get("children")

    context = {  
        "hotel":hotel, 
        "room_type":room_type, 
        "rtype":rtype,          
        "checkin":checkin, 
        "checkout":checkout, 
        "adults":adults, 
        "children":children, 
        "rooms":rooms
    }

    return render(request,"hotel/room_type_detail.html",context)


def selected_rooms(request):
    # context = {}
    total=0
    room_count=0
    total_days=0
    adults=0
    children=0
    checkin=""
    checkout=""
    # room_type=None

    if "selection_data_obj" in request.session:
        hotel = None

        if request.method == "POST":
            for h_id,items in request.session['selection_data_obj'].items():
                id= int(items['hotel_id'])
                checkin= items['checkin']
                checkout= items['checkout']
                adults= int(items['adults']) if not None else 0
                children= int(items['children']) if not None else 0
                room_type_= int(items['room_type'])
                room_id= int(items['room_id'])\
                
                user = request.user

                hotel = Hotel.objects.get(id=id)
                room = Room.objects.get(id=room_id)
                room_type = RoomType.objects.get(id=room_type_)

            date_format = "%Y-%m-%d"
            checkin_date = dt.strptime(checkin, date_format)
            checkout_date = dt.strptime(checkout, date_format)
            time_difference = checkout_date - checkin_date

            total_days = time_difference.days

            firstname = request.POST.get('firstname')
            lastname = request.POST.get('lastname')
            email = request.POST.get('email')
            phone = request.POST.get('phone')

            booking = Booking.objects.create(
                hotel=hotel,
                room_type=room_type,
                checkin_date=checkin,
                checkout_date=checkout,
                total_days=total_days,
                num_adults=adults,
                num_children=children,
                fullname=firstname +" "+lastname,
                email=email,
                phone=phone,  
                payment_status = "Processing",

                user = request.user or None           
            )
            for h_id,items in request.session['selection_data_obj'].items():
                room_id = int(items['room_id'])
                room = Room.objects.get(id=room_id)
                booking.room.add(room)

                room_count +=1
                days = total_days
                price = int(room_type.price)                
                room_price = price*room_count 
                total = room_price*days

            booking.total += float(total)
            booking.before_discount += float(total)
            booking.save()

            return redirect("Hotel:checkout",booking.booking_id)

        
        for h_id,items in request.session['selection_data_obj'].items():
            id= int(items['hotel_id'])
            checkin= items['checkin']
            checkout= items['checkout']
            adults= int(items['adults']) if not None else 0
            children= int(items['children']) if not None else 0
            room_type_= int(items['room_type'])
            room_id= int(items['room_id'])


            room_type = RoomType.objects.get(id=room_type_)

            date_format = "%Y-%m-%d"
            checkin_date = datetime.strptime(checkin, date_format)
            checkout_date = datetime.strptime(checkout, date_format)
            time_difference = checkout_date - checkin_date

            total_days = time_difference.days
            room_count +=1
            days = total_days
            price = int(room_type.price)
            # room_name_= room_type.type
            # room_type=room_name_
            room_price = price*room_count 
            total = room_price*days

            hotel = Hotel.objects.get(id=id)
            
        context = {
            "data": request.session['selection_data_obj'],
            "total_selected_item": len(request.session['selection_data_obj']),
            # "room_name":room_type,
            "total":total,
            "total_days":total_days,
            "adults":adults,
            "children":children,
            "checkin":checkin,
            "checkout":checkout,
            "hotel":hotel,
        }

        return render(request,"hotel/selected_rooms.html",context)

            
    else:
        return redirect("/")
    # return render(request,"hotel/selected_rooms.html",context)
    

def checkout(request,booking_id):
    booking = Booking.objects.get(booking_id=booking_id)
    if request.method == "POST":
        code = request.POST.get("code")
        try:
            coupon = Coupon.objects.get(code__iexact=code,active=True)
            if coupon in booking.coupons.all():
                messages.warning(request,"Coupon already Activated!")
                return redirect('Hotel:checkout',booking.booking_id)
            else:
                if coupon.type == "Percentage":
                    discount = booking.total* coupon.discount / 100
                else: 
                    discount = coupon.discount
                
                booking.coupons.add(coupon)
                booking.total -= discount
                booking.saved += discount
                booking.payment_status = "Processing"
                booking.save()
                coupon.redemptions +=1
                coupon.save()

                messages.success(request, "Coupon Activated!")
                return redirect('Hotel:checkout',booking.booking_id)
        except: 
            messages.error(request,"Coupon Does Not Exist")
    
    context = {
        "booking":booking, 
        "stripe_publishable_key": settings.STRIPE_PUBLIC_KEY,
    }
    

    return render(request,"hotel/checkout.html",context)


@csrf_exempt
def create_checkout_session(request,booking_id):
    booking = Booking.objects.get(booking_id=booking_id)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    checkout_session = stripe.checkout.Session.create(
        customer_email= booking.email,
        payment_method_types=['card'],
        line_items=[ 
            {
                'price_data':{
                    'currency':'USD', 
                    'product_data':{
                        'name':booking.fullname
                    }, 
                    'unit_amount':int(booking.total)
                }, 
                'quantity':1
            }
        ],
        mode= 'payment',
        success_url= request.build_absolute_uri(reverse('Hotel:success',args=[booking.booking_id]))+"?session_id{CHECKOUT_SESSION_ID}&succes_id="+booking.success_id+"&booking_total="+str(booking.total), 
        cancel_url= request.build_absolute_uri(reverse('Hotel:failed',args=[booking.booking_id]))
    )

    booking.payment_status = 'Processing'
    booking.stripe_payment_intent = checkout_session['id']
    booking.save()

    return JsonResponse({'sessionID':checkout_session.id})


def payment_success(request,booking_id):
    user=None
    if request.user.is_authenticated:
        print("Authenticated user: ", request.user)
        user = request.user


    success_id = request.GET.get('success_id')
    booking_total = request.GET.get('booking_total')
    if success_id and booking_total:
        success_id = success_id.rstrip("/")
        booking_total = booking_total.rstrip("/")

        booking = Booking.objects.get(booking_id=booking_id, success_id=success_id)
        if booking.total == Decimal(booking_total):
            if booking.payment_status == "Processing":
                booking.payment_status = 'Paid'
                booking.save()

                print("===========================================booking saved========================================")
                noti = Notifications.objects.create(
                    booking=booking, 
                    type="Booking Confirmed",
                    user=user
                )
                noti.save()
                print("===========================================Notification saved========================================")

                if 'selection_data_obj' in request.session:
                    del request.session['selection_data_obj']
            else:
                messages.success(request,"Payment made already, thanks for your Patronage")
        else:
            messages.error(request,"Payment manupilation detected!")
    return render(request,'hotel/payment_success.html',{"booking":booking})
#/success/WX3JWN62/?success=ervttjjbjz&payer_id=9BC70445HA750121P&status=COMPLETED&booking_total=9600

def payment_failed(request):
    #return render(request,'hotel/payment_failed.html')
    pass