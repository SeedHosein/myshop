from django.urls import path
from . import views

app_name = 'static_pages'

urlpatterns = [
    path('<slug:slug>/', views.StaticPageView.as_view(), name='static_page_detail'),
] 