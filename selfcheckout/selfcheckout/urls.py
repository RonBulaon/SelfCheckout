"""selfcheckout URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.urls import path
from django.conf import settings               
from django.conf.urls.static import static     

from checkout import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.step1, name='step1'),
    path('book/<str:item_barcode>/', views.step2, name='step2'),
    path('patron/<str:patron_id>/', views.step3, name='step3'),
    path('code/<str:patron_code>/', views.step4, name='step4'),
]
