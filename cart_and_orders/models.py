from django.db import models
from django.conf import settings # To refer to the custom user model
from decimal import Decimal
# from django.utils.translation import gettext_lazy as _ # No longer needed
# from products.models import Product # Assuming Product model is in products app

class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name="کاربر"
    ) # Each user has one cart
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    
    applied_discount_code = models.CharField(verbose_name="کد تخفیف اعمال شده", max_length=50, null=True, blank=True)
    discount_amount = models.DecimalField(verbose_name="مبلغ تخفیف (تومان)", max_digits=12, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = "سبد خرید"
        verbose_name_plural = "سبدهای خرید"

    def __str__(self):
        return f"سبد خرید برای {self.user.email if self.user else 'کاربر ناشناس'}"

    @property
    def subtotal_price(self):
        """Total price of active items before any cart-level discount."""
        for item in self.items.filter(is_saved_for_later=False):
            if not item.product.is_active:
                item.delete()
        return sum(item.get_total_price() for item in self.items.filter(is_saved_for_later=False) if item.product and item.product.price is not None)

    @property
    def final_price(self):
        """Final price after applying cart-level discount."""
        return self.subtotal_price - self.discount_amount

    def clear_discount(self):
        self.applied_discount_code = None
        self.discount_amount = Decimal('0.00')
        self.save()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="سبد خرید")
    product = models.ForeignKey(
        'products.Product', # Use string 'app_label.ModelName' to avoid circular imports
        on_delete=models.CASCADE, # Or SET_NULL if you want to keep cart item if product is deleted
        verbose_name="محصول"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="تعداد")
    is_saved_for_later = models.BooleanField(default=False, verbose_name="ذخیره برای بعد؟")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ افزودن")

    class Meta:
        verbose_name = "مورد سبد خرید"
        verbose_name_plural = "موارد سبد خرید"
        unique_together = ('cart', 'product', 'is_saved_for_later') # Avoid duplicate product entries unless for 'saved for later' distinction

    def __str__(self):
        return f"{self.quantity} عدد از {self.product.name} در سبد {self.cart.user.email if self.cart.user else 'ناشناس'}"

    def get_total_price(self):
        if self.product and self.product.price is not None:
            # Assuming get_display_price is a method. If it's a property, use self.product.get_display_price
            # Based on previous context, it was designed as a property.
            if callable(self.product.get_display_price):
                return self.product.get_display_price() * self.quantity
            return self.product.get_display_price * self.quantity 
        return Decimal('0.00')


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELED = 'canceled'

    ORDER_STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار پرداخت"),
        (STATUS_PROCESSING, "در حال پردازش"),
        (STATUS_SHIPPED, "ارسال شده"),
        (STATUS_DELIVERED, "تحویل شده"),
        (STATUS_CANCELED, "لغو شده"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Keep order history even if user is deleted (or PROTECT)
        null=True, # Allows for guest checkouts if implemented later, or for deleted users
        blank=True,
        related_name='orders',
        verbose_name="کاربر"
    )
    order_number = models.CharField(max_length=50, unique=True, blank=True, verbose_name="شماره سفارش")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ سفارش")
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="وضعیت سفارش"
    )
    
    original_total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="مبلغ کل اصلی (قبل از تخفیف)")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="مبلغ تخفیف اعمال شده")
    applied_discount_code = models.CharField(max_length=50, null=True, blank=True, verbose_name="کد تخفیف اعمال شده")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="مبلغ نهایی (تومان)")
    
    # Billing and Shipping information
    # For simplicity, using TextField. For structured data, separate Address model is better.
    billing_name = models.CharField(max_length=255, verbose_name="نام صورتحساب")
    billing_address = models.TextField(verbose_name="آدرس صورتحساب")
    billing_city = models.CharField(max_length=100, verbose_name="شهر صورتحساب")
    billing_postal_code = models.CharField(max_length=20, verbose_name="کد پستی صورتحساب")
    billing_phone = models.CharField(max_length=20, verbose_name="تلفن صورتحساب") # Increased length

    shipping_name = models.CharField(max_length=255, verbose_name="نام گیرنده")
    shipping_address = models.TextField(verbose_name="آدرس تحویل")
    shipping_city = models.CharField(max_length=100, verbose_name="شهر تحویل")
    shipping_postal_code = models.CharField(max_length=20, verbose_name="کد پستی تحویل")
    shipping_phone = models.CharField(max_length=20, verbose_name="تلفن تحویل") # Increased length

    payment_method = models.CharField(max_length=100, blank=True, null=True, verbose_name="روش پرداخت")
    payment_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="شناسه پرداخت") # For transaction ID from payment gateway
    is_paid = models.BooleanField(default=False, verbose_name="پرداخت شده؟")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت مشتری")

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"
        ordering = ['-order_date']

    def __str__(self):
        return f"سفارش {self.order_number or self.id} توسط {self.user.email if self.user else 'مهمان'}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None 
        super().save(*args, **kwargs) 
        if is_new and not self.order_number: 
            from django.utils import timezone
            timestamp_id = timezone.now().strftime('%Y%m%d%H%M%S')
            self.order_number = f"CHK-{timestamp_id}-{self.pk}"
            Order.objects.filter(pk=self.pk).update(order_number=self.order_number)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="سفارش")
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL, # Keep item in order history even if product is deleted, but mark as unavailable
        null=True, # Product might be deleted from catalog later
        verbose_name="محصول"
    )
    quantity = models.PositiveIntegerField(verbose_name="تعداد")
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="قیمت در زمان خرید (تومان)")
    # Store product name/sku as well in case product details change or product is deleted
    product_name_at_purchase = models.CharField(max_length=255, blank=True, null=True, verbose_name="نام محصول در زمان خرید")

    class Meta:
        verbose_name = "مورد سفارش"
        verbose_name_plural = "موارد سفارش"

    def __str__(self):
        product_display_name = self.product.name if self.product else self.product_name_at_purchase
        return f"{self.quantity} عدد از {product_display_name} برای سفارش {self.order.id}"

    def get_total_price(self):
        return self.price_at_purchase * self.quantity
