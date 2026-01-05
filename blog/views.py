from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.views import View
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from datetime import datetime
from django.http import JsonResponse, Http404
from django.utils.decorators import method_decorator
from django.core.files.storage import default_storage
from django.views.decorators.cache import cache_page
from hitcount.views import HitCountDetailView, HitCountMixin
from hitcount.utils import get_hitcount_model

from .models import BlogPost, BlogCategory, BlogComment
from .forms import BlogCommentForm

import os


class BlogListView(ListView, HitCountMixin):
    model = BlogPost
    template_name = 'blog/blog_list.html'
    context_object_name = 'posts'
    paginate_by = 12
    object = None

    count_hit = True

    def get_queryset(self):
        queryset = BlogPost.objects.select_related("author", "category").filter(
            is_published=True, published_at__lte=timezone.now()
            ).order_by('published_at')
        category_slug = self.kwargs.get('category_slug')

        if category_slug:
            # Fetch the current category, eagerly loading its parent to avoid additional queries
            self.current_category = get_object_or_404(BlogCategory.objects.select_related('parent'), slug=category_slug)
            # Filter posts by the current category and all its descendants
            category_ids = self.current_category.get_descendants(include_self=True).values_list('id', flat=True)
            queryset = queryset.filter(category_id__in=category_ids).order_by('published_at')
            self.object = self.current_category  # Set object for hitcount
        else:
            self.current_category = None
            self.object = None # No specific category object for hitcount on all posts page

        return queryset.order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Hitcount logic for categories (if a category is being viewed)
        if self.object: # self.object will be a BlogCategory if category_slug is present
            hit_count = get_hitcount_model().objects.get_for_object(self.object)
            hits = hit_count.hits
            context['hitcount'] = {'pk': hit_count.pk}

            if self.count_hit:
                hit_count_response = self.hit_count(self.request, hit_count)
                if hit_count_response.hit_counted:
                    hits = hits + 1
                context['hitcount']['hit_counted'] = hit_count_response.hit_counted
                context['hitcount']['hit_message'] = hit_count_response.hit_message

            context['hitcount']['total_hits'] = hits
        else:
            context['hitcount'] = None # No hitcount for the "all posts" page itself

        context['SHOP_NAME'] = settings.SHOP_NAME

        context['current_category'] = self.current_category
        # Get all categories as cached trees for efficient display in the sidebar
        # This reduces N+1 queries when traversing children in the template.
        context['categories'] = BlogCategory.objects.get_cached_trees()
        return context

# for the csrf token handle on adding a comment, caching went to the template.
# @method_decorator(cache_page(43200, cache="blog", key_prefix="blog_post"), name="dispatch")
class BlogDetailView(HitCountDetailView):
    model = BlogPost
    template_name = 'blog/blog_detail.html'
    context_object_name = 'post'
    slug_url_kwarg = 'slug' # Matches the slug parameter in urls.py

    count_hit = True

    def get_queryset(self):
        # Ensure only published posts are accessible directly via URL
        return BlogPost.objects.filter(is_published=True, published_at__lte=timezone.now()).select_related('author', 'category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        context['ALLOW_ANONYMOUS_COMMENTS_BLOG'] = settings.ALLOW_ANONYMOUS_COMMENTS_BLOG

        post = self.get_object()
        context['comments'] = post.comments.filter(status=BlogComment.STATUS_APPROVED).select_related('user').order_by('created_at')
        context['comment_form'] = BlogCommentForm(user=self.request.user)

        # MPTT categories can be traversed directly in the template using .get_ancestors()
        return context

class AddBlogCommentView(View):
    form_class = BlogCommentForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and not settings.ALLOW_ANONYMOUS_COMMENTS_BLOG:
            messages.error(request, "برای ثبت نظر اول باید وارد شوید.")
            post_slug = self.kwargs.get('post_slug')
            return redirect(reverse('blog:post_detail', kwargs={'slug': post_slug}) + '#comments')
        if request.user.is_authenticated and (not request.user.email or not request.user.get_full_name):
            messages.error(request, "برای ثبت نظر باید ایمیل و اسم و فامیل را در پروفایل خود وارد کنید.")
            post_slug = self.kwargs.get('post_slug')
            return redirect(reverse('blog:post_detail', kwargs={'slug': post_slug}) + '#comments')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        post_slug = self.kwargs.get('post_slug')
        post = get_object_or_404(BlogPost, slug=post_slug, is_published=True)
        form = self.form_class(request.POST, user=request.user)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            if request.user.is_authenticated:
                comment.user = request.user
                comment.name = request.user.get_full_name or request.user.username
                comment.email = request.user.email

            comment.save()
            messages.success(request, "دیدگاه شما ثبت شد و پس از تایید، نمایش داده خواهد شد.")
            return redirect(reverse('blog:post_detail', kwargs={'slug': post_slug}) + '#comments')
        else:
            # Add form errors to messages and redirect back
            for field, errors in form.errors.items():
                for error in errors:
                    # Try to get the field's verbose name for a friendlier message
                    field_label = form.fields.get(field).label if form.fields.get(field) else field
                    error_message = f"خطا در فیلد «{field_label}»: {error}"
                    messages.error(self.request, error_message)
            return redirect(reverse('blog:post_detail', kwargs={'slug': post_slug}) + '#comment-form')


class CKeditorUplodeBlogImage(View):

    permission_required = 'core.CKeditor_Uplode_Blog_image'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm(self.permission_required):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        uploaded_file = request.FILES.get('upload')
        if uploaded_file:
            now = datetime.now()
            date_path = now.strftime('%Y_%m_%d')
            upload_path = os.path.join('ck_editor/blog_uplodeimage', f"{date_path}___{str(uploaded_file.name)}")

            saved_path = default_storage.save(upload_path, uploaded_file)
            file_url = default_storage.url(saved_path)

            return JsonResponse({'url': file_url})

        return JsonResponse({'error': {'message': 'درخواست نامعتبر است'}}, status=400)

