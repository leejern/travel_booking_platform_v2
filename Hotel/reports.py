from django.contrib import admin
from django.db.models import Count, Sum, Q, Avg
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.http import JsonResponse
from django.shortcuts import render
from django.db import models
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
import django.forms as forms
from datetime import date, timedelta, datetime
from collections import defaultdict
import json
from decimal import Decimal

from .models import *



class ReportsAdminMixim:
    """Mixin for custom reports functionality in admin."""

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reports/', self.admin_site.admin_view(self.reports_view), name='hotel_reports'),
            path('reports/api/bookings/', self.admin_site.admin_view(self.bookings_api), name='bookings_api'),
            path('reports/api/users/', self.admin_site.admin_view(self.users_api), name='users_api'),
            path('reports/api/hotels/', self.admin_site.admin_view(self.hotels_api), name='hotels_api'),
            path('reports/api/room-types/', self.admin_site.admin_view(self.room_types_api), name='room_types_api'),
        ]
        return custom_urls + urls
    
    def reports_view(self, request):
        """Render the custom reports dashboard."""
        context = {
            'title': 'Hotel Management Reports',
            'has_permission': True, 
            'site_header': self.admin_site.site_header,
            'site_title': self.admin_site.site_title,
            'today':date.today()
        }
        return render(request, 'admin/hotel_reports.html', context)
    
    def bookings_api(self, request):
        """API endpoint foe bookings data"""
        # get the date range, default last 12 months 
        end_date = date.today()
        start_date = end_date - timedelta(days=365)

        # monthly bookings 
        bookings_by_month = []
        revenue_by_month = []

        while start_date <= end_date:
            month_bookings = Booking.objects.filter(
                booking_date__year = start_date.year, 
                booking_date__month = start_date.month, 
                payment_status__in = ['Paid', 'Processing']
            )

            count = month_bookings.count()
            total_revenue = month_bookings.aggregate(sum('total'))['total'] or Decimal(0)
            bookings_by_month.append({
                'month':start_date.strftime('%Y-%m'),
                'month_name':start_date.strftime('%B %Y'),
                'count': count,
                'revenue': float(total_revenue)
            })

            # move tpo the next month
            if start_date.month == 12:
                start_date = start_date.replace(year=start_date.year + 1,month=1)
            else:
                start_date = start_date.replace(month=start_date.month + 1)

        # Booking status distribution 
        status_data = list(
            Booking.objects.values('payment_status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Top perfoming hotels
        top_hotels = list(
            Hotel.objects.annotate(
                 booking_count=Count('booking'),
                total_revenue=Sum('booking__total')
                # booking_count = count('booking', filter=Q(booking__payment_status__in=['Paid', 'Processing'])), 
                # total_revenue = Sum('booking__total', filter=Q(booking__payment_status__in=['Paid', 'Processing']))
            ).filter(booking_count__gt=0)
            .order_by('-total_revenue')[:10]
            .values('name', 'booking_count', 'total_revenue',)
        )

        # Recent bookings
        recent_bookings = list(
            Booking.objects.select_related('hotel', 'user')
            .order_by('-booking_date')[:10]
            .values(
                'booking_id', 'hotel__name', 'user__username', 'fullname', 
                'checkin_date', 'checkout_date', 'total', 'payment_status', 
                'booking_date'
            )
        )

        return JsonResponse({
            'monthly_bookings': bookings_by_month, 
            'booking_status_distribution': status_data,
            'top_hotels': top_hotels,
            'recent_bookings': recent_bookings, 
            'total_bookings': Booking.objects.filter(payment_status__in=['Paid', 'Processing']).count(),
            'total_revenue': float(Booking.objects.filter(paymant_status='Paid').aggregate(Sum('total'))['total'] or 0),
            'avg_booking_value': float(Booking.objects.filter(payment_status='Paid').aggregate(Avg('total'))['total'] or 0),
        })


    def users_api(self, request):
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
        
        # Top customers by bookings
        top_customers = list(
            User.objects.annotate(
                booking_count=Count('booking'),
                total_spent=Sum('booking__total')
            )
            .filter(booking_count__gt=0)
            .order_by('-total_spent')[:10]
            .values('username', 'email', 'booking_count', 'total_spent')
        )
        
        return JsonResponse({
            'monthly_registrations': users_by_month,
            'total_users': total_users,
            'active_users': active_users,
            'new_users_this_month': new_users_this_month,
            'user_retention_rate': round((active_users / total_users * 100) if total_users > 0 else 0, 2),
            'top_customers': top_customers,
        })
    
    def hotels_api(self, request):
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
                avg_rating=Avg('reviews__rating'),
                total_rooms=Count('rooms')
            )
            .filter(total_bookings__gt=0)
            .order_by('-total_revenue')[:15]
            .values(
                'name', 'city', 'total_bookings', 'total_revenue', 
                'avg_rating', 'total_rooms', 'views', 'featured'
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
            'average_views': Hotel.objects.aggregate(Avg('views'))['views__avg'] or 0,
        })
    
    def room_types_api(self, request):
        """API endpoint for room types data"""
        # Most booked room types
        room_type_bookings = list(
            RoomType.objects.annotate(
                booking_count=Count('booking'),
                total_revenue=Sum('booking__total'),
                total_nights=Sum('booking__total_days')
            )
            .filter(booking_count__gt=0)
            .order_by('-booking_count')
            .values(
                'type', 'hotel__name', 'price', 'booking_count', 
                'total_revenue', 'total_nights', 'number_of_beds', 'max_occupancy'
            )
        )
        
        # Room type distribution
        room_type_distribution = list(
            RoomType.objects.values('type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Price analysis
        price_ranges = [
            {'range': '$0-50', 'min': 0, 'max': 50},
            {'range': '$51-100', 'min': 51, 'max': 100},
            {'range': '$101-200', 'min': 101, 'max': 200},
            {'range': '$201-500', 'min': 201, 'max': 500},
            {'range': '$500+', 'min': 501, 'max': 999999},
        ]
        
        price_analysis = []
        for price_range in price_ranges:
            count = RoomType.objects.filter(
                price__gte=price_range['min'],
                price__lte=price_range['max']
            ).count()
            price_analysis.append({
                'range': price_range['range'],
                'count': count
            })
        
        # Average prices by room type
        avg_prices = list(
            RoomType.objects.values('type')
            .annotate(
                avg_price=Avg('price'),
                count=Count('id')
            )
            .order_by('-avg_price')
        )
        
        return JsonResponse({
            'most_booked': room_type_bookings,
            'type_distribution': room_type_distribution,
            'price_analysis': price_analysis,
            'average_prices': avg_prices,
            'total_room_types': RoomType.objects.count(),
            'total_rooms': Room.objects.count(),
            'available_rooms': Room.objects.filter(is_available=True).count(),
        })