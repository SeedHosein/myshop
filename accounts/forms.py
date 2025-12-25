# This is a new file: accounts/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm #, UserCreationForm, UserChangeForm (UserCreationForm not used directly here)
from django.core.exceptions import ValidationError
# from django.utils.translation import gettext_lazy as _ # No longer needed
from .models import UserProfile

class UserRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        label="آدرس ایمیل یا شماره موبایل",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': "مثال: user@example.com یا 09123456789"})
    )
    first_name = forms.CharField(label="نام", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="نام خانوادگی", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="رمز عبور باید حداقل ۸ کاراکتر باشد."
    )
    password_confirm = forms.CharField(
        label="تکرار رمز عبور",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserProfile
        fields = ('username', 'first_name', 'last_name')
        # Add Persian labels for model fields if not using custom form fields for them
        labels = {
            'username': "آدرس ایمیل یا شماره موبایل",
            'first_name': "نام",
            'last_name': "نام خانوادگی",
        }

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise ValidationError("رمزهای عبور وارد شده یکسان نیستند.")
        if len(password or "") < 8: # Ensure password is not None before checking length
            raise ValidationError("رمز عبور باید حداقل ۸ کاراکتر باشد.")
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="ایمیل یا شماره تلفن همراه",
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'})
    )
    password = forms.CharField(
        label="رمز عبور",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}),
    )

class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(label="نام", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="نام خانوادگی", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    national_code = forms.CharField(label="کد ملی", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(label="آدرس", required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    city = forms.CharField(label="شهر", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    postal_code = forms.CharField(label="کد پستی", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = (
            'first_name', 'last_name',
            'national_code', 'address', 'city', 'postal_code'
        )
        # Since model field verbose_names are already Persian, explicit labels here might be redundant
        # but providing them for clarity and to ensure they are indeed Persian.
        labels = {
            'first_name': "نام",
            'last_name': "نام خانوادگی",
            'national_code': "کد ملی",
            'address': "آدرس",
            'city': "شهر",
            'postal_code': "کد پستی",
        }
        widgets = {
            # Ensure widgets defined here also align with Persian UI if needed, but usually class is sufficient
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    # Not strictly necessary to override __init__ if fields are defined directly with Persian labels.
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['first_name'].label = "نام"
    #     self.fields['last_name'].label = "نام خانوادگی"
    #     self.fields['national_code'].label = "کد ملی"
    #     self.fields['address'].label = "آدرس"
    #     self.fields['city'].label = "شهر"
    #     self.fields['postal_code'].label = "کد پستی"

# For password change, Django's built-in PasswordChangeForm is usually sufficient
# as it works with the active user. We will use it directly in the PasswordChangeView.

# For password reset, Django's built-in PasswordResetForm (finds user by email)
# and SetPasswordForm (sets new password) are used by the CBVs.
# PasswordResetForm will work because our UserProfile has a unique email field. 