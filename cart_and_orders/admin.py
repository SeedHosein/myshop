from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0 # Don't show extra empty forms for existing carts
    fields = ('is_saved_for_later', 'product', 'quantity', 'added_at', 'get_total_price')
    readonly_fields = ('added_at', 'get_total_price')

    def get_total_price(self, obj):
        return obj.get_total_price()
    get_total_price.short_description = "مجموع قیمت آیتم (تومان)"

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at', 'total_items', 'total_price')
    search_fields = ('user__email', 'user__phone_number')
    readonly_fields = ('created_at', 'updated_at', 'total_items', 'total_price')
    inlines = [CartItemInline]

    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = "تعداد کل آیتم ها"

    def total_price(self, obj):
        return obj.total_price
    total_price.short_description = "مجموع قیمت سبد (تومان)"

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0 # Don't show extra empty forms for existing orders
    readonly_fields = ('product', 'quantity', 'price_at_purchase', 'product_name_at_purchase', 'get_total_price')

    def get_total_price(self, obj):
        return obj.get_total_price()
    get_total_price.short_description = "مجموع قیمت آیتم (تومان)"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'user_display', 'order_date', 'total_amount', 
        'status', 'is_paid', 'shipping_city'
    )
    list_filter = ('status', 'is_paid', 'order_date', 'shipping_city')
    search_fields = (
        'order_number', 'user__email', 'user__phone_number', 'user__first_name', 'user__last_name',
        'shipping_name', 'shipping_address', 'shipping_city', 'shipping_postal_code',
        'billing_name', 'billing_phone'
    )
    readonly_fields = ('order_number', 'user', 'order_date', 'total_amount', 'payment_id') # Make some fields read-only in detail view
    inlines = [OrderItemInline]
    list_per_page = 25

    fieldsets = (
        ("اطلاعات اصلی سفارش", {
            'fields': ('order_number', 'user', 'order_date', 'total_amount', 'status', 'is_paid')
        }),
        ("اطلاعات پرداخت", {
            'fields': ('payment_method', 'payment_id')
        }),
        ("اطلاعات ارسال", {
            'classes': ('collapse',),
            'fields': ('shipping_name', 'shipping_phone', 'shipping_address', 'shipping_city', 'shipping_postal_code')
        }),
        ("اطلاعات صورتحساب", {
            'classes': ('collapse',),
            'fields': ('billing_name', 'billing_phone', 'billing_address', 'billing_city', 'billing_postal_code')
        }),
        ("یادداشت مشتری", {
            'fields': ('notes',)
        }),
    )

    def user_display(self, obj):
        if obj.user:
            return obj.user.email # Or any other identifying field from UserProfile
        return "مهمان"
    user_display.short_description = "کاربر"

# Simple registration for CartItem and OrderItem if direct access is ever needed (usually managed via inlines)
# @admin.register(CartItem)
# class CartItemAdmin(admin.ModelAdmin):
#     list_display = ('cart', 'product', 'quantity', 'is_saved_for_later')

# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ('order', 'product', 'quantity', 'price_at_purchase')
