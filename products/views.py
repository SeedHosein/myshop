from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.db.models import Q
from .models import Product, Category, ProductImage, ProductVideo

# Create your views here.

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12 # Optional: add pagination

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=category)
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent__isnull=True) # Top-level categories
        context['current_category'] = None
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(Category, slug=category_slug)
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug' # Ensure your Product model has a slug field
    slug_url_kwarg = 'slug' # Matches the URL pattern

    def get_queryset(self):
        # Ensure only active products are viewable
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        if query and len(query) >= 2: # Minimum query length
            products = Product.objects.filter(
                Q(is_active=True) &
                (Q(name__icontains=query) | 
                 Q(description_short__icontains=query) | 
                 Q(category__name__icontains=query))
            ).distinct()[:10] # Limit results
            
            results = []
            for product in products:
                # Safely get the main image
                main_image = product.get_main_image()
                results.append({
                    'id': product.id,
                    'name': product.name,
                    'slug': product.slug,
                    'price': str(product.get_display_price), # Ensure this method exists
                    'image_url': main_image.image.url if main_image else '',
                    # Add a URL to the product detail page
                    'detail_url': product.get_absolute_url() if hasattr(product, 'get_absolute_url') else '#' 
                })
            return JsonResponse({'products': results})
        return JsonResponse({'products': []})

# Example of get_absolute_url in Product model (products/models.py)
# from django.urls import reverse
# class Product(...):
#     ...
#     def get_absolute_url(self):
#         return reverse('products:product_detail', kwargs={'slug': self.slug})
