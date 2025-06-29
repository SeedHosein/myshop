from django.contrib import admin
from .models import Discount, Campaign
# from django.utils.translation import gettext_lazy as _ # No longer needed

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'discount_type',
        'value',
        'is_active',
        'start_date',
        'end_date',
        'min_cart_amount'
    )
    list_filter = ('is_active', 'discount_type', 'start_date', 'end_date')
    search_fields = ('name', 'code')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'discount_type', 'value')
        }),
        ("فعالیت و مدت زمان", {
            'fields': ('is_active', 'start_date', 'end_date')
        }),
        ("شرایط", {
            'fields': ('min_cart_amount',)
        }),
    )

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('name', 'description')
    filter_horizontal = ('products',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description',)
        }),
        ("فعالیت و مدت زمان", {
            'fields': ('is_active', 'start_date', 'end_date')
        }),
        ("محصولات مرتبط", {
            'fields': ('products',)
        }),
        # If you add banner_image to the model:
        # ("تصاویر", {
        #     'fields': ('banner_image',)
        # }),
    )
