from django.contrib import admin
from django.db.models import Count, Sum, Avg
from django.utils.translation import gettext_lazy as _
from django.urls import reverse, path
from django.http import JsonResponse
from django.shortcuts import render
from datetime import date, timedelta

from .models import *


class HotelAdminSite(admin.AdminSite):
    site_header = "Hotel Management System"
    site_title = "Hotel Admin"
    index_title = "Welcome to Hotel Management System"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reports/', self.admin_view(self.reports_view), name='hotel_reports'),
            path('reports/api/bookings/', self.admin_view(self.bookings_api), name='bookings_api'),
            path('reports/api/users/', self.admin_view(self.users_api), name='users_api'),
            path('reports/api/hotels/', self.admin_view(self.hotels_api), name='hotels_api'),
            path('reports/api/room-types/', self.admin_view(self.room_types_api), name='room_types_api'),
        ]
        return custom_urls + urls
    
    def reports_view(self, request):
        """Main reports dashboard view"""
        context = {
            'title': 'Hotel Management Reports',
            'has_permission': True,
            'site_header': self.site_header,
            'site_title': self.site_title,
            'today': date.today(),
        }
        return render(request, 'admin/hotel_reports.html', context)
    
    def bookings_api(self, request):
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
        
        return JsonResponse({
            'monthly_data': bookings_by_month,
            'status_distribution': status_data,
            'top_hotels': top_hotels,
            'total_bookings': Booking.objects.count(),
            'total_revenue': float(Booking.objects.filter(payment_status='Paid').aggregate(Sum('total'))['total'] or 0),
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
        
        return JsonResponse({
            'monthly_registrations': users_by_month,
            'total_users': total_users,
            'active_users': active_users,
            'user_retention_rate': round((active_users / total_users * 100) if total_users > 0 else 0, 2),
        })
    
    def hotels_api(self, request):
        """API endpoint for hotels data"""
        hotel_status = list(
            Hotel.objects.values('status')
            .annotate(count=Count('id'))
        )
        
        active_hotels = Hotel.objects.filter(status='Live').count()
        total_hotels = Hotel.objects.count()
        
        return JsonResponse({
            'status_distribution': hotel_status,
            'active_hotels': active_hotels,
            'total_hotels': total_hotels,
        })
    
    def room_types_api(self, request):
        """API endpoint for room types data"""
        room_type_bookings = list(
            RoomType.objects.annotate(
                booking_count=Count('booking')
            )
            .filter(booking_count__gt=0)
            .order_by('-booking_count')[:10]
            .values('type', 'hotel__name', 'price', 'booking_count')
        )
        
        return JsonResponse({
            'most_booked': room_type_bookings,
        })

    def index(self, request, extra_context=None):
        """Override the admin index to include reports link"""
        extra_context = extra_context or {}
        extra_context['reports_url'] = reverse('admin:hotel_reports')
        return super().index(request, extra_context)