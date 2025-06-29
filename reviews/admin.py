from django.contrib import admin
from .models import ProductReview

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'user_email', 'rating', 'comment_summary', 'status', 'created_at')
    list_filter = ('status', 'rating', 'created_at', 'product__category')
    search_fields = ('comment', 'user__email', 'user__phone_number', 'user__first_name', 'user__last_name', 'product__name')
    list_editable = ('status',)
    actions = ['approve_reviews', 'reject_reviews', 'mark_pending']
    readonly_fields = ('product', 'user', 'created_at') # Review content itself (rating, comment) should be editable by admin
    list_per_page = 25

    fieldsets = (
        ("اطلاعات اصلی", {
            'fields': ('product', 'user', 'rating', 'status', 'created_at')
        }),
        ("متن نظر", {
            'fields': ('comment',)
        }),
    )

    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = "نام محصول"
    product_name.admin_order_field = 'product__name' # Allows sorting by product name

    def user_email(self, obj):
        if obj.user:
            return obj.user.email
        return "-"
    user_email.short_description = "ایمیل کاربر"
    user_email.admin_order_field = 'user__email'

    def comment_summary(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
    comment_summary.short_description = "خلاصه نظر"

    def approve_reviews(self, request, queryset):
        queryset.update(status=ProductReview.STATUS_APPROVED)
    approve_reviews.short_description = "تایید کردن نقدهای انتخاب شده"

    def reject_reviews(self, request, queryset):
        queryset.update(status=ProductReview.STATUS_REJECTED)
    reject_reviews.short_description = "رد کردن نقدهای انتخاب شده"

    def mark_pending(self, request, queryset):
        queryset.update(status=ProductReview.STATUS_PENDING)
    mark_pending.short_description = "علامت گذاری به عنوان در انتظار تایید"
