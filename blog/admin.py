from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from hitcount.models import HitCount

from .models import BlogCategory, BlogPost, BlogComment

class HitCountInline(GenericTabularInline):
    ct_fk_field = "object_pk"
    model = HitCount
    extra = 0
    readonly_fields = ('hits',)

@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [HitCountInline,]

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_email', 'category', 'is_published', 'published_at', 'created_at')
    list_filter = ('category', 'is_published', 'author', 'created_at', 'published_at')
    search_fields = ('title', 'slug', 'content', 'author__email', 'author__first_name', 'author__last_name')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_published',)
    readonly_fields = ('created_at', 'updated_at') # 'published_at' is auto-set by model logic
    date_hierarchy = 'published_at' # Adds date navigation drill-down
    actions = ['publish_posts', 'unpublish_posts']
    inlines = [HitCountInline,]
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'category')
        }),
        ("محتوا و تصویر", {
            'fields': ('content', 'image', 'tags')
        }),
        ("وضعیت انتشار", {
            'fields': ('is_published', 'published_at') # published_at is often best left to model logic or read-only
        }),
        ("زمانبندی", {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def author_email(self, obj):
        if obj.author:
            return obj.author.email
        return "-"
    author_email.short_description = "ایمیل نویسنده"
    author_email.admin_order_field = 'author__email'

    def publish_posts(self, request, queryset):
        queryset.update(is_published=True)
        # Potentially call .save() on each if published_at logic needs to trigger for existing null dates
        # for post in queryset: post.save() 
    publish_posts.short_description = "انتشار پست های انتخاب شده"

    def unpublish_posts(self, request, queryset):
        queryset.update(is_published=False, published_at=None) # Model logic should handle published_at=None
    unpublish_posts.short_description = "لغو انتشار پست های انتخاب شده"

@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ('post_title', 'commenter_info', 'comment_summary', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'post__category')
    search_fields = ('comment', 'name', 'email', 'user__email', 'post__title')
    list_editable = ('status',)
    actions = ['approve_comments', 'reject_comments', 'mark_pending']
    readonly_fields = ('post', 'user', 'name', 'email', 'created_at', 'admin_accepted_by')
    list_per_page = 25

    fieldsets = (
        ("اطلاعات اصلی دیدگاه", {
            'fields': ('post', 'user', 'name', 'email', 'status', 'created_at', 'admin_accepted_by')
        }),
        ("متن دیدگاه", {
            'fields': ('comment',)
        }),
    )

    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = "عنوان پست"
    post_title.admin_order_field = 'post__title'

    def commenter_info(self, obj):
        if obj.user:
            return obj.user.email
        return f"{obj.name} (مهمان)"
    commenter_info.short_description = "نظر دهنده"

    def comment_summary(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
    comment_summary.short_description = "خلاصه دیدگاه"

    def approve_comments(self, request, queryset):
        queryset.update(status=BlogComment.STATUS_APPROVED, admin_accepted_by=request.user)
    approve_comments.short_description = "تایید کردن دیدگاه های انتخاب شده"

    def reject_comments(self, request, queryset):
        queryset.update(status=BlogComment.STATUS_REJECTED, admin_accepted_by=request.user)
    reject_comments.short_description = "رد کردن دیدگاه های انتخاب شده"

    def mark_pending(self, request, queryset):
        queryset.update(status=BlogComment.STATUS_PENDING, admin_accepted_by=None)
    mark_pending.short_description = "علامت گذاری به عنوان در انتظار تایید"
