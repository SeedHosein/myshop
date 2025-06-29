from django.contrib import admin
from .models import StaticPage

@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'updated_at')
    list_filter = ('is_published',)
    search_fields = ('title', 'slug', 'content')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content')
        }),
        ('Publication', {
            'fields': ('is_published',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # If you want to use the CKEditor widget in the admin for the 'content' field,
    # it should happen automatically because RichTextField uses it by default.
    # For standard TextFields, you might do:
    # from django.db import models
    # from ckeditor.widgets import CKEditorWidget
    # formfield_overrides = {
    #     models.TextField: {'widget': CKEditorWidget}
    # }
