from datetime import datetime as dt
from django.shortcuts import render,redirect
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from Hotel.models import *
from django.template.loader import render_to_string
from django.contrib import messages

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
        
       
        url = reverse("Hotel:room_type_detail", args=[hotel.slug, room_type.slug])
        url_with_params = f"{url}?hotel-id={id}&checkin={checkin}&checkout={checkout}&adults={adults}&children={children}&room_type={room_type}"
        return HttpResponseRedirect(url_with_params)
    

def add_to_selection(request): 
    room_selection={} 
    room_selection[str(request.GET["id"])]={ 
        'hotel_id':request.GET['hotel_id'],
        'hotel_name':request.GET['hotel_name'],
        'room_id':request.GET['room_id'],
        'room_type':request.GET['room_type'],
        'room_name':request.GET['room_name'],
        'room_price':request.GET['room_price'],
        'number_of_beds':request.GET['number_of_beds'],
        'room_number':request.GET['room_number'],
        'checkin':request.GET['checkin'],
        'checkout':request.GET['checkout'],
        'adults':request.GET['adults'],
        'children':request.GET['children'],
    }
    if "selection_data_obj" in request.session:
        if str(request.GET["id"]) in request.session['selection_data_obj']:
            selection_data = request.session['selection_data_obj']
            selection_data[str(request.GET['id'])]['adults'] = int(room_selection[str(request.GET["id"])]["adults"]) 
            selection_data[str(request.GET['id'])]['children'] = int(room_selection[str(request.GET["id"])]["children"]) 
            request.session['selection_data_obj']=selection_data
        else: 
            selection_data = request.session['selection_data_obj']
            selection_data.update(room_selection)
            request.session['selection_data_obj']=selection_data 
    else:
        request.session['selection_data_obj']=room_selection

    data = { 
        "data":request.session['selection_data_obj'], 
        "name":"lijan",
        "total_selected_item":len(request.session['selection_data_obj'])
    }
    messages.success(request, "Added to cart")
    return JsonResponse(data)


def delete_selection(request):
    hotel_id = str(request.GET['id'])
    if "selection_data_obj" in request.session:
        if hotel_id in request.session['selection_data_obj']:
            selection_data = request.session['selection_data_obj']
            del request.session['selection_data_obj'][hotel_id]
            request.session['selection_data_obj'] = selection_data

    total=0
    room_count=0
    total_days=0
    adults=0
    children=0
    checkin=""
    checkout=""
    hotel=None

    if 'selection_data_obj' in request.session:
        for h_id,items in request.session['selection_data_obj'].items():
            id= int(items['hotel_id'])
            checkin= items['checkin']
            checkout= items['checkout']
            adults= int(items['adults']) 
            children= int(items['children']) 
            room_type_= int(items['room_type'])
            room_id= int(items['room_id'])


            room_type = RoomType.objects.get(id=room_type_)

            date_format = "%Y-%m-%d"
            checkin_date = dt.strptime(checkin, date_format)
            checkout_date = dt.strptime(checkout, date_format)
            time_difference = checkout_date - checkin_date

            total_days = time_difference.days
            room_count +=1
            days = total_days
            price = room_type.price
            
            room_price = price*room_count 
            total = room_price*days
            

    context = render_to_string(
        'hotel/async/selected_room.html',
        {
            "data":request.session['selection_data_obj'],
            "total_selected_item":len(request.session['selection_data_obj']),
            "total":total, 
            "total_days":total_days, 
            "adults":adults, 
            "chilren":children,
            "checkin":checkin,
            "checkout":checkout,
            "hotel":hotel,
        }
    )
    # print("=======================================================\n=======================",context)
    return JsonResponse({"data":context, "total_selected_item":len(request.session['selection_data_obj']),}) 