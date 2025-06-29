from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile

# To display custom fields in the user admin, we need to customize UserAdmin
@admin.register(UserProfile)
class UserProfileAdmin(BaseUserAdmin):
    # Fields to display in the list view
    list_display = ('email', 'phone_number', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'date_joined')
    search_fields = ('email', 'phone_number', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    # Define fieldsets for the add/change forms
    # This largely mirrors the default UserAdmin fieldsets but uses email/phone
    fieldsets = (
        (None, {'fields': ('email', 'phone_number', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'national_code', 'address', 'city', 'postal_code')}),
        ('دسترسی‌ها', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('تاریخ‌های مهم', {'fields': ('last_login', 'date_joined')}),
    )

    # For the add user form (createsuperuser might behave differently)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'password'), # Assuming password handling is appropriate for add form
        }),
        ('اطلاعات شخصی (اختیاری)', {
            'classes': ('collapse',),
            'fields': ('first_name', 'last_name', 'national_code'),
        }),
        ('دسترسی‌ها (اختیاری)', {
            'classes': ('collapse',),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
    )

    # Since we removed username, we need to tell UserAdmin which fields to use
    # for ordering, search, etc., if they were based on 'username'.
    # Our USERNAME_FIELD is 'email'.

    # If you have custom forms for creating/changing users, specify them here:
    # form = UserProfileChangeForm
    # add_form = UserProfileCreationForm

    # Ensure that read-only fields like date_joined and last_login are shown correctly.
    readonly_fields = ('last_login', 'date_joined')

    # In a real project, you would define UserProfileChangeForm and UserProfileCreationForm
    # that inherit from UserChangeForm and UserCreationForm respectively, and point to your UserProfile model.
    # For now, this setup should work for basic admin management.

# Note: If you don't unregister the default User model (if it was ever registered before setting AUTH_USER_MODEL),
# you might see two "Users" sections. But with AUTH_USER_MODEL set early, this shouldn't be an issue.
# from django.contrib.auth.models import User
# admin.site.unregister(User) # Only if User was somehow registered and you see duplicates
