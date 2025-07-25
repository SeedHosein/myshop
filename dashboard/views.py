from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse # Import reverse for fallback
from django.views.generic import ListView, CreateView, UpdateView, View, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
# from django.utils.translation import gettext_lazy as _ # No longer needed
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied, FieldError
from django.urls import NoReverseMatch # Import NoReverseMatch from django.urls
from django.db.models import Sum, Count, Q, Prefetch
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache

from discounts_and_campaigns.models import Discount, Campaign
from reviews.models import ProductReview # Assuming ProductReview is in reviews.models
# from .forms import DiscountForm, CampaignForm # We'll create these if needed for more complex validation or fields
from cart_and_orders.models import Order, OrderItem
from products.models import Product, Category, ProductImage
from django.conf import settings
from blog.models import BlogPost, BlogCategory, BlogComment
from django.db.models import Prefetch
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
import json
import os, shutil


User = get_user_model()

# --- RBAC Helper Mixins (Optional, but good for complex checks) ---
# This mixin is no longer needed and will be removed.

# --- Discount Management Views ---
class DiscountListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Discount
    template_name = 'dashboard/discount_list.html'
    context_object_name = 'discounts'
    permission_required = 'discounts_and_campaigns.view_discount'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm(self.permission_required):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Discount.objects.all().order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class DiscountCreateUpdateView(LoginRequiredMixin, SuccessMessageMixin, View):
    template_name = 'dashboard/discount_form.html'
    # form_class = DiscountForm # Use if you create a custom form
    model = Discount
    fields = ['name', 'code', 'discount_type', 'value', 'is_active', 'start_date', 'end_date', 'min_cart_amount']
    success_url = reverse_lazy('dashboard:discount_list')

    def get_object(self, pk=None):
        if pk:
            return get_object_or_404(Discount, pk=pk)
        return None

    def get_permission_required(self, instance=None):
        if instance:
            return ('discounts_and_campaigns.change_discount',)
        return ('discounts_and_campaigns.add_discount',)

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object(kwargs.get('pk'))
        perms = self.get_permission_required(instance)
        # Ensure request.user has all permissions in the perms tuple/list
        if not all(request.user.has_perm(p) for p in perms):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk=None):
        instance = self.get_object(pk)
        form_class = self.get_form_class()
        form = form_class(instance=instance)
        context = {'form': form, 'object': instance}
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, self.template_name, context)

    def post(self, request, pk=None):
        instance = self.get_object(pk)
        form_class = self.get_form_class()
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            success_message = "تخفیف با موفقیت ایجاد شد." if not instance else "تخفیف با موفقیت بروزرسانی شد."
            messages.success(request, success_message)
            return redirect(self.success_url)
        context = {'form': form, 'object': instance}
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, self.template_name, context)
    
    def get_form_class(self):
        from django.forms import modelform_factory
        return modelform_factory(self.model, fields=self.fields)

class DiscountDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Discount
    template_name = 'dashboard/confirm_delete.html' # A generic confirmation template
    success_url = reverse_lazy('dashboard:discount_list')
    permission_required = 'discounts_and_campaigns.delete_discount'
    success_message = "تخفیف با موفقیت حذف شد."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

    def post(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().post(request, *args, **kwargs)


# --- Campaign Management Views ---
class CampaignListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Campaign
    template_name = 'dashboard/campaign_list.html'
    context_object_name = 'campaigns'
    permission_required = 'discounts_and_campaigns.view_campaign'
    paginate_by = 20

    def get_queryset(self):
        return Campaign.objects.all().order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class CampaignCreateUpdateView(LoginRequiredMixin, SuccessMessageMixin, View):
    template_name = 'dashboard/campaign_form.html'
    model = Campaign
    fields = ['name', 'description', 'products', 'is_active', 'start_date', 'end_date']
    success_url = reverse_lazy('dashboard:campaign_list')

    def get_object(self, pk=None):
        if pk:
            return get_object_or_404(Campaign, pk=pk)
        return None

    def get_permission_required(self, instance=None):
        if instance:
            return ('discounts_and_campaigns.change_campaign',)
        return ('discounts_and_campaigns.add_campaign',)

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object(kwargs.get('pk'))
        perms = self.get_permission_required(instance)
        # Ensure request.user has all permissions in the perms tuple/list
        if not all(request.user.has_perm(p) for p in perms):
            messages.error(request, "شما اجازه انجام این عملیات را ندارید.")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk=None):
        instance = self.get_object(pk)
        form_class = self.get_form_class()
        form = form_class(instance=instance)
        context = {'form': form, 'object': instance}
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, self.template_name, context)

    def post(self, request, pk=None):
        instance = self.get_object(pk)
        form_class = self.get_form_class()
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            success_message = "کمپین با موفقیت ایجاد شد." if not instance else "کمپین با موفقیت بروزرسانی شد."
            messages.success(request, success_message)
            return redirect(self.success_url)
        context = {'form': form, 'object': instance}
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, self.template_name, context)

    def get_form_class(self):
        from django.forms import modelform_factory
        return modelform_factory(self.model, fields=self.fields)

class CampaignDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Campaign
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboard:campaign_list')
    permission_required = 'discounts_and_campaigns.delete_campaign'
    success_message = "کمپین با موفقیت حذف شد."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

    def post(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().post(request, *args, **kwargs)


# --- Product Management Views ---
class ProductListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Product
    template_name = 'dashboard/product_list.html'
    context_object_name = 'products'
    permission_required = 'products.view_product'
    paginate_by = 20

    def get_queryset(self):
        # Prefetch all images for the products. The get_main_image() method on the model
        # will then use this prefetched data, avoiding N+1 queries.
        return Product.objects.all().order_by('-created_at').prefetch_related('images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class ProductCreateUpdateView(LoginRequiredMixin, SuccessMessageMixin, View):
    template_name = 'dashboard/product_form.html'
    model = Product
    fields = ['category', 'name', 'slug', 'description_short', 'description_full', 'price', 'discounted_price', 'stock', 'is_active', 'product_type', 'downloadable_file']
    success_url = reverse_lazy('dashboard:product_list')

    def get_object(self, pk=None):
        if pk:
            return get_object_or_404(Product, pk=pk)
        return None

    def get_permission_required(self, instance=None):
        if instance:
            return ('products.change_product',)
        return ('products.add_product',)

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object(kwargs.get('pk'))
        perms = self.get_permission_required(instance)
        if not all(request.user.has_perm(p) for p in perms):
            messages.error(request, "شما اجازه انجام این عملیات را ندارید.")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        from django.forms import modelform_factory
        return modelform_factory(self.model, fields=self.fields)

    def get(self, request, pk=None):
        instance = self.get_object(pk)
        form = self.get_form_class()(instance=instance)
        context = {'form': form, 'object': instance}
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, self.template_name, context)

    def post(self, request, pk=None):
        instance = self.get_object(pk)
        form = self.get_form_class()(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            success_message = "محصول با موفقیت ایجاد شد." if not instance else "محصول با موفقیت بروزرسانی شد."
            messages.success(request, success_message)
            return redirect(self.success_url)
        context = {'form': form, 'object': instance}
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, self.template_name, context)

class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Product
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboard:product_list')
    permission_required = 'products.delete_product'
    success_message = "محصول با موفقیت حذف شد."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

    def post(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().post(request, *args, **kwargs)


# --- Order Management Views ---
class OrderListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Order
    template_name = 'dashboard/order_list.html'
    context_object_name = 'orders'
    permission_required = 'cart_and_orders.view_order'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

    def get_queryset(self):
        return Order.objects.all().order_by('-order_date')

class OrderDetailView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Order
    template_name = 'dashboard/order_detail.html'
    context_object_name = 'order'
    permission_required = 'cart_and_orders.change_order'
    fields = ['status']
    success_url = reverse_lazy('dashboard:order_list')

    def get_success_message(self, cleaned_data):
        return f"وضعیت سفارش {self.object.id} با موفقیت به «{self.object.get_status_display()}» تغییر یافت."

    def form_valid(self, form):
        messages.success(self.request, self.get_success_message(form.cleaned_data))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context


# --- Category Management Views ---
class CategoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Category
    template_name = 'dashboard/category_list.html'
    context_object_name = 'categories'
    permission_required = 'products.view_category'
    paginate_by = 30 # Set a higher number for categories

    def get_queryset(self):
        # Fetch all categories, and let the template handle the hierarchy
        return Category.objects.all().order_by('parent__name', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class CategoryCreateUpdateView(LoginRequiredMixin, SuccessMessageMixin, View):
    template_name = 'dashboard/category_form.html'
    model = Category
    fields = ['name', 'slug', 'parent', 'description', 'image']
    success_url = reverse_lazy('dashboard:category_list')

    def get_object(self, pk=None):
        if pk:
            return get_object_or_404(Category, pk=pk)
        return None

    def get_permission_required(self, instance=None):
        if instance:
            return ('products.change_category',)
        return ('products.add_category',)

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object(kwargs.get('pk'))
        perms = self.get_permission_required(instance)
        if not all(request.user.has_perm(p) for p in perms):
            messages.error(request, "شما اجازه انجام این عملیات را ندارید.")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        from django.forms import modelform_factory
        return modelform_factory(self.model, fields=self.fields)

    def get(self, request, pk=None):
        instance = self.get_object(pk)
        form = self.get_form_class()(instance=instance)
        context = {'form': form, 'object': instance}
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, self.template_name, context)

    def post(self, request, pk=None):
        instance = self.get_object(pk)
        form = self.get_form_class()(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            success_message = "دسته بندی با موفقیت ایجاد شد." if not instance else "دسته بندی با موفقیت بروزرسانی شد."
            messages.success(request, success_message)
            return redirect(self.success_url)
        context = {'form': form, 'object': instance}
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, self.template_name, context)

class CategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Category
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboard:category_list')
    permission_required = 'products.delete_category'
    success_message = "دسته بندی با موفقیت حذف شد."

    def post(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().post(request, *args, **kwargs)


# --- User Management Views ---
class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = 'dashboard/user_list.html'
    context_object_name = 'users'
    permission_required = 'auth.view_user'
    paginate_by = 20

    def get_queryset(self):
        return User.objects.all().order_by('email')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    template_name = 'dashboard/user_form.html'
    fields = ['first_name', 'last_name', 'groups']
    success_url = reverse_lazy('dashboard:user_list')
    permission_required = 'auth.change_user'
    success_message = "اطلاعات کاربر با موفقیت بروزرسانی شد."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['groups'].widget = forms.CheckboxSelectMultiple()
        form.fields['groups'].queryset = Group.objects.all()
        return form

    def form_valid(self, form):
        # Get the user being edited
        user_to_edit = form.instance
        requesting_user = self.request.user

        # Get the groups from the form and the user's current groups
        submitted_groups = set(form.cleaned_data['groups'])
        current_groups = set(user_to_edit.groups.all())

        # Determine which groups are being added or removed
        groups_to_add = submitted_groups - current_groups
        groups_to_remove = current_groups - submitted_groups
        
        # Check permissions for group modifications
        is_requester_superuser = requesting_user.is_superuser
        is_requester_owner = requesting_user.groups.filter(name='owner').exists()
        is_requester_admin = requesting_user.groups.filter(name='admin').exists()

        for group in groups_to_add | groups_to_remove:
            if group.name == 'owner':
                if not is_requester_superuser:
                    messages.error(self.request, "فقط کاربر Superuser می‌تواند عضویت در گروه 'Owner' را تغییر دهد.")
                    return redirect(self.get_success_url())
            elif group.name == 'admin':
                if not (is_requester_superuser or is_requester_owner):
                    messages.error(self.request, "فقط کاربر Superuser و اعضای گروه 'Owner' می‌توانند عضویت در گروه 'Admin' را تغییر دهند.")
                    return redirect(self.get_success_url())
            else: # For any other group
                if not (is_requester_superuser or is_requester_owner or is_requester_admin):
                    messages.error(self.request, "شما اجازه تغییر عضویت در این گروه را ندارید.")
                    return redirect(self.get_success_url())

        # If all checks pass, proceed with the default behavior
        messages.success(self.request, self.success_message)
        return super().form_valid(form)


# --- Product Review Management View ---
class ProductReviewManagementView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ProductReview
    template_name = 'dashboard/product_review_management.html'
    context_object_name = 'reviews'
    permission_required = ('reviews.view_productreview', 'reviews.change_productreview')
    paginate_by = 25

    def get_queryset(self):
        # Optionally filter by status, e.g., to show pending reviews first
        status_filter = self.request.GET.get('status', 'all')
        queryset = ProductReview.objects.select_related('product', 'user').order_by('-created_at')
        if status_filter != 'all' and status_filter in [choice[0] for choice in ProductReview.REVIEW_STATUS_CHOICES]:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        
        context['review_statuses'] = ProductReview.REVIEW_STATUS_CHOICES
        context['current_status_filter'] = self.request.GET.get('status', 'all')
        return context

    def post(self, request, *args, **kwargs):
        # Action to approve/reject/pending a review
        review_id = request.POST.get('review_id')
        action = request.POST.get('action') # e.g., 'approve', 'reject', 'pending'

        if not review_id or not action:
            messages.error(request, "درخواست نامعتبر است.")
            return redirect(reverse('dashboard:product_review_management'))

        try:
            review = ProductReview.objects.get(pk=review_id)
        except ProductReview.DoesNotExist:
            messages.error(request, "بررسی مورد نظر یافت نشد.")
            return redirect(reverse('dashboard:product_review_management'))

        # Check permissions again within POST
        if not self.request.user.has_perm('reviews.change_productreview'):
             messages.error(request, "شما اجازه تغییر وضعیت بررسی‌ها را ندارید.")
             return redirect(reverse('dashboard:product_review_management'))


        if action == 'approve':
            review.status = ProductReview.STATUS_APPROVED
            review.save()
            messages.success(request, f"بررسی برای '{review.product.name}' تایید شد.")
        elif action == 'reject':
            review.status = ProductReview.STATUS_REJECTED
            review.save()
            messages.warning(request, f"بررسی برای '{review.product.name}' رد شد.")
        elif action == 'pending':
            review.status = ProductReview.STATUS_PENDING
            review.save()
            messages.info(request, f"وضعیت بررسی برای '{review.product.name}' به حالت معلق تغییر یافت.")
        else:
            messages.error(request, "عملیات نامعتبر است.")

        return redirect(reverse('dashboard:product_review_management'))

# A simple dashboard home view (optional)
class DashboardHomeView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'dashboard/dashboard_home.html'
    permission_required = 'core.view_dashboard'

    def get(self, request, *args, **kwargs):
        # 1. Online Users
        online_users_cache = cache.get('online-users', {})
        guest_users = 0
        logged_in_users = 0
        for user_key, last_seen in online_users_cache.items():
            if isinstance(user_key, int): # Authenticated users have integer IDs
                logged_in_users += 1
            else: # Guests have session keys (strings)
                guest_users += 1
        
        # 2. Total Visits
        total_visits = 0

        context = {
            'total_visits': total_visits,
            'logged_in_users': logged_in_users,
            'guest_users': guest_users,
        }
        
        # --- Original context data ---
        total_sales = Order.objects.filter(status='completed').aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders_count = Order.objects.count()
        pending_orders_count = Order.objects.filter(status='pending').count()
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_users_count = User.objects.filter(date_joined__gte=thirty_days_ago).count()

        # Top 5 selling products - Corrected Query
        top_products_stats = list(OrderItem.objects.values('product_id', 'product__name', 'product__slug')
                                  .annotate(total_sold=Sum('quantity'))
                                  .order_by('-total_sold')[:5])
        
        product_ids = [item['product_id'] for item in top_products_stats]

        # Fetch main images for the top products in a single query to prevent N+1 issues.
        main_images = ProductImage.objects.filter(product_id__in=product_ids, is_main=True)\
                                           .values('product_id', 'image')
        
        # Create a dictionary for easy image lookup
        images_dict = {img['product_id']: img['image'] for img in main_images}

        top_products_list = []
        for item in top_products_stats:
            image_url = ""
            if item['product_id'] in images_dict:
                try:
                    image_url = request.build_absolute_uri(settings.MEDIA_URL + str(images_dict[item['product_id']]))
                except (ValueError, TypeError):
                    image_url = ""
            
            top_products_list.append({
                'name': item['product__name'],
                'slug': item['product__slug'],
                'total_sold': item['total_sold'],
                'image_url': image_url,
            })
        
        recent_orders = Order.objects.order_by('-order_date')[:5]

        # Review statistics
        approved_reviews_count = ProductReview.objects.filter(status=ProductReview.STATUS_APPROVED).count()
        pending_reviews_count = ProductReview.objects.filter(status=ProductReview.STATUS_PENDING).count()
        
        # Blog stats
        total_posts_count = BlogPost.objects.count()
        published_posts_count = BlogPost.objects.filter(is_published=True).count()
        recent_posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')[:5]
        

        
        original_context = {
            'total_sales': total_sales,
            'total_orders_count': total_orders_count,
            'pending_orders_count': pending_orders_count,
            'new_users_count': new_users_count,
            'top_products_data': top_products_list,
            'recent_orders': recent_orders,
            'approved_reviews_count': approved_reviews_count,
            'pending_reviews_count': pending_reviews_count,
            'total_posts_count': total_posts_count,
            'published_posts_count': published_posts_count,
            'recent_posts': recent_posts,
            'SHOP_NAME': settings.SHOP_NAME,
        }
        
        context.update(original_context)

        return render(request, self.template_name, context)

# You might need to adjust imports and reverse_lazy paths based on your actual app structure
# Ensure products.models.Product and reviews.models.ProductReview are correctly imported.
# Also, remember to create the groups "Sales Manager", "Content Creator", "Admin" in Django Admin and assign permissions.

# --- Blog Management Views ---

class BlogListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = BlogPost
    template_name = 'dashboard/blog_list.html'
    context_object_name = 'posts'
    permission_required = 'blog.view_blogpost'
    paginate_by = 20

    def get_queryset(self):
        return BlogPost.objects.all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context



class BlogCreateUpdateView(LoginRequiredMixin, SuccessMessageMixin, View):
    template_name = 'dashboard/blog_form.html'
    model = BlogPost
    # TODO block change 'author' fields from member and auto change 'author' from system
    fields = ['title', 'slug', 'author', 'content', 'image', 'category', 'tags', 'is_published']
    success_url = reverse_lazy('dashboard:blog_list')
    CKEditor5Widget_custom = CKEditor5Widget
    CKEditor5Widget_custom.template_name = "django_ckeditor_5_custom/widget.html"

    def get_object(self, pk=None):
        if pk:
            return get_object_or_404(BlogPost, pk=pk)
        return None

    def get_permission_required(self, instance=None):
        if instance:
            return ('blog.change_blogpost',)
        return ('blog.add_blogpost',)

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object(kwargs.get('pk'))
        perms = self.get_permission_required(instance)
        if not all(request.user.has_perm(p) for p in perms):
            messages.error(request, "شما اجازه انجام این عملیات را ندارید.")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        from django.forms import modelform_factory
        modelform = modelform_factory(self.model, fields=self.fields, widgets={
            "content":self.CKEditor5Widget_custom(config_name="blog"),
            })

        return modelform

    def get(self, request, pk=None):
        instance = self.get_object(pk)
        form = self.get_form_class()(instance=instance)
        context = {'form': form, 'object': instance}
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, self.template_name, context)

    def post(self, request, pk=None):
        instance = self.get_object(pk)
        form = self.get_form_class()(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            success_message = "پست وبلاگ با موفقیت ایجاد شد." if not instance else "پست وبلاگ با موفقیت بروزرسانی شد."
            messages.success(request, success_message)
            return redirect(self.success_url)
        context = {'form': form, 'object': instance}
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, self.template_name, context)

class BlogDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = BlogPost
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboard:blog_list')
    permission_required = 'blog.delete_blogpost'
    success_message = "پست وبلاگ با موفقیت حذف شد."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        context['success_url'] = self.success_url
        return context

    def post(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().post(request, *args, **kwargs)

class BlogCategoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = BlogCategory
    template_name = 'dashboard/blog_category_list.html'
    context_object_name = 'categories'
    permission_required = 'blog.view_blogcategory'
    paginate_by = 20

    def get_queryset(self):
        return BlogCategory.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class BlogCategoryCreateUpdateView(LoginRequiredMixin, SuccessMessageMixin, View):
    template_name = 'dashboard/blog_category_form.html'
    model = BlogCategory
    fields = ['name', 'slug']
    success_url = reverse_lazy('dashboard:blog_category_list')

    def get_object(self, pk=None):
        if pk:
            return get_object_or_404(BlogCategory, pk=pk)
        return None

    def get_permission_required(self, instance=None):
        if instance:
            return ('blog.change_blogcategory',)
        return ('blog.add_blogcategory',)

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object(kwargs.get('pk'))
        perms = self.get_permission_required(instance)
        if not all(request.user.has_perm(p) for p in perms):
            messages.error(request, "شما اجازه انجام این عملیات را ندارید.")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        from django.forms import modelform_factory
        return modelform_factory(self.model, fields=self.fields)

    def get(self, request, pk=None):
        instance = self.get_object(pk)
        form = self.get_form_class()(instance=instance)
        context = {'form': form, 'object': instance}
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, self.template_name, context)

    def post(self, request, pk=None):
        instance = self.get_object(pk)
        form = self.get_form_class()(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            success_message = "دسته بندی وبلاگ با موفقیت ایجاد شد." if not instance else "دسته بندی وبلاگ با موفقیت بروزرسانی شد."
            messages.success(request, success_message)
            return redirect(self.success_url)
        context = {'form': form, 'object': instance}
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, self.template_name, context)

class BlogCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = BlogCategory
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboard:blog_category_list')
    permission_required = 'blog.delete_blogcategory'
    success_message = "دسته بندی وبلاگ با موفقیت حذف شد."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

    def post(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().post(request, *args, **kwargs)

# --- Blog Comment Management Views ---

class BlogCommentManagementView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = BlogComment
    template_name = 'dashboard/blog_comment_management.html'
    context_object_name = 'comments'
    permission_required = ('blog.view_blogcomment', 'blog.change_blogcomment')
    paginate_by = 25

    def get_queryset(self):
        queryset = BlogComment.objects.select_related('post', 'user').order_by('-created_at')
        status = self.request.GET.get('status')
        if status in [BlogComment.STATUS_PENDING, BlogComment.STATUS_APPROVED, BlogComment.STATUS_REJECTED]:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', '')
        context['total_comments'] = BlogComment.objects.count()
        context['pending_count'] = BlogComment.objects.filter(status=BlogComment.STATUS_PENDING).count()
        context['approved_count'] = BlogComment.objects.filter(status=BlogComment.STATUS_APPROVED).count()
        context['rejected_count'] = BlogComment.objects.filter(status=BlogComment.STATUS_REJECTED).count()
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class UpdateBlogCommentStatusView(LoginRequiredMixin, PermissionRequiredMixin, View):
    def get_permission_required(self):
        action = self.request.POST.get('action')
        if action == 'delete':
            return ('blog.delete_blogcomment',)
        return ('blog.change_blogcomment',)

    def handle_no_permission(self):
        messages.error(self.request, "شما اجازه انجام این کار را ندارید.")
        return redirect(reverse('dashboard:blog_comment_management'))

    def post(self, request, *args, **kwargs):
        comment_id = request.POST.get('comment_id')
        action = request.POST.get('action')
        comment = get_object_or_404(BlogComment, pk=comment_id)
        
        # Check permissions
        perms = self.get_permission_required()
        if not request.user.has_perms(perms):
            return self.handle_no_permission()

        if action == 'approve':
            comment.status = BlogComment.STATUS_APPROVED
            comment.admin_accepted_by = request.user
            comment.save()
            messages.success(request, "دیدگاه با موفقیت تایید شد.")
        elif action == 'reject':
            comment.status = BlogComment.STATUS_REJECTED
            comment.admin_accepted_by = request.user
            comment.save()
            messages.warning(request, "دیدگاه رد شد.")
        elif action == 'pending':
            comment.status = BlogComment.STATUS_PENDING
            comment.admin_accepted_by = request.user
            comment.save()
            messages.info(request, "وضعیت دیدگاه به 'در انتظار تایید' تغییر یافت.")
        elif action == 'delete':
            comment.delete()
            messages.success(request, "دیدگاه با موفقیت حذف شد.")
        else:
            messages.error(request, "عملیات نامعتبر است.")

        # Redirect back to the referrer or the main management page
        redirect_url = request.META.get('HTTP_REFERER', reverse('dashboard:blog_comment_management'))
        return redirect(redirect_url)



