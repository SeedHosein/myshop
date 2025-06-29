from django.urls import path
from . import views

app_name = 'cart_and_orders'

urlpatterns = [
    path('', views.CartDetailView.as_view(), name='cart_detail'),
    path('add/', views.AddToCartView.as_view(), name='add_to_cart'), # Expects product_id and quantity in POST
    path('remove/<int:item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('update/<int:item_id>/', views.UpdateCartItemQuantityView.as_view(), name='update_cart_item_quantity'),
    path('save-for-later/<int:item_id>/', views.SaveForLaterView.as_view(), name='save_for_later'),
    
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('order-confirmation/', views.OrderConfirmationView.as_view(), name='order_confirmation'),
    path('apply-discount/', views.ApplyDiscountView.as_view(), name='apply_discount'),
] 