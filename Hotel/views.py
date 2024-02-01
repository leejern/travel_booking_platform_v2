import json
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import *

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

def selected_room(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        selected_type = data.get('type')
        selected_image = data.get('image')

        # Perform any necessary processing with the selected data
        # (e.g., store preferences, retrieve additional information)

        return JsonResponse({'type': selected_type, 'image': selected_image})
    else:
        return HttpResponseBadRequest()


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