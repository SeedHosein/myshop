from django.db import models
# from django.utils.translation import gettext_lazy as _ # No longer needed if hardcoding
from products.models import Product # Assuming Product model is in products.models
from django.utils import timezone

class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'درصدی'),
        ('fixed_amount', 'مبلغ ثابت'),
    ]

    name = models.CharField("نام تخفیف", max_length=255)
    code = models.CharField("کد تخفیف", max_length=50, unique=True, help_text="مثال: SUMMER20, SAVE10000")
    discount_type = models.CharField(
        "نوع تخفیف",
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage'
    )
    value = models.DecimalField(
        "مقدار",
        max_digits=10,
        decimal_places=2,
        help_text="اگر درصدی است، عدد را وارد کنید (مثلاً 10 برای 10%). اگر مبلغ ثابت است، ارزش پولی را وارد کنید."
    )
    is_active = models.BooleanField("فعال است؟", default=True)
    start_date = models.DateTimeField("تاریخ شروع", default=timezone.now)
    end_date = models.DateTimeField("تاریخ پایان")
    min_cart_amount = models.DecimalField(
        "حداقل مبلغ سبد خرید",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="حداقل مبلغ کل در سبد خرید برای اعمال این تخفیف."
    )

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = "تخفیف"
        verbose_name_plural = "تخفیف‌ها"
        ordering = ['-start_date']

class Campaign(models.Model):
    name = models.CharField("نام کمپین", max_length=255)
    description = models.TextField("توضیحات", blank=True, null=True)
    products = models.ManyToManyField(
        Product,
        verbose_name="محصولات مرتبط",
        blank=True, 
        related_name='campaigns'
    )
    start_date = models.DateTimeField("تاریخ شروع", default=timezone.now)
    end_date = models.DateTimeField("تاریخ پایان")
    is_active = models.BooleanField("فعال است؟", default=True)
    # banner_image = models.ImageField("بنر کمپین", upload_to='campaign_banners/', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "کمپین"
        verbose_name_plural = "کمپین‌ها"
        ordering = ['-start_date']

    def get_active_products(self):
        """محصولات فعال مرتبط با این کمپین را برمی‌گرداند."""
        return self.products.filter(is_active=True)
