from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.views import View
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone

from .models import BlogPost, BlogCategory, BlogComment
from .forms import BlogCommentForm

class BlogListView(ListView):
    model = BlogPost
    template_name = 'blog/blog_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = BlogPost.objects.filter(is_published=True)
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            self.category = get_object_or_404(BlogCategory, slug=category_slug)
            queryset = queryset.filter(category=self.category)
        else:
            self.category = None
        return queryset.order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = BlogCategory.objects.all()
        return context

class BlogDetailView(DetailView):
    model = BlogPost
    template_name = 'blog/blog_detail.html'
    context_object_name = 'post'
    slug_url_kwarg = 'slug' # Matches the slug parameter in urls.py

    def get_queryset(self):
        # Ensure only published posts are accessible directly via URL
        return BlogPost.objects.filter(is_published=True, published_at__lte=timezone.now()).select_related('author', 'category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
