import os

from datetime import datetime
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

from products.models import Product, Category
from cart_and_orders.models import Cart, CartItem

# Create your views here.
class HomePageView(TemplateView):
    template_name = "home.html" # Or 'core/home.html' if you prefer to keep app templates namespaced

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        
        products = Product.objects.filter(is_active=True)
        popular_products = products.order_by('-hit_count_generic__hits')[:10]
        context['popular_products'] = popular_products
        categorys = Category.objects.all()
        popular_category = categorys.order_by('-hit_count_generic__hits')[:5]
        context['popular_category'] = popular_category
        
        return context







class CKeditorUplodeFile(View):
    
    permission_required = 'core.CKeditor_Uplode_Blog_file'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm(self.permission_required):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        # print(request.__dict__)
        uploaded_file = request.FILES.get('upload')
        if uploaded_file:
            now = datetime.now()
            date_path = now.strftime('%Y_%m_%d')
            upload_path = os.path.join('ck_editor', f"{date_path}___{str(uploaded_file.name)}")

            saved_path = default_storage.save(upload_path, uploaded_file)
            file_url = default_storage.url(saved_path)

            return JsonResponse({'url': file_url})

        return JsonResponse({'error': {'message': 'درخواست نامعتبر است'}}, status=400)