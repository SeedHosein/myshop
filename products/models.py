from random import randint
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.contenttypes.fields import GenericRelation
# from ckeditor.fields import RichTextField # Old import
from django_ckeditor_5.fields import CKEditor5Field # New import for CKEditor 5
from hitcount.models import HitCountMixin, HitCount

# Tip: Consider adding a base model with created_at and updated_at if many models need them.
# For now, we'll add them directly to the Product model.

class Category(models.Model, HitCountMixin):
    name = models.CharField(max_length=255, verbose_name="نام دسته")
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True, verbose_name="اسلاگ (نامک)")
    description = CKEditor5Field(blank=True, null=True, verbose_name="توضیحات", config_name="blog")
    image = models.ImageField(upload_to='category_images/', verbose_name="تصویر دسته")
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,  # Or models.CASCADE if subcategories should be deleted with parent
        null=True,
        blank=True,
        related_name='children',
        verbose_name="دسته والد"
    )
    
    hit_count_generic = GenericRelation(
        HitCount, object_id_field='object_pk',
        related_query_name='hit_count_generic_relation'
    )

    class Meta:
        verbose_name = "دسته بندی"
        verbose_name_plural = "دسته بندی ها"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    # Optional: Add a method to get the absolute URL for a category
    def get_absolute_url(self):
        return reverse('products:category_detail', kwargs={'category_slug': self.slug})


class ProductAttribute(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="نام ویژگی (مثلا: رنگ، سایز)")
    display_name = models.CharField(max_length=150, verbose_name="نام نمایشی ویژگی (برای کاربر)")

    class Meta:
        verbose_name = "ویژگی محصول"
        verbose_name_plural = "ویژگی های محصول"
        ordering = ['name']

    def __str__(self):
        return self.display_name


class ProductAttributeValue(models.Model):
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name="نوع ویژگی"
    )
    value = models.CharField(max_length=100, verbose_name="مقدار ویژگی (مثلا: قرمز، XL)")
    # You might add a 'slug' or 'code' here if needed for filtering or specific logic

    class Meta:
        verbose_name = "مقدار ویژگی محصول"
        verbose_name_plural = "مقادیر ویژگی های محصول"
        ordering = ['attribute__name', 'value']
        unique_together = ('attribute', 'value') # Each value should be unique for a given attribute type

    def __str__(self):
        return f"{self.attribute.display_name}: {self.value}"


class Product(models.Model, HitCountMixin):
    PHYSICAL = 'physical'
    DOWNLOADABLE = 'downloadable'
    PRODUCT_TYPE_CHOICES = [
        (PHYSICAL, "فیزیکی"),
        (DOWNLOADABLE, "دانلودی"),
    ]

    name = models.CharField(max_length=255, verbose_name="نام محصول")
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True, verbose_name="اسلاگ (نامک)")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,  # Prevent deleting a category if products are linked
        related_name='products',
        verbose_name="دسته بندی"
    )
    description_short = models.CharField(max_length=250, verbose_name="توضیحات کوتاه")
    description_full = CKEditor5Field(config_name="product", verbose_name="توضیحات کامل / نقد و بررسی")
    attribute_values = models.ManyToManyField(ProductAttributeValue, blank=True, related_name='products', verbose_name="مشخصات فنی")
    price = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="قیمت (تومان)")
    discounted_price = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="قیمت با تخفیف (تومان)"
    )
    stock = models.PositiveIntegerField(default=0, verbose_name="موجودی انبار")
    is_active = models.BooleanField(default=True, verbose_name="فعال / نمایش داده شود؟")

    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        default=PHYSICAL,
        verbose_name="نوع محصول"
    )
    downloadable_file = models.FileField(
        upload_to='product_files/',
        blank=True,
        null=True,
        verbose_name="فایل قابل دانلود"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    # Add more fields as needed, e.g., brand, SKU, weight (for physical), file version (for downloadable)
    
    hit_count_generic = GenericRelation(
        HitCount, object_id_field='object_pk',
        related_query_name='hit_count_generic_relation'
    )

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ['-created_at'] # Show newest products first

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        # Ensure downloadable_file is cleared if product_type is not 'downloadable'
        if self.product_type != self.DOWNLOADABLE:
            self.downloadable_file = None
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})

    @property
    def get_display_price(self):
        if self.discounted_price:
            return self.discounted_price
        return self.price

    def get_main_image(self):
        return self.images.filter(is_main=True).first()

    def get_main_image_url(self):
        return self.images.filter(is_main=True).first().image.url


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE, # If product is deleted, its images are also deleted
        related_name='images',
        verbose_name="محصول"
    )
    image = models.ImageField(upload_to='product_images/', verbose_name="تصویر")
    alt_text = models.CharField(max_length=255, blank=True, null=True, verbose_name="متن جایگزین (Alt Text)")
    is_main = models.BooleanField(default=False, verbose_name="تصویر اصلی؟")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ آپلود")

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصول"
        ordering = ['-is_main', 'uploaded_at'] # Main image first, then by upload date

    def __str__(self):
        return f"تصویر برای {self.product.name} ({'اصلی' if self.is_main else 'فرعی'})"

    def save(self, *args, **kwargs):
        # If this image is being set as the main one,
        # ensure no other images for the same product are main.
        if self.is_main:
            # Select all other ProductImage objects for the same product that are is_main=True
            other_main_images = ProductImage.objects.filter(product=self.product, is_main=True).exclude(pk=self.pk)
            # And set their is_main to False
            other_main_images.update(is_main=False)
        
        super().save(*args, **kwargs)


class ProductVideo(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='videos',
        verbose_name="محصول"
    )
    video_url = models.URLField(max_length=500, verbose_name="URL ویدیو (مثلا لینک یوتیوب)")
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name="عنوان ویدیو")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ افزودن")

    class Meta:
        verbose_name = "ویدیو محصول"
        verbose_name_plural = "ویدیوهای محصول"
        ordering = ['added_at']

    def __str__(self):
        return f"ویدیو برای {self.product.name} - {self.title if self.title else self.video_url}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="محصول اصلی")
    attribute_values = models.ManyToManyField(ProductAttributeValue, related_name='variants', verbose_name="مقادیر ویژگی")
    sku = models.CharField(max_length=400, unique=True, blank=True, null=True, verbose_name="SKU")
    price_override = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True, verbose_name="قیمت جایگزین (تومان)")
    stock = models.PositiveIntegerField(default=0, verbose_name="موجودی انبار")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    is_deleted = False
    ri = str(randint(10000000,99999999))

    class Meta:
        verbose_name = "تنوع محصول"
        verbose_name_plural = "تنوع های محصولات"

    def __str__(self):
        if self.is_deleted or not self.pk:
            return f"{self.product.name}-(None)"
        values = ",".join([f"{val.attribute.name}:{val.value}" for val in self.attribute_values.all()])
        return f"{self.product.name}-({values if values else "None"})"
    
    @property
    def get_attribute_values_value(self):
        if self.is_deleted:
            return f"None"
        values = " ".join([f"{val.value}" for val in self.attribute_values.all()]) if self.pk else ""
        return f"{values if values else f"None{self.ri}"}"
    
    @property
    def get_variant_name(self):
        if self.is_deleted:
            return f"None"
        values = " ".join([f"{val.attribute.name}:{val.value}" for val in self.attribute_values.all()]) if self.pk else ""
        return f"{values if values else f"None{self.ri}"}"
    
    @property
    def product_variant_name(self):
        if self.is_deleted:
            return f"{self.product.name}-(None)"
        values = ",".join([f"{val.attribute.name}:{val.value}" for val in self.attribute_values.all()]) if self.pk else ""
        return f"{self.product.name}-({values if values else f"None{self.ri}"})"

    @property
    def get_price(self):
        if self.price_override is not None:
            return self.price_override
        return self.product.get_display_price

    def save(self, *args, **kwargs):
        """
        Overrides save to clean the SKU and auto-generate if needed.
        """
        if self.sku:
            self.sku = self.sku.replace(' ', '-')
        super().save(*args, **kwargs)
        
        
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        
        super().delete(*args, **kwargs)

