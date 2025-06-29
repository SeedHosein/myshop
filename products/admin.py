from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVideo, ProductAttribute, ProductAttributeValue
# from django.utils.translation import gettext_lazy as _ # No longer needed

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'id')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    # fieldsets = (
    #     (None, {'fields': ('name', 'slug', 'parent')}),
    #     ("توضیحات و تصویر", {'fields': ('description', 'image')}),
    # )

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    # Add fields to display in the inline form, e.g., 'image', 'alt_text', 'is_main'
    fields = ('image', 'alt_text', 'is_main') 
    # readonly_fields = ('image_preview',) # If you add an image_preview method to ProductImage model

class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 1
    fields = ('video_url', 'title')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category', 'price', 'stock', 'is_active', 'product_type', 'created_at')
    list_filter = ('is_active', 'product_type', 'category', 'created_at')
    search_fields = ('name', 'description_short', 'description_full')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVideoInline]
    # Adjust fieldsets based on actual fields and desired grouping in Persian
    fieldsets = (
        ("اطلاعات اصلی", {
            'fields': ('name', 'slug', 'category')
        }),
        ("توضیحات", {
            'fields': ('description_short', 'description_full')
        }),
        ("قیمت و موجودی", {
            'fields': ('price', 'discounted_price', 'stock')
        }),
        ("نوع و وضعیت محصول", {
            'fields': ('product_type', 'downloadable_file', 'is_active')
        }),
        # If you have M2M to ProductAttributeValue on Product model:
        # ("ویژگی های محصول", {
        #     'fields': ('attribute_values',) # Assuming 'attribute_values' is the M2M field name
        # }),
    )
    # If Product has M2M to ProductAttributeValue:
    # filter_horizontal = ('attribute_values',) 

class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1
    # fields = ('attribute', 'value') # This is if ProductAttributeValue is directly linked to Product
                                  # More likely, ProductAttributeValue is global and linked via an intermediary M2M on Product or Variant.
                                  # For now, assuming ProductAttributeValue is generic and might not be directly inlined in ProductAdmin this way.
                                  # Or, if Product has M2M to ProductAttributeValue:
                                  # filter_horizontal = ('attribute_values',) in ProductAdmin

@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name')
    search_fields = ('name', 'display_name')
    # inlines = [ProductAttributeValueInline] # This would be if AttributeValue was an inline TO Attribute, not Product

@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value')
    list_filter = ('attribute',)
    search_fields = ('value', 'attribute__name', 'attribute__display_name')

# ProductImage and ProductVideo are handled by inlines in ProductAdmin,
# but can be registered separately if direct admin access is needed.
# @admin.register(ProductImage)
# class ProductImageAdmin(admin.ModelAdmin):
#     list_display = ('product', 'alt_text', 'is_main', 'uploaded_at')
#     list_filter = ('is_main', 'product')

# @admin.register(ProductVideo)
# class ProductVideoAdmin(admin.ModelAdmin):
#     list_display = ('product', 'title', 'added_at')
#     list_filter = ('product',)
