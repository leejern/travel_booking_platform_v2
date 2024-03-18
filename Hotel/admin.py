from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
import django.forms as forms

from .models import *
# Register your models here.

class HotelGalleryinline(admin.TabularInline):
    model = HotelGallery

class HotelFeatureinline(admin.TabularInline):
    model = HotelFeatures

class HotelFaqinline(admin.TabularInline):
    model = HotelFaqs

class HotelRoomTypeinline(admin.TabularInline):
    model = RoomType

class HotelRoominline(admin.TabularInline):
    model = Room


class HotelAdmin(admin.ModelAdmin):
    inlines=[HotelGalleryinline,HotelFeatureinline,HotelFaqinline,HotelRoomTypeinline,HotelRoominline]
    list_display = ['thumbnail', 'name', 'mobile', 'status', 'views']
    list_filter = ['user',]
    search_fields=['name', 'mobile', 'status', ]
    prepopulated_fields = {'slug':('name',)}



class RoomTypeAdmin(admin.ModelAdmin):
    list_display= ['hotel','type','price']
    prepopulated_fields = {'slug':('type',)}

class CouponAdmin(admin.ModelAdmin):
    list_display = ['code','active','type','discount','valid_from','valid_to','redemptions']

admin.site.register(Hotel,HotelAdmin)
admin.site.register(HotelGallery)
admin.site.register(HotelFeatures)
admin.site.register(HotelFaqs)
admin.site.register(RoomType,RoomTypeAdmin)
admin.site.register(Room)
admin.site.register(Booking)
admin.site.register(GuestActivityLog)
admin.site.register(StaffOnDuty)
admin.site.register(Notifications)
admin.site.register(Coupon,CouponAdmin)


