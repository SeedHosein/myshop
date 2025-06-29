from django.db import models
from django.conf import settings # To refer to the custom user model
# from products.models import Product
from django.core.validators import MinValueValidator, MaxValueValidator

class ProductReview(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    REVIEW_STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار تایید"),
        (STATUS_APPROVED, "تایید شده"),
        (STATUS_REJECTED, "رد شده"),
    ]

    product = models.ForeignKey(
        'products.Product', # String notation
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="محصول"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # If user is deleted, their reviews are deleted
        related_name='reviews',
        verbose_name="کاربر"
    )
    rating = models.PositiveSmallIntegerField(
        verbose_name="امتیاز (از 1 تا 5)",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="امتیاز خود را از 1 (ضعیف) تا 5 (عالی) ستاره انتخاب کنید."
    )
    comment = models.TextField(verbose_name="متن نظر")
    status = models.CharField(
        max_length=10,
        choices=REVIEW_STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="وضعیت"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    # You could add an updated_at field if reviews can be edited
    # updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "نقد و بررسی محصول"
        verbose_name_plural = "نقد و بررسی های محصولات"
        ordering = ['-created_at']
        unique_together = ('product', 'user') # Allow one review per user per product

    def __str__(self):
        return f"نظر کاربر {self.user.email} برای محصول {self.product.name} (امتیاز: {self.rating})"
