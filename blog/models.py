from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from django.contrib.contenttypes.fields import GenericRelation
# from ckeditor.fields import RichTextField # Old import
from django_ckeditor_5.fields import CKEditor5Field # New import for CKEditor 5
from hitcount.models import HitCountMixin, HitCount

class BlogCategory(models.Model, HitCountMixin):
    name = models.CharField(max_length=100, unique=True, verbose_name="نام دسته بندی وبلاگ")
    slug = models.SlugField(max_length=120, unique=True, allow_unicode=True, verbose_name="اسلاگ (نامک)")
    
    hit_count_generic = GenericRelation(
        HitCount, object_id_field='object_pk',
        related_query_name='hit_count_generic_relation'
    )

    class Meta:
        verbose_name = "دسته بندی وبلاگ"
        verbose_name_plural = "دسته بندی های وبلاگ"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class BlogPost(models.Model, HitCountMixin):
    title = models.CharField(max_length=255, verbose_name="عنوان پست")
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True, help_text="به صورت خودکار از عنوان ساخته میشود.", verbose_name="اسلاگ (نامک)")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Keep post if author is deleted, or models.PROTECT
        null=True,
        related_name='blog_posts',
        verbose_name="نویسنده"
    )
    content = CKEditor5Field(config_name="blog", verbose_name="محتوای پست")
    
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True, verbose_name="تصویر شاخص پست")
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
        verbose_name="دسته بندی"
    )
    tags = models.CharField(max_length=255, blank=True, help_text="کلمات کلیدی را با کاما (,) جدا کنید.", verbose_name="برچسب ها")
    
    published_at = models.DateTimeField(blank=True, null=True, verbose_name="تاریخ انتشار")
    is_published = models.BooleanField(default=False, verbose_name="منتشر شده؟")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    
    hit_count_generic = GenericRelation(
        HitCount, object_id_field='object_pk',
        related_query_name='hit_count_generic_relation'
    )

    class Meta:
        verbose_name = "پست وبلاگ"
        verbose_name_plural = "پست های وبلاگ"
        ordering = ['-published_at', '-created_at'] # Order by publish date, then creation date

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        # If is_published is set to True and published_at is not set, set published_at to now
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        # If is_published is set to False, clear published_at
        elif not self.is_published:
            self.published_at = None
        super().save(*args, **kwargs)

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})


class BlogComment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    COMMENT_STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار تایید"),
        (STATUS_APPROVED, "تایید شده"),
        (STATUS_REJECTED, "رد شده"),
    ]

    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments', verbose_name="پست مربوطه")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Keep comment if user is deleted, but mark as guest-like
        null=True,
        blank=True, # Allow anonymous comments
        verbose_name="کاربر (اگر عضو باشد)"
    )
    name = models.CharField(max_length=100, verbose_name="نام (برای مهمانان)") # Required if user is None
    email = models.EmailField(verbose_name="ایمیل (برای مهمانان, نمایش داده نمیشود)") # Required if user is None, not shown publicly
    comment = models.TextField(verbose_name="متن دیدگاه")
    status = models.CharField(
        max_length=10,
        choices=COMMENT_STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="وضعیت دیدگاه"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت دیدگاه")
    admin_accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_blog_comments',
        verbose_name="تایید شده توسط ادمین"
    )

    class Meta:
        verbose_name = "دیدگاه وبلاگ"
        verbose_name_plural = "دیدگاه های وبلاگ"
        ordering = ['-created_at']

    def __str__(self):
        return f"دیدگاه از طرف {self.name if self.name else self.user.email} روی پست \"{self.post.title}\"."

    def save(self, *args, **kwargs):
        if self.user:
            self.name = self.user.get_full_name() or self.user.email # Or however you get user's display name
            self.email = self.user.email
        super().save(*args, **kwargs)
