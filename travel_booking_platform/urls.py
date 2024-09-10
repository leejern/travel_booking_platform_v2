"""
URL configuration for travel_booking_platform project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from Hotel import views as hotel_views
from django.conf import settings


from django.conf.urls.static import static


urlpatterns = [ 
    path('admin_tools_stats/', include('admin_tools_stats.urls')),
    path('admin/', admin.site.urls),
    path("",hotel_views.home,name="home"),

    # custom urls
    # userauth urls
    path('user/',include("UserAuth.urls")),

    # hotel ursl
    path('',include("Hotel.urls")),

    # booking ursl
    path('booking/',include("booking.urls")),

    # booking ursl
    path('dashboard/',include("User_dashboard.urls")),


    # ckeditor ursl
    path('ckeditor5/',include("django_ckeditor_5.urls")),


    
]

urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)


urlpatterns += staticfiles_urlpatterns()