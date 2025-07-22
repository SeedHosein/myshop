from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.contenttypes.fields import GenericRelation
# from ckeditor.fields import RichTextField # Old import
from django_ckeditor_5.fields import CKEditor5Field # New import for CKEditor 5
from hitcount.models import HitCountMixin, HitCount

class StaticPage(models.Model, HitCountMixin):
    title = models.CharField(max_length=200, verbose_name="عنوان صفحه")
    slug = models.SlugField(max_length=220, unique=True, allow_unicode=True, 
                            help_text="این نامک در URL صفحه استفاده میشود. فقط از حروف، اعداد، خط تیره و زیرخط استفاده کنید.",
                            verbose_name="نامک (Slug)")
    content = CKEditor5Field(verbose_name="محتوای صفحه", config_name="blog")
    is_published = models.BooleanField(default=True, verbose_name="منتشر شده؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    
    hit_count_generic = GenericRelation(
        HitCount, object_id_field='object_pk',
        related_query_name='hit_count_generic_relation'
    )

    class Meta:
        verbose_name = "صفحه ایستا"
        verbose_name_plural = "صفحات ایستا"
        ordering = ['title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        # Ensure slug is unique, though the field definition already enforces this at DB level upon final save.
        # You might add more sophisticated unique slug generation here if needed (e.g., appending a number).
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('static_pages:static_page_detail', kwargs={'slug': self.slug})
