from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg
from datetime import date, timedelta
from .models import *

@staff_member_required
def reports_view(request):
    """Main reports dashboard view"""
    context = {
        'title': 'Hotel Management Reports',
        'site_header': 'Hotel Management System',
        'site_title': 'Hotel Admin',
        'today': date.today(),
    }
    return render(request, 'admin/hotel_reports.html', context)

@staff_member_required
def bookings_api(request):
    """API endpoint for bookings data"""
    # Get date range (default to last 12 months)
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    
    # Monthly bookings data
    bookings_by_month = []
    current_date = start_date
    
    while current_date <= end_date:
        month_bookings = Booking.objects.filter(
            booking_date__year=current_date.year,
            booking_date__month=current_date.month,
            payment_status__in=['Paid', 'Processing']
        )
        
        count = month_bookings.count()
        revenue = month_bookings.aggregate(total=Sum('total'))['total'] or 0
        
        bookings_by_month.append({
            'month': current_date.strftime('%Y-%m'),
            'month_name': current_date.strftime('%B %Y'),
            'count': count,
            'revenue': float(revenue)
        })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Booking status distribution
    status_data = list(
        Booking.objects.values('payment_status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Top performing hotels
    top_hotels = list(
        Hotel.objects.annotate(
            booking_count=Count('booking'),
            total_revenue=Sum('booking__total')
        )
        .filter(booking_count__gt=0)
        .order_by('-total_revenue')[:10]
        .values('name', 'booking_count', 'total_revenue')
    )
    
    # Recent bookings
    recent_bookings = list(
        Booking.objects.select_related('hotel', 'user')
        .order_by('-booking_date')[:10]
        .values(
            'booking_id', 'fullname', 'hotel__name', 
            'total', 'payment_status', 'booking_date'
        )
    )
    
    return JsonResponse({
        'monthly_data': bookings_by_month,
        'status_distribution': status_data,
        'top_hotels': top_hotels,
        'recent_bookings': recent_bookings,
        'total_bookings': Booking.objects.count(),
        'total_revenue': float(Booking.objects.filter(payment_status='Paid').aggregate(Sum('total'))['total'] or 0),
        'avg_booking_value': float(Booking.objects.filter(payment_status='Paid').aggregate(Avg('total'))['total'] or 0),
    })

@staff_member_required
def users_api(request):
    """API endpoint for users data"""
    # Monthly user registrations
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    
    users_by_month = []
    current_date = start_date
    
    while current_date <= end_date:
        month_users = User.objects.filter(
            date_joined__year=current_date.year,
            date_joined__month=current_date.month
        ).count()
        
        users_by_month.append({
            'month': current_date.strftime('%Y-%m'),
            'month_name': current_date.strftime('%B %Y'),
            'count': month_users
        })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # User activity stats
    total_users = User.objects.count()
    active_users = User.objects.filter(booking__isnull=False).distinct().count()
    new_users_this_month = User.objects.filter(
        date_joined__year=end_date.year,
        date_joined__month=end_date.month
    ).count()
    
    return JsonResponse({
        'monthly_registrations': users_by_month,
        'total_users': total_users,
        'active_users': active_users,
        'new_users_this_month': new_users_this_month,
        'user_retention_rate': round((active_users / total_users * 100) if total_users > 0 else 0, 2),
    })

@staff_member_required
def hotels_api(request):
    """API endpoint for hotels data"""
    # Hotel status distribution
    hotel_status = list(
        Hotel.objects.values('status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Hotels by city
    hotels_by_city = list(
        Hotel.objects.values('city')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    # Hotel performance metrics
    hotel_performance = list(
        Hotel.objects.annotate(
            total_bookings=Count('booking'),
            total_revenue=Sum('booking__total'),
            total_rooms=Count('rooms')
        )
        .filter(total_bookings__gt=0)
        .order_by('-total_revenue')[:15]
        .values(
            'name', 'city', 'total_bookings', 'total_revenue', 
            'total_rooms', 'views', 'featured'
        )
    )
    
    # Active vs inactive hotels
    active_hotels = Hotel.objects.filter(status='Live').count()
    total_hotels = Hotel.objects.count()
    
    return JsonResponse({
        'status_distribution': hotel_status,
        'hotels_by_city': hotels_by_city,
        'hotel_performance': hotel_performance,
        'active_hotels': active_hotels,
        'total_hotels': total_hotels,
        'featured_hotels': Hotel.objects.filter(featured=True).count(),
    })

@staff_member_required
def room_types_api(request):
    """API endpoint for room types data"""
    # Most booked room types
    room_type_bookings = list(
        RoomType.objects.annotate(
            booking_count=Count('booking'),
            total_revenue=Sum('booking__total'),
            total_nights=Sum('booking__total_days')
        )
        .filter(booking_count__gt=0)
        .order_by('-booking_count')[:10]
        .values(
            'type', 'hotel__name', 'price', 'booking_count', 
            'total_revenue', 'total_nights', 'number_of_beds'
        )
    )
    
    return JsonResponse({
        'most_booked': room_type_bookings,
        'total_room_types': RoomType.objects.count(),
        'total_rooms': Room.objects.count(),
        'available_rooms': Room.objects.filter(is_available=True).count(),
    })