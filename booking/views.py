from django.shortcuts import render,redirect
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from Hotel.models import *

# Create your views here.

def check_room_availabilty(request): 
    if request.method == "POST": 
        id = request.POST.get("hotel-id")
        checkin = request.POST.get("checkin")
        checkout = request.POST.get("checkout")
        adults = request.POST.get("adults")
        children = request.POST.get("children")
        roomtype = request.POST.get("room_type")
        

        hotel = Hotel.objects.get(id=id)
        room_type = RoomType.objects.get(hotel=hotel,slug=roomtype)
        
        print("id =======",id)
        print("checkin =======",checkin)
        print("checkout =======",checkout)
        print("adults =======",adults)
        print("children =======",children)
        print("room_type =======",room_type)

        url = reverse("Hotel:room_type_detail", args=[hotel.slug, room_type.slug])
        url_with_params = f"{url}?hotel-id={id}&checkin={checkin}$checkout={checkout}$adults={adults}&children={children}$room_type={room_type}"
        return HttpResponseRedirect(url_with_params)
    

def add_to_selection(request): 
    room_selection={} 
    room_selection[str(request.GET["id"])]={ 
        'hotel_id':request.GET['hotel_id'],
        'hotel_name':request.GET['hotel_name'],
        'room_id':request.GET['room_id'],
        'room_type':request.GET['room_type'],
        'room_price':request.GET['room_price'],
        'number_of_beds':request.GET['number_of_beds'],
        'room_number':request.GET['room_number'],
        'checkin':request.GET['checkin'],
        'checkout':request.GET['checkout'],
        'adults':request.GET['adults'],
        'children':request.GET['children'],
    }
    if "selection_data_odj" in request.session: 
        if str(request.GET['id']) in request.session['selection_data_obj']: 
            selection_data = request.session['selection_data_obj']
            selection_data[str(request.GET['id'])]['adults'] = int(room_selection[str(request.GET["id"])]['adults'])
            selection_data[str(request.GET['id'])]['children'] = int(room_selection[str(request.GET["id"])]['children'])

        else: 
            selection_data = request.session['selection_data_obj']
            selection_data.update(room_selection)
            request.session["selection_data_obj"] = selection_data
            
    else: 
        request.session['selection_data_obj'] = room_selection
    
    data = { 
        "data": request.session["selected_data_obj"], 
        "fruit":"banana",
        "name":"Lijan Ouma",
        "total_selected_items":request.session["selection_data_obj"]
    }

    return JsonResponse(data)