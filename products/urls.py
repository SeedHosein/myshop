from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('search/', views.ProductListView.as_view(), name='product_search_page'), # For non-AJAX search result page
    path('category/<category_slug>/', views.ProductListView.as_view(), name='category_detail'),
    path('product/<slug>', views.ProductDetailView.as_view(), name='product_detail'),
    path('api/search/', views.ProductSearchAPIView.as_view(), name='product_search_api'),
] 