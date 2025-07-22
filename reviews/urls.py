from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('product/<product_slug>/review/add/', views.AddReviewView.as_view(), name='add_review'),
    # Add other review-related URLs here if needed
]
