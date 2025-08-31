from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.http import Http404, JsonResponse
from django.db.models import Q
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from hitcount.views import HitCountDetailView, HitCountMixin
from hitcount.utils import get_hitcount_model

from cart_and_orders.views import calculate_session_cart_totals, get_session_cart, save_session_cart


from .models import Product, Category, ProductImage, ProductVideo
from cart_and_orders.models import Cart, CartItem


import os


class ProductListView(ListView, HitCountMixin):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12 # Optional: add pagination
    object = None
    
    count_hit = True

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            self.object = category
            queryset = queryset.filter(category=category)
        return queryset.order_by('-created_at')

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

        cart_items_active = []
        cart_items_saved_for_later = []
        context['SHOP_NAME'] = settings.SHOP_NAME

        if self.request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=self.request.user)
            active_items_query = cart.items.filter(is_saved_for_later=False)
            saved_items_query = cart.items.filter(is_saved_for_later=True)
            
            for item in active_items_query:
                if item.product.is_active and item.product.stock > 0:
                    if item.product.stock < item.quantity:
                        item.quantity = item.product.stock
                        item.save()
                        msg = f"تعداد محصول '{item.product.name}' به علت کم بودن موجودی محصول در سبد خرید شما به '{item.quantity}' کاهش یافت. قبل از اتمام کامل موجودی خرید خود را تکمیل کنید."
                        messages.warning(self.request, msg)
                    cart_items_active.append({
                        'item': item,
                        'product': item.product,
                        'quantity': item.quantity,
                    })
                else:
                    product_name = item.product.name
                    item.delete()
                    msg = f"محصول '{product_name}' به علت تمام شدن موجودی از سبد خرید شما حذف شد."
                    messages.warning(self.request, msg)

            for item in saved_items_query:
                if item.product.is_active and item.product.stock > 0:
                    if item.product.stock < item.quantity:
                        item.quantity = item.product.stock
                        item.save()
                        msg = f"تعداد محصول '{item.product.name}' به علت کم بودن موجودی محصول در سبد خرید بعدی شما به '{item.quantity}' کاهش یافت. قبل از اتمام کامل موجودی خرید خود را تکمیل کنید."
                        messages.warning(self.request, msg)
                    cart_items_saved_for_later.append({
                        'item': item,
                        'product': item.product,
                        'quantity': item.quantity,
                    })
                else:
                    product_name = item.product.name
                    item.delete()
                    msg = f"محصول '{product_name}' به علت تمام شدن موجودی از سبد خرید بعدی شما حذف شد."
                    messages.warning(self.request, msg)
        else:
            # Session cart
            session_cart_data = get_session_cart(self.request.session)
            session_cart = get_session_cart(self.request.session)
            for product_id_str, details in session_cart_data.get('items', {}).items():
                try:
                    product = Product.objects.get(id=int(product_id_str), is_active=True)
                    quantity = details.get('quantity', 1)
                    if product.stock > 0:
                        if product.stock < quantity:
                            session_cart['items'][product_id_str].quantity = item.product.stock
                            msg = f"تعداد محصول '{item.product.name}' به علت کم بودن موجودی محصول در سبد خرید شما به '{item.quantity}' کاهش یافت. قبل از اتمام کامل موجودی خرید خود را تکمیل کنید."
                            messages.warning(self.request, msg)
                        cart_items_active.append({
                            'product': product,
                            'quantity': session_cart['items'][product_id_str].get('quantity', 1),
                        })
                    else:
                        if product_id_str in session_cart['items']:
                            product_name = session_cart['items'][product_id_str].get('name', "انتخابی")
                            del session_cart['items'][product_id_str]
                        msg = f"محصول '{product_name}' به علت تمام شدن موجودی از سبد خرید شما حذف شد."
                        messages.warning(self.request, msg)
                except Product.DoesNotExist:
                    if product_id_str in session_cart['items']:
                        product_name = session_cart['items'][product_id_str].get('name', "انتخابی")
                        del session_cart['items'][product_id_str]
                    msg = f"محصول '{product_name}' به علت تمام شدن موجودی از سبد خرید شما حذف شد."
                    messages.warning(self.request, msg)
                    continue 
            if session_cart != session_cart_data:
                session_cart = calculate_session_cart_totals(session_cart)
                save_session_cart(self.request.session, session_cart)
        context['cart_items_active'] = cart_items_active
        context['cart_items_saved_for_later'] = cart_items_saved_for_later
        
        
        context['categories'] = Category.objects.filter(parent__isnull=True) # Top-level categories
        context['current_category'] = None
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(Category, slug=category_slug)
        return context

class ProductDetailView(HitCountDetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug' # Ensure your Product model has a slug field
    slug_url_kwarg = 'slug' # Matches the URL pattern
    
    count_hit = True

    def get_queryset(self):
        # Ensure only active products are viewable
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        
        product = self.get_object()
        context['images'] = ProductImage.objects.filter(product=product)
        context['videos'] = ProductVideo.objects.filter(product=product)
        # You can add related products or other context here later
        return context

# For AJAX search
class ProductSearchAPIView(ListView):
    model = Product

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        page = request.GET.get('page', '1')
        try:
            page = int(page)
        except:
            page = 1
        if query and len(query) >= 2: # Minimum query length
            products = Product.objects.filter(
                Q(is_active=True) &
                (Q(name__icontains=query) | 
                 Q(description_short__icontains=query) | 
                 Q(category__name__icontains=query))
            ).distinct()[(page*10)-10:(page*10)+1]
            
            results = []
            for product in products:
                # Safely get the main image
                main_image = product.get_main_image()
                results.append({
                    'id': product.id,
                    'name': product.name,
                    'category_name':product.category.name,
                    'slug': product.slug,
                    'price': product.price,
                    'discounted_price': product.get_display_price, # Ensure this method exists
                    'image_url': main_image.image.url if main_image else '',
                    # Add a URL to the product detail page
                    'detail_url': product.get_absolute_url() if hasattr(product, 'get_absolute_url') else '#' 
                })
            return JsonResponse({'products': results})
        return JsonResponse({'products': []})


class CKeditorUplodeProductImage(View):
    
    permission_required = 'core.CKeditor_Uplode_Product_image'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm(self.permission_required):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        uploaded_file = request.FILES.get('upload')
        if uploaded_file:
            now = datetime.now()
            date_path = now.strftime('%Y_%m_%d')
            upload_path = os.path.join('ck_editor/product_uplodeimage', f"{date_path}___{str(uploaded_file.name)}")

            saved_path = default_storage.save(upload_path, uploaded_file)
            file_url = default_storage.url(saved_path)

            return JsonResponse({'url': file_url})

        return JsonResponse({'error': {'message': 'درخواست نامعتبر است'}}, status=400)
        
