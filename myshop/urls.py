"""
URL configuration for myshop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("ckeditor5/", include('django_ckeditor_5.urls')), # CKEditor 5 URLS
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('products/', include('products.urls', namespace='products')),
    path('cart/', include('cart_and_orders.urls', namespace='cart_and_orders')),
    path('blog/', include('blog.urls', namespace='blog')),
    path('chat/', include('chat.urls', namespace='chat')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('pages/', include('static_pages.urls', namespace='static_pages')),
    path('reviews/', include('reviews.urls', namespace='reviews')),
    path('', include('core.urls', namespace='core')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
# Optional: Add a simple homepage view directly here or from an app like 'core'
# from django.shortcuts import render
# def home_view(request):
#     return render(request, 'home.html', {})
# urlpatterns.append(path('', home_view, name='home')) 