from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.core.validators import RegexValidator
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email or phone number is the unique identifier for 
    authentication instead of username.
    """
    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        """
        Create and save a user with the given email or phone number and password.
        """
        if not email and not phone_number:
            raise ValueError('Email or phone number must be entered.')
            
        if not password:
            raise ValueError('A password must be entered.')

        if email:
            email = self.normalize_email(email)
            extra_fields.setdefault('email', email)

        if phone_number:
            extra_fields.setdefault('phone_number', phone_number)
            

        user = self.model(**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, phone_number=None, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email or phone number and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser باید is_staff=True داشته باشد.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser باید is_superuser=True داشته باشد.')

        if email and phone_number:
            return self.create_user(email=email, phone_number=phone_number, password=password, **extra_fields)
        else: 
            raise ValueError('ایجاد Superuser نیازمند ایمیل یا شماره موبایل است.')


phone_validator = RegexValidator(r"^\+989\d{9}$")

class UserProfile(AbstractUser):
    username = None

    email = models.EmailField(
        'آدرس ایمیل', 
        unique=True, 
        blank=True, 
        null=True,
        help_text='. فرمت: name@domain.com'
    )
    phone_number = models.CharField(
        'شماره موبایل',
        max_length=15,
        validators=[phone_validator],
        unique=True, 
        blank=True,
        null=True,
        help_text='. فرمت: 09xxxxxxxxx یا +989xxxxxxxxx'
    )

    national_code = models.CharField('کد ملی', max_length=10, unique=True, blank=True, null=True)
    address = models.TextField('آدرس', blank=True, null=True)
    city = models.CharField('شهر', max_length=100, blank=True, null=True)
    postal_code = models.CharField('کد پستی', max_length=20, blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        verbose_name='گروه‌ها',
        blank=True,
        help_text=(
            'گروه‌هایی که این کاربر به آن‌ها تعلق دارد. یک کاربر تمام مجوزهای '
            'اعطا شده به هر یک از گروه‌های خود را دریافت خواهد کرد.'
        ),
        related_name="user_profile_groups",
        related_query_name="user_profile",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='مجوزهای کاربر',
        blank=True,
        help_text='مجوزهای خاص برای این کاربر.',
        related_name="user_profile_permissions",
        related_query_name="user_profile",
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']

    objects = CustomUserManager()
    
    def save(self, **kwargs):
        if not self.email and not self.phone_number:
            raise ValueError('Email or phone number must be set.')
        if self.phone_number:
            if self.phone_number[:-9] in ['09', '989', '9']:
                self.phone_number = "+989" + self.phone_number[-9:]
            if len(self.phone_number) != 13 and self.phone_number[:-9] != "+989":
                raise ValidationError('Mobile number is invalid.')
                
        return super().save(**kwargs)

    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل‌های کاربران'

    def __str__(self):
        if self.phone_number:
            return self.phone_number
        return self.email

    @property
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()
    
    @property
    def get_short_name(self):
        if self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return f'کاربر {settings.SHOP_NAME}'
