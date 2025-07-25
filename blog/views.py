from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.views import View
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from datetime import datetime
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.http import Http404
from hitcount.views import HitCountDetailView, HitCountMixin
from hitcount.utils import get_hitcount_model

from core.models import ShopInformation

from .models import BlogPost, BlogCategory, BlogComment
from .forms import BlogCommentForm

import os

class BlogListView(ListView, HitCountMixin):
    model = BlogPost
    template_name = 'blog/blog_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    object = None
    
    count_hit = True

    def get_queryset(self):
        queryset = BlogPost.objects.filter(is_published=True)
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            self.category = get_object_or_404(BlogCategory, slug=category_slug)
            self.object = self.category
            queryset = queryset.filter(category=self.category)
        else:
            self.category = None
        return queryset.order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
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

        
        context['SHOP_NAME'] = settings.SHOP_NAME
        context['ShopInformation'] = ShopInformation.objects.all()
        
        context['category'] = self.category
        context['categories'] = BlogCategory.objects.all()
        return context

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
        context['ShopInformation'] = ShopInformation.objects.all()
        
        post = self.get_object()
        context['comments'] = post.comments.filter(status=BlogComment.STATUS_APPROVED).select_related('user').order_by('created_at')
        context['comment_form'] = BlogCommentForm(user=self.request.user)
        # Optional: Add related posts or other context
        # context['related_posts'] = BlogPost.objects.filter(category=post.category, is_published=True).exclude(pk=post.pk)[:3]
        return context

class AddBlogCommentView(View):
    form_class = BlogCommentForm

    def post(self, request, *args, **kwargs):
        post_slug = self.kwargs.get('post_slug')
        post = get_object_or_404(BlogPost, slug=post_slug, is_published=True)
        form = self.form_class(request.POST, user=request.user)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            if request.user.is_authenticated:
                comment.user = request.user
                comment.name = request.user.get_full_name() or request.user.username
                comment.email = request.user.email
            
            comment.save()
            messages.success(request, "دیدگاه شما ثبت شد و پس از تایید نمایش داده خواهد شد.")
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
        
        