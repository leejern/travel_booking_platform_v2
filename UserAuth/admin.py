from django.contrib import admin
from django.utils.html import mark_safe
from .models import User,Profile

# Register your models here.

class UserModdel(admin.ModelAdmin):
   
    search_fields = ['full_name','username','email']
    list_display = ['username','email','phone']


class ProfileModel(admin.ModelAdmin):
    model = Profile
    search_fields = ['full_name','user__username']
    list_display = ['full_name','image_img','user','verified','phone']
    def image_img(self, obj):
        if obj.image:
            return mark_safe('<img src="%s" width="50px" height="50px"style="border-radius:10px" />' % obj.image.url)
        else:
            return '(Sin imagen)'

    image_img.short_description = 'Thumb'
    image_img.allow_tags = True



admin.site.register(User,UserModdel)
admin.site.register(Profile,ProfileModel)