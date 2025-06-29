from django.urls import path
from . import views # Assuming you might have views later

app_name = 'core'

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
] 