from django.contrib import admin
from .models import ShopInformation

# Register your models here.
@admin.register(ShopInformation)
class ShopInformationAdmin(admin.ModelAdmin):
    list_display = ('name', 'value',)
    search_fields = ('name', 'value')
