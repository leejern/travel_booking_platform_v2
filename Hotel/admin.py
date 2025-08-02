
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
from .reports import ReportsAdminMixim
from .custom_admin import CustomAdminSite, custom_admin_site

# Register your models here.

class HotelStatusFilter(admin.SimpleListFilter):
    title = _('Hotel Status')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('active', _('Active Hotels')),
            ('featured', _('Featured Hotels')),
            ('new', _('New Hotels (Last 30 days)')),
            ('popular', _('Popular Hotels (High Views)')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(status='Live', user__isnull=False)
        if self.value() == 'featured':
            return queryset.filter(featured=True, status='Live')
        if self.value() == 'new':
            thirty_days_ago = date.today() - timedelta(days=30)
            return queryset.filter(date__gte=thirty_days_ago)
        if self.value() == 'popular':
            return queryset.filter(views__gte=100)

class BookingDateFilter(admin.SimpleListFilter):
    title = _('Booking Period')
    parameter_name = 'booking_period'

    def lookups(self, request, model_admin):
        return (
            ('today', _('Today')),
            ('week', _('This Week')),
            ('month', _('This Month')),
            ('upcoming', _('Upcoming Check-ins')),
            ('active', _('Active Stays')),
        )

    def queryset(self, request, queryset):
        today = date.today()
        if self.value() == 'today':
            return queryset.filter(booking_date__date=today)
        if self.value() == 'week':
            week_start = today - timedelta(days=today.weekday())
            return queryset.filter(booking_date__date__gte=week_start)
        if self.value() == 'month':
            return queryset.filter(booking_date__year=today.year, booking_date__month=today.month)
        if self.value() == 'upcoming':
            return queryset.filter(checkin_date__gte=today, checkin_date__lte=today + timedelta(days=7))
        if self.value() == 'active':
            return queryset.filter(checkin_date__lte=today, checkout_date__gte=today, check_in=True, check_out=False)

# Inline admin classes
class HotelGalleryInline(admin.TabularInline):
    model = HotelGallery
    extra = 1
    fields = ('image', 'caption', 'is_primary', 'order')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" style="object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = "Preview"


class HotelFeatureInline(admin.TabularInline):
    model = HotelFeatures
    extra = 1
    fields = ('name', 'icon_type', 'icon', 'description')


class HotelFaqInline(admin.TabularInline):
    model = HotelFaqs
    extra = 1
    fields = ('question', 'answer', 'order')


class RoomTypeInline(admin.TabularInline):
    model = RoomType
    extra = 0
    fields = ('type', 'price', 'number_of_beds', 'max_occupancy', 'rooms_count_display')
    readonly_fields = ('rooms_count_display',)
    
    def rooms_count_display(self, obj):
        if obj.pk:
            count = obj.rooms_count()
            return f"{count} rooms"
        return "Save to see room count"
    rooms_count_display.short_description = "Rooms"


class RoomInline(admin.TabularInline):
    model = Room
    extra = 0
    fields = ('room_number', 'room_type', 'floor', 'is_available', 'maintenance_mode')
    list_filter = ('is_available', 'maintenance_mode')


# Main admin classes
@admin.register(Hotel)
class HotelAdmin(ReportsAdminMixim,admin.ModelAdmin):
    inlines = [HotelGalleryInline, HotelFeatureInline, HotelFaqInline, RoomTypeInline, RoomInline]
    
    list_display = [
        'thumbnail', 'name', 'user', 'city', 'status', 'featured', 
        'views', 'rooms_count_display', 'bookings_count_display', 'rating_display', 'date'
    ]
    list_filter = [HotelStatusFilter, 'status', 'featured', 'city', 'date']
    search_fields = ['name', 'city', 'address', 'email', 'mobile', 'user__username']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('views',  'rating_display', 'date', 'updated')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'slug', 'description', 'image') 
        }),
        ('Contact & Location', {
            'fields': ('email', 'mobile', 'address', 'city', 'state', 'country', 'latitude', 'longitude')
        }),
        ('Settings', {
            'fields': ('status', 'featured', 'tags')
        }),
        ('Statistics', {
            'fields': ('views', 'date', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['make_featured', 'remove_featured', 'activate_hotels', 'deactivate_hotels']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user').prefetch_related('rooms', 'reviews')
    
    def rooms_count_display(self, obj):
        count = obj.rooms.count()
        url = reverse('admin:Hotel_room_changelist') + f'?hotel__id__exact={obj.id}'
        return format_html('<a href="{}">{} rooms</a>', url, count)
    rooms_count_display.short_description = "Rooms"
    rooms_count_display.admin_order_field = 'rooms__count'
    
    def bookings_count_display(self, obj):
        count = obj.booking_set.count()
        url = reverse('admin:Hotel_booking_changelist') + f'?hotel__id__exact={obj.id}'
        return format_html('<a href="{}">{} bookings</a>', url, count)
    bookings_count_display.short_description = "Bookings"
    
    def rating_display(self, obj):
        avg_rating = obj.average_rating()
        if avg_rating:
            stars = "⭐" * int(avg_rating)
            return f"{stars} ({avg_rating:.1f})"
        return "No ratings"
    rating_display.short_description = "Rating"
    
    def make_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} hotels marked as featured.')
    make_featured.short_description = "Mark selected hotels as featured"
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} hotels removed from featured.')
    remove_featured.short_description = "Remove featured status"
    
    def activate_hotels(self, request, queryset):
        updated = queryset.update(status='Live')
        self.message_user(request, f'{updated} hotels activated.')
    activate_hotels.short_description = "Activate selected hotels"
    
    def deactivate_hotels(self, request, queryset):
        updated = queryset.update(status='Disabled')
        self.message_user(request, f'{updated} hotels deactivated.')
    deactivate_hotels.short_description = "Deactivate selected hotels"

@admin.register(HotelGallery)
class HotelGalleryAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'hotel', 'caption', 'is_primary', 'order']
    list_filter = ['is_primary', 'hotel']
    search_fields = ['hotel__name', 'caption']
    list_editable = ['is_primary', 'order', 'caption']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" style="object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = "Preview"


@admin.register(HotelFeatures)
class HotelFeaturesAdmin(admin.ModelAdmin):
    list_display = ['name', 'hotel', 'icon_type', 'icon']
    list_filter = ['icon_type', 'hotel']
    search_fields = ['name', 'hotel__name']


@admin.register(HotelFaqs)
class HotelFaqsAdmin(admin.ModelAdmin):
    list_display = ['question_short', 'hotel', 'order', 'date']
    list_filter = ['hotel', 'date']
    search_fields = ['question', 'answer', 'hotel__name']
    list_editable = ['order']
    
    def question_short(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_short.short_description = "Question"


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'type', 'price', 'number_of_beds', 'max_occupancy', 'rooms_count_display']
    list_filter = ['hotel', 'number_of_beds']
    search_fields = ['type', 'hotel__name']
    prepopulated_fields = {'slug': ('type',)}
    readonly_fields = ('rooms_count_display',)
    
    def rooms_count_display(self, obj):
        count = obj.rooms_count()
        if count > 0:
            url = reverse('admin:Hotel_room_changelist') + f'?room_type__id__exact={obj.id}'
            return format_html('<a href="{}">{} rooms</a>', url, count)
        return f"{count} rooms"
    rooms_count_display.short_description = "Rooms Count"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'hotel', 'room_type', 'floor', 'is_available', 'maintenance_mode', 'current_booking']
    list_filter = ['is_available', 'maintenance_mode', 'hotel', 'room_type', 'floor']
    search_fields = ['room_number', 'hotel__name', 'room_type__type']
    list_editable = ['is_available', 'maintenance_mode']
    
    def current_booking(self, obj):
        today = date.today()
        current_booking = Booking.objects.filter(
            room=obj,
            checkin_date__lte=today,
            checkout_date__gte=today,
            payment_status__in=['Paid', 'Processing']
        ).first()
        
        if current_booking:
            url = reverse('admin:Hotel_booking_change', args=[current_booking.pk])
            return format_html('<a href="{}">Booking #{}</a>', url, current_booking.booking_id)
        return "Available"
    current_booking.short_description = "Current Status"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_id', 'fullname', 'hotel', 'room_type', 'payment_status', 
        'checkin_date', 'checkout_date', 'total', 'booking_date', 'status_display'
    ]
    list_filter = [BookingDateFilter, 'payment_status', 'check_in', 'check_out', 'hotel', 'room_type']
    search_fields = ['booking_id', 'fullname', 'email', 'phone', 'hotel__name']
    readonly_fields = ['booking_id', 'success_id', 'booking_date', 'total_days']
    date_hierarchy = 'booking_date'
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_id', 'success_id', 'booking_date', 'payment_status')
        }),
        ('Guest Information', {
            'fields': ('user', 'fullname', 'email', 'phone')
        }),
        ('Stay Details', {
            'fields': ('hotel', 'room_type', 'room', 'checkin_date', 'checkout_date', 'total_days')
        }),
        ('Guest Count', {
            'fields': ('num_adults', 'num_children')
        }),
        ('Pricing', {
            'fields': ('before_discount', 'total', 'saved', 'coupons')
        }),
        ('Status Tracking', {
            'fields': ('check_in', 'check_out', 'is_active', 'check_in_tracker', 'check_out_tracker')
        }),
        ('Payment Details', {
            'fields': ('stripe_payment_intent', 'payment_id'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_paid', 'mark_as_cancelled', 'check_in_guests', 'check_out_guests']
    
    def status_display(self, obj):
        today = date.today()
        if obj.check_out:
            return format_html('<span style="color: green;">✓ Completed</span>')
        elif obj.check_in and obj.checkin_date <= today <= obj.checkout_date:
            return format_html('<span style="color: blue;">🏨 Active Stay</span>')
        elif obj.checkin_date > today:
            return format_html('<span style="color: orange;">📅 Upcoming</span>')
        elif obj.checkout_date < today and not obj.check_out:
            return format_html('<span style="color: red;">⚠ Overdue</span>')
        return "Pending"
    status_display.short_description = "Status"
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(payment_status='Paid')
        self.message_user(request, f'{updated} bookings marked as paid.')
    mark_as_paid.short_description = "Mark as paid"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(payment_status='Cancelled', is_active=False)
        self.message_user(request, f'{updated} bookings cancelled.')
    mark_as_cancelled.short_description = "Cancel bookings"
    
    def check_in_guests(self, request, queryset):
        updated = queryset.update(check_in=True, check_in_tracker=True)
        self.message_user(request, f'{updated} guests checked in.')
    check_in_guests.short_description = "Check in guests"
    
    def check_out_guests(self, request, queryset):
        updated = queryset.update(check_out=True, check_out_tracker=True)
        self.message_user(request, f'{updated} guests checked out.')
    check_out_guests.short_description = "Check out guests"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'hotel', 'rating_stars', 'title', 'is_verified', 'date']
    list_filter = ['rating', 'is_verified', 'date', 'hotel']
    search_fields = ['user__username', 'hotel__name', 'title', 'comment']
    readonly_fields = ['date']
    
    def rating_stars(self, obj):
        return "⭐" * obj.rating
    rating_stars.short_description = "Rating"


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_display', 'active', 'valid_from', 'valid_to', 'redemptions', 'max_redemptions', 'is_valid_now']
    list_filter = ['active', 'type', 'valid_from', 'valid_to']
    search_fields = ['code']
    readonly_fields = ['redemptions', 'date', 'cid']
    
    def discount_display(self, obj):
        if obj.type == 'Percentage':
            return f"{obj.discount}%"
        return f"${obj.discount}"
    discount_display.short_description = "Discount"
    
    def is_valid_now(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Invalid</span>')
    is_valid_now.short_description = "Current Status"


@admin.register(GuestActivityLog)
class GuestActivityLogAdmin(admin.ModelAdmin):
    list_display = ['booking', 'guest_out', 'guest_in', 'date']
    list_filter = ['date', 'booking__hotel']
    search_fields = ['booking__fullname', 'booking__booking_id', 'description']
    readonly_fields = ['date']


@admin.register(StaffOnDuty)
class StaffOnDutyAdmin(admin.ModelAdmin):
    list_display = ['staff_id', 'Booking', 'date']
    list_filter = ['date', 'Booking__hotel']
    search_fields = ['staff_id', 'Booking__booking_id', 'Booking__fullname']
    readonly_fields = ['date']


@admin.register(Notifications)
class NotificationsAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'seen', 'date']
    list_filter = ['type', 'seen', 'date']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['date']
    actions = ['mark_as_seen', 'mark_as_unseen']
    
    def mark_as_seen(self, request, queryset):
        updated = queryset.update(seen=True)
        self.message_user(request, f'{updated} notifications marked as seen.')
    mark_as_seen.short_description = "Mark as seen"
    
    def mark_as_unseen(self, request, queryset):
        updated = queryset.update(seen=False)
        self.message_user(request, f'{updated} notifications marked as unseen.')
    mark_as_unseen.short_description = "Mark as unseen"


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'hotel', 'date']
    list_filter = ['date', 'hotel']
    search_fields = ['user__username', 'hotel__name']
    readonly_fields = ['bid', 'date']


# Custom admin site configuration
admin.site.site_header = "Hotel Management System"
admin.site.site_title = "Hotel Admin"
admin.site.index_title = "Welcome to Hotel Management System"

# Add some custom styling
admin.site.enable_nav_sidebar = True

# custom admin site

# register all your models with the custom admin site
custom_admin_site.register(Hotel, HotelAdmin)
custom_admin_site.register(HotelGallery, HotelGalleryAdmin)
custom_admin_site.register(HotelFeatures, HotelFeaturesAdmin)
custom_admin_site.register(HotelFaqs, HotelFaqsAdmin)
custom_admin_site.register(RoomType, RoomTypeAdmin)
custom_admin_site.register(Room, RoomAdmin)
custom_admin_site.register(Booking, BookingAdmin)
custom_admin_site.register(Coupon, CouponAdmin)
custom_admin_site.register(GuestActivityLog, GuestActivityLogAdmin)
custom_admin_site.register(StaffOnDuty, StaffOnDutyAdmin)
custom_admin_site.register(Notifications, NotificationsAdmin)
custom_admin_site.register(Bookmark, BookmarkAdmin)