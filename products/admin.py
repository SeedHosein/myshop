from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from hitcount.models import HitCount
from .models import (
    Category,
    Product,
    ProductImage,
    ProductVariant,
    ProductVideo,
    ProductAttribute,
    ProductAttributeValue
)

class HitCountInline(GenericTabularInline):
    ct_fk_field = "object_pk"
    model = HitCount
    extra = 0
    readonly_fields = ('hits',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'id')
    search_fields = ('name', 'description', 'parent')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [HitCountInline,]
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'parent')}),
        ("توضیحات و تصویر", {'fields': ('image', 'description')}),
    )

class ProductImageInline(admin.TabularInline):
    """Inline for managing product images."""
    model = ProductImage
    extra = 1  
    fields = ('image', 'alt_text', 'is_main')
    verbose_name = "تصویر محصول"
    verbose_name_plural = "تصاویر محصول"


class ProductVideoInline(admin.TabularInline):
    """Inline for managing product videos."""
    model = ProductVideo
    extra = 1  
    fields = ('video_url', 'title')
    verbose_name = "ویدیو محصول"
    verbose_name_plural = "ویدیوهای محصول"


class ProductVariantInline(admin.TabularInline):
    """Inline for managing product variants."""
    model = ProductVariant
    extra = 1 
    fields = ('attribute_values', 'sku', 'price_override', 'stock', 'is_active')
    verbose_name = "تنوع محصول"
    verbose_name_plural = "تنوع‌های محصول"
    
    autocomplete_fields = ('attribute_values',)
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category', 'price', 'stock', 'is_active', 'product_type', 'created_at')
    list_filter = ('is_active', 'product_type', 'category', 'created_at')
    search_fields = ('name', 'description_short', 'description_full')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVideoInline, ProductVariantInline, HitCountInline]
    
    list_editable = ('price', 'stock', 'is_active')
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
            'fields': ('is_active', 'product_type', 'downloadable_file')
        }),
        # ("ویژگی های محصول", {
        #     'fields': ('attribute_values',) # Assuming 'attribute_values' is the M2M field name
        # }),
    )
    # If Product has M2M to ProductAttributeValue:
    # filter_horizontal = ('attribute_values',) 

class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1
    fields = ('attribute', 'value') 

@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    """Admin configuration for ProductAttribute model."""
    list_display = ('name', 'display_name')
    search_fields = ('name', 'display_name')
    inlines = [ProductAttributeValueInline]

@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    """Admin configuration for ProductAttributeValue model."""
    list_display = ('__str__', 'attribute', 'value')
    list_filter = ('attribute',)
    search_fields = ('value', 'attribute__name', 'attribute__display_name')

# ProductImage and ProductVideo are handled by inlines in ProductAdmin,
# but can be registered separately if direct admin access is needed.
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text', 'is_main', 'uploaded_at')
    list_filter = ('is_main', 'product')
    search_fields = ('product', 'alt_text')

@admin.register(ProductVideo)
class ProductVideoAdmin(admin.ModelAdmin):
    list_display = ('product', 'video_url', 'title', 'added_at')
    list_filter = ('product', 'added_at')
