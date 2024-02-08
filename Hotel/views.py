import json
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import *
from datetime import datetime
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
            print(h_id,items)
            # print("rooom name ===============================================================================",room_name)

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
    
