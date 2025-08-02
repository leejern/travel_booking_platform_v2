# custom_admin.py
from django.template.response import TemplateResponse
from django.contrib.admin import AdminSite
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncMonth, TruncDay
from .models import *
from UserAuth.models import User as CustomUser

import datetime
from datetime import timedelta

class CustomAdminSite(AdminSite):
    site_header = 'Hotel Admin Dashboard'
    site_title = 'Hotel Admin'
    index_title = 'Welcome to the Admin Dashboard'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_view(self.hotel_reports_view), name='dashboard'),
            path('reports/', self.admin_view(self.hotel_reports_view), name='hotel_reports'),
            
            # Existing API endpoints
            path('reports/api/bookings/', self.admin_view(self.booking_stats_api), name='booking_stats_api'),
            path('reports/api/users/', self.admin_view(self.user_stats_api), name='user_stats_api'),
            path('reports/api/hotels/', self.admin_view(self.hotel_distribution_api), name='hotel_distribution_api'),
            path('reports/api/room-types/', self.admin_view(self.room_type_distribution_api), name='room_type_distribution_api'),
            
            # New API endpoints to match JavaScript calls
            path('reports/statistics/', self.admin_view(self.statistics_api), name='statistics_api'),
            path('reports/bookings-chart/', self.admin_view(self.bookings_chart_api), name='bookings_chart_api'),
            path('reports/users-chart/', self.admin_view(self.users_chart_api), name='users_chart_api'),
            path('reports/payment-status/', self.admin_view(self.payment_status_api), name='payment_status_api'),
            path('reports/room-types/', self.admin_view(self.room_types_chart_api), name='room_types_chart_api'),
            path('reports/top-hotels/', self.admin_view(self.top_hotels_api), name='top_hotels_api'),
            path('reports/recent-bookings/', self.admin_view(self.recent_bookings_api), name='recent_bookings_api'),
            
            # Export endpoints
            path('reports/export/pdf/', self.admin_view(self.export_pdf), name='export_pdf'),
            path('reports/export/excel/', self.admin_view(self.export_excel), name='export_excel'),
            path('reports/export/csv/', self.admin_view(self.export_csv), name='export_csv'),
        ]
        return custom_urls + urls

    def get_date_range(self, request):
        """Helper method to get date range from request parameters"""
        days = int(request.GET.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Convert to timezone-aware datetime objects for filtering
        start_datetime = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min))
        end_datetime = timezone.make_aware(datetime.datetime.combine(end_date, datetime.time.max))
        
        return start_datetime, end_datetime

    def get_hotel_filter(self, request):
        """Helper method to get hotel filter from request parameters"""
        hotel_id = request.GET.get('hotel')
        if hotel_id:
            try:
                return Hotel.objects.get(id=hotel_id)
            except Hotel.DoesNotExist:
                pass
        return None

    def hotel_reports_view(self, request):
        # Get all hotels for the filter dropdown
        hotels = Hotel.objects.all().values('id', 'name')
        
        context = dict(
            self.each_context(request),
            title='Hotel Reports Dashboard',
            hotels=list(hotels),
        )
        return TemplateResponse(request, 'admin/hotel_reports.html', context)

    def statistics_api(self, request):
        """API endpoint for main statistics"""
        start_date, end_date = self.get_date_range(request)
        hotel_filter = self.get_hotel_filter(request)
        
        # Base queryset for bookings
        bookings_qs = Booking.objects.filter(booking_date__range=(start_date, end_date))
        if hotel_filter:
            bookings_qs = bookings_qs.filter(room__hotel=hotel_filter)
        
        # Calculate statistics
        total_bookings = bookings_qs.count()
        total_revenue = bookings_qs.filter(payment_status__in=['Paid', 'Processing']).aggregate(
            total=Sum('total'))['total'] or 0
        
        avg_booking_value = bookings_qs.filter(payment_status='Paid').aggregate(
            avg=Avg('total'))['avg'] or 0
        
        # User statistics
        users_qs = CustomUser.objects.filter(date_joined__range=(start_date, end_date))
        total_users = users_qs.count()
        
        # Hotel statistics
        hotels_qs = Hotel.objects.all()
        if hotel_filter:
            hotels_qs = hotels_qs.filter(id=hotel_filter.id)
        
        active_hotels = hotels_qs.filter(status='Live').count()
        featured_hotels = hotels_qs.filter(is_featured=True).count() if hasattr(Hotel, 'is_featured') else 0
        
        # Room statistics
        rooms_qs = Room.objects.all()
        if hotel_filter:
            rooms_qs = rooms_qs.filter(hotel=hotel_filter)
        
        available_rooms = rooms_qs.filter(is_available=True).count() if hasattr(Room, 'is_available') else rooms_qs.count()
        
        # User retention (simplified - users who made bookings)
        active_users = CustomUser.objects.filter(booking__isnull=False).distinct().count()
        user_retention = (active_users / CustomUser.objects.count() * 100) if CustomUser.objects.count() > 0 else 0
        
        return JsonResponse({
            'total_bookings': total_bookings,
            'total_revenue': float(total_revenue),
            'total_users': total_users,
            'active_hotels': active_hotels,
            'avg_booking_value': float(avg_booking_value),
            'user_retention': user_retention,
            'available_rooms': available_rooms,
            'featured_hotels': featured_hotels,
        })

    def bookings_chart_api(self, request):
        """API endpoint for bookings chart data"""
        start_date, end_date = self.get_date_range(request)
        hotel_filter = self.get_hotel_filter(request)
        
        # Get daily bookings data for the chart
        bookings_qs = Booking.objects.filter(booking_date__range=(start_date, end_date))
        if hotel_filter:
            bookings_qs = bookings_qs.filter(room__hotel=hotel_filter)
        
        daily_data = (
            bookings_qs.filter(payment_status__in=['Paid', 'Processing'])
            .annotate(day=TruncDay('booking_date'))
            .values('day')
            .annotate(count=Count('id'), revenue=Sum('total'))
            .order_by('day')
        )
        
        labels = []
        bookings = []
        revenue = []
        
        for entry in daily_data:
            labels.append(entry['day'].strftime('%Y-%m-%d'))
            bookings.append(entry['count'])
            revenue.append(float(entry['revenue'] or 0))
        
        return JsonResponse({
            'labels': labels,
            'bookings': bookings,
            'revenue': revenue
        })

    def users_chart_api(self, request):
        """API endpoint for users chart data"""
        start_date, end_date = self.get_date_range(request)
        
        daily_data = (
            CustomUser.objects.filter(date_joined__range=(start_date, end_date))
            .annotate(day=TruncDay('date_joined'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        
        labels = []
        users = []
        
        for entry in daily_data:
            labels.append(entry['day'].strftime('%Y-%m-%d'))
            users.append(entry['count'])
        
        return JsonResponse({
            'labels': labels,
            'users': users
        })

    def payment_status_api(self, request):
        """API endpoint for payment status distribution"""
        start_date, end_date = self.get_date_range(request)
        hotel_filter = self.get_hotel_filter(request)
        
        bookings_qs = Booking.objects.filter(booking_date__range=(start_date, end_date))
        if hotel_filter:
            bookings_qs = bookings_qs.filter(room__hotel=hotel_filter)
        
        status_data = list(
            bookings_qs.values('payment_status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        labels = [item['payment_status'] for item in status_data]
        data = [item['count'] for item in status_data]
        
        return JsonResponse({
            'labels': labels,
            'data': data
        })

    def room_types_chart_api(self, request):
        """API endpoint for room types chart data"""
        start_date, end_date = self.get_date_range(request)
        hotel_filter = self.get_hotel_filter(request)
        
        bookings_qs = Booking.objects.filter(booking_date__range=(start_date, end_date))
        if hotel_filter:
            bookings_qs = bookings_qs.filter(room__hotel=hotel_filter)
        
        room_type_data = list(
            bookings_qs.values('room__room_type')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        labels = [item['room__room_type'] for item in room_type_data]
        data = [item['count'] for item in room_type_data]
        
        return JsonResponse({
            'labels': labels,
            'data': data
        })

    def top_hotels_api(self, request):
        """API endpoint for top hotels data"""
        start_date, end_date = self.get_date_range(request)
        
        hotels_data = []
        hotels = Hotel.objects.all()
        
        for hotel in hotels:
            bookings = Booking.objects.filter(
                room__hotel=hotel,
                booking_date__range=(start_date, end_date),
                payment_status__in=['Paid', 'Processing']
            )
            
            bookings_count = bookings.count()
            revenue = bookings.aggregate(total=Sum('total'))['total'] or 0
            total_rooms = Room.objects.filter(hotel=hotel).count()
            
            hotels_data.append({
                'name': hotel.name,
                'bookings': bookings_count,
                'revenue': float(revenue),
                'total_rooms': total_rooms,
                'views': getattr(hotel, 'view_count', 0),  # Assuming you have a view_count field
                'is_featured': getattr(hotel, 'is_featured', False),  # Assuming you have an is_featured field
            })
        
        # Sort by revenue and get top 10
        hotels_data.sort(key=lambda x: x['revenue'], reverse=True)
        
        return JsonResponse({
            'hotels': hotels_data[:10]
        })

    def recent_bookings_api(self, request):
        """API endpoint for recent bookings data"""
        recent_bookings = Booking.objects.select_related('hotel', 'user').order_by('-booking_date')[:20]
        
        bookings_data = []
        for booking in recent_bookings:
            bookings_data.append({
                'id': booking.id,
                'guest_name': f"{booking.user.first_name} {booking.user.last_name}" if booking.user else "Unknown",
                'hotel_name': booking.hotel.name if booking.hotel else "Unknown",
                'amount': float(booking.total),
                'status': booking.payment_status,
                'created_at': booking.booking_date.isoformat(),
            })
        
        return JsonResponse({
            'bookings': bookings_data
        })

    # Export methods (placeholder implementations)
    def export_pdf(self, request):
        from django.http import HttpResponse
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="hotel_report.pdf"'
        # Implement PDF generation here
        response.write(b"PDF export not implemented yet")
        return response

    def export_excel(self, request):
        from django.http import HttpResponse
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="hotel_report.xlsx"'
        # Implement Excel generation here
        response.write(b"Excel export not implemented yet")
        return response

    def export_csv(self, request):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="hotel_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Hotel', 'Bookings', 'Revenue', 'Status'])
        
        # Add sample data
        hotels = Hotel.objects.all()
        for hotel in hotels:
            bookings_count = Booking.objects.filter(room__hotel=hotel).count()
            revenue = Booking.objects.filter(room__hotel=hotel, payment_status='Paid').aggregate(Sum('total'))['total'] or 0
            writer.writerow([hotel.name, bookings_count, revenue, hotel.status])
        
        return response

    # Keep your existing API methods
    def booking_stats_api(self, request):
        today = timezone.now().date()
        start_date = timezone.make_aware(datetime.datetime.combine(today.replace(day=1, month=1), datetime.time.min))
        end_date = timezone.make_aware(datetime.datetime.combine(today, datetime.time.max))

        revenue = Booking.objects.filter(payment_status__in=['Paid', 'Processing']).aggregate(total_revenue=Sum('total'))['total_revenue'] or 0

        monthly_data = (
            Booking.objects.filter(booking_date__range=(start_date, end_date), payment_status__in=['Paid', 'Processing'])
            .annotate(month=TruncMonth('booking_date'))
            .values('month')
            .annotate(count=Count('id'), revenue=Sum('total'))
            .order_by('month')
        )

        bookings_by_month = [
            {
                'month': entry['month'].strftime('%Y-%m'),
                'month_name': entry['month'].strftime('%B %Y'),
                'count': entry['count'],
                'revenue': float(entry['revenue'] or 0)
            } for entry in monthly_data
        ]

        status_distribution = dict(
            Booking.objects.values_list('status').annotate(count=Count('id'))
        )

        top_hotels = (
            Booking.objects.filter(payment_status__in=['Paid', 'Processing'])
            .values('room__hotel__name')
            .annotate(total=Count('id'))
            .order_by('-total')[:5]
        )

        return JsonResponse({
            'total_revenue': float(revenue),
            'bookings_by_month': bookings_by_month,
            'status_distribution': status_distribution,
            'top_hotels': list(top_hotels)
        })

    def user_stats_api(self, request):
        today = timezone.now().date()
        start_date = today.replace(day=1, month=1)
        end_date = today

        monthly_data = (
            CustomUser.objects.filter(date_joined__range=(start_date, end_date))
            .annotate(month=TruncMonth('date_joined'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        users_by_month = [
            {
                'month': entry['month'].strftime('%Y-%m'),
                'month_name': entry['month'].strftime('%B %Y'),
                'count': entry['count']
            } for entry in monthly_data
        ]

        total_users = CustomUser.objects.count()
        joined_this_year = CustomUser.objects.filter(date_joined__range=(start_date, end_date)).count()
        retention_rate = round((joined_this_year / total_users) * 100, 2) if total_users else 0

        return JsonResponse({
            'users_by_month': users_by_month,
            'retention_rate': retention_rate
        })

    def hotel_distribution_api(self, request):
        hotels_per_location = (
            Hotel.objects.values('location')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return JsonResponse({
            'hotels_per_location': list(hotels_per_location)
        })

    def room_type_distribution_api(self, request):
        rooms_by_type = (
            Room.objects.values('room_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return JsonResponse({
            'rooms_by_type': list(rooms_by_type)
        })


custom_admin_site = CustomAdminSite(name='custom_admin')