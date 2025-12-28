# accounts/forms.py
from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm
)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from .models import UserProfile

# Define a set of common symbols
PASSWORD_SYMBOLS = r"!@#$%^&*()-_+=[]{}\|;:,.<>/?`~"

def validate_complex_password(password):
    """
    Validates that the password contains at least one uppercase letter,
    one lowercase letter, one digit, and one of a few common symbols.
    """
    if len(password) < 8:
        raise ValidationError("این رمز عبور خیلی کوتاه است. باید حداقل ۸ کاراکتر داشته باشد.")
    if not re.search(r'[A-Z]', password):
        raise ValidationError("رمز عبور باید حداقل شامل یک حرف بزرگ انگلیسی باشد.")
    if not re.search(r'[a-z]', password):
        raise ValidationError("رمز عبور باید حداقل شامل یک حرف کوچک انگلیسی باشد.")
    if not re.search(r'\d', password):
        raise ValidationError("رمز عبور باید حداقل شامل یک عدد باشد.")
    if not re.search(r'[' + re.escape(PASSWORD_SYMBOLS) + ']', password):
        raise ValidationError(f"رمز عبور باید حداقل شامل یکی از نمادهای {PASSWORD_SYMBOLS} باشد.")
    if not re.match(r'^[A-Za-z\d' + re.escape(PASSWORD_SYMBOLS) + ']*$', password):
        raise ValidationError(("رمز عبور فقط میتواند از " 
                               "حرف بزرگ و کوچک انگلیسی، " 
                               "اعدد " 
                               f"و نمادهای {PASSWORD_SYMBOLS} تشکیل شود."))


class UserRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        label="آدرس ایمیل یا شماره موبایل",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "مثال: user@example.com یا 09123456789"}),
        required=True,
        error_messages = {"required": "این فیلد الزامی است.",},
    )
    first_name = forms.CharField(
        label="نام",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages = {"required": "این فیلد الزامی است.",},
    )
    last_name = forms.CharField(
        label="نام خانوادگی",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages = {"required": "این فیلد الزامی است.",},
    )
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text= ("رمز عبور شما باید شرایت زیر را داشته باشد:<ul>" 
                    "<li>حداقل شامل ۸ کاراکتر باشد.</li>" 
                    "<li>حداقل دارای یک حرف بزرگ و ک حرف کوچک انگلیسی باشد.</li>" 
                    "<li>حداقل دارای یک عدد باشد.</li>" 
                    f"<li>حداقل دارای یکی از نمادهای {PASSWORD_SYMBOLS} باشد.</li></ul>"),
        error_messages = {"required": "این فیلد الزامی است.",},
    )
    password_confirm = forms.CharField(
        label="تکرار رمز عبور",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        error_messages = {"required": "این فیلد الزامی است.",},
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

    def clean_username(self):
        username = self.cleaned_data.get('username').strip()
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        mobile_regex = r'^\+989\d{9}$'
        
        if self.phone_number[:-9] in ['09', '989', '9']:
            self.phone_number = "+989" + self.phone_number[-9:]

        if re.match(email_regex, username):
            self.input_type = 'email'
            self.destination = username.lower()
            if UserProfile.objects.filter(email=self.destination).exists():
                self.add_error("username", "این ایمیل قبلاً ثبت نام کرده است.")
            return self.destination
        elif re.match(mobile_regex, username):
            self.input_type = 'mobile'
            self.destination = username
            if UserProfile.objects.filter(phone_number=self.destination).exists():
                self.add_error("username", "این شماره موبایل قبلاً ثبت نام کرده است.")
            return self.destination
        else:
            self.add_error("username", "لطفاً ایمیل یا شماره موبایل معتبر وارد کنید.")
        return username
    
    

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            try:
                validate_complex_password(password)
            except ValidationError as e:
                raise e # Re-raise to be caught by Django's form validation
        return password

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "رمزهای عبور وارد شده یکسان نیستند.")

        # Password length validation is now handled by AUTH_PASSWORD_VALIDATORS.
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        # Set email/phone based on detected input_type from clean_username
        if hasattr(self, 'input_type'):
            if self.input_type == 'email':
                user.email = self.destination
                user.phone_number = None # Ensure only one is set as primary username
            elif self.input_type == 'mobile':
                user.phone_number = self.destination
                user.email = None # Ensure only one is set as primary username

        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="آدرس ایمیل یا شماره موبایل",
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}),
        error_messages = {"required": "این فیلد الزامی است."},
    )
    password = forms.CharField(
        label="رمز عبور",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}),
        error_messages = {"required": "این فیلد الزامی است."},
    )

    error_messages = {
        "invalid_login": "نام کاربری (آدرس ایمیل/شماره موبایل) یا رمز عبور اشتباه است.",
        "inactive": "این حساب کاربری غیرفعال است.",
    }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and username[:-9] in ['09', '989', '9']:
            return "+989" + username[-9:]
        return username

class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        label="نام",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages = {"required": "این فیلد الزامی است."},
    )
    last_name = forms.CharField(
        label="نام خانوادگی",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages = {"required": "این فیلد الزامی است."},
    )
    national_code = forms.CharField(
        label="کد ملی",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    address = forms.CharField(
        label="آدرس",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )
    city = forms.CharField(
        label="شهر",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    postal_code = forms.CharField(
        label="کد پستی",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserProfile
        fields = (
            'first_name', 'last_name',
            'national_code', 'address', 'city', 'postal_code'
        )
        labels = {
            'first_name': "نام",
            'last_name': "نام خانوادگی",
            'national_code': "کد ملی",
            'address': "آدرس",
            'city': "شهر",
            'postal_code': "کد پستی",
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control bg-gray-50'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control bg-gray-50'}),
            'national_code': forms.TextInput(attrs={'class': 'form-control bg-gray-50'}),
            'address': forms.Textarea(attrs={'class': 'form-control bg-gray-50', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control bg-gray-50'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control bg-gray-50'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="رمز عبور فعلی",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
        required=True,
        error_messages = {"required": "این فیلد الزامی است."},
    )
    new_password1 = forms.CharField(
        label="رمز عبور جدید",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
        help_text= ("رمز عبور شما باید شرایت زیر را داشته باشد:<ul>" 
                    "<li>حداقل شامل ۸ کاراکتر باشد.</li>" 
                    "<li>حداقل دارای یک حرف بزرگ و ک حرف کوچک انگلیسی باشد.</li>" 
                    "<li>حداقل دارای یک عدد باشد.</li>" 
                    f"<li>حداقل دارای یکی از نمادهای {PASSWORD_SYMBOLS} باشد.</li></ul>"),
        required=True,
        error_messages = {"required": "این فیلد الزامی است."},
    )
    new_password2 = forms.CharField(
        label="تایید رمز عبور جدید",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="لطفاً رمز عبور جدید خود را دوباره وارد کنید.",
        required=True,
        error_messages = {"required": "این فیلد الزامی است."},
    )

    error_messages = {
        "password_mismatch": "رمزهای عبور وارد شده یکسان نیستند.",
        "password_incorrect": "رمز عبور قبلی شما اشتباه وارد شده است. لطفاً دوباره آن را وارد کنید.",
    }

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password:
            try:
                validate_complex_password(password)
            except ValidationError as e:
                raise e # Re-raise to be caught by Django's form validation
        return password


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="آدرس ایمیل",
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'}),
        help_text="ایمیل خود را وارد کنید تا لینک بازیابی رمز عبور برایتان ارسال شود.",
        required=True,
        error_messages = {"required": "این فیلد الزامی است."},
    )

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="رمز عبور جدید",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
        help_text= ("رمز عبور شما باید شرایت زیر را داشته باشد:<ul>" 
                    "<li>حداقل شامل ۸ کاراکتر باشد.</li>" 
                    "<li>حداقل دارای یک حرف بزرگ و ک حرف کوچک انگلیسی باشد.</li>" 
                    "<li>حداقل دارای یک عدد باشد.</li>" 
                    f"<li>حداقل دارای یکی از نمادهای {PASSWORD_SYMBOLS} باشد.</li></ul>"),
        required=True,
        error_messages = {"required": "این فیلد الزامی است."},
    )
    new_password2 = forms.CharField(
        label="تایید رمز عبور جدید",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="لطفاً رمز عبور جدید خود را دوباره وارد کنید.",
        required=True,
        error_messages = {"required": "این فیلد الزامی است."},
    )

    error_messages = {
        "password_mismatch": "رمزهای عبور وارد شده یکسان نیستند.",
    }

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password:
            try:
                validate_complex_password(password)
            except ValidationError as e:
                raise e # Re-raise to be caught by Django's form validation
        return password
