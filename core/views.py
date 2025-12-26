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
from core.models import ShopInformation
from static_pages.models import StaticPage
from cart_and_orders.models import Cart, CartItem

# Create your views here.
class HomePageView(TemplateView):
    template_name = "home.html" # Or 'core/home.html' if you prefer to keep app templates namespaced

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        home_page_article_content = ""
        try:
            home_page_article_slug = ShopInformation.objects.get(name="home-page-article").value
            home_page_article_content = StaticPage.objects.get(slug=home_page_article_slug).content
        except ShopInformation.DoesNotExist:
            home_page_article_content = ""
        except StaticPage.DoesNotExist:
            home_page_article_content = ""
        
        context['home_page_article_content'] = home_page_article_content
        
        
        products = Product.objects.filter(is_active=True)
        popular_products = products.order_by('-hit_count_generic__hits')[:10]
        context['popular_products'] = popular_products
        categorys = Category.objects.all()
        popular_category = categorys.order_by('-hit_count_generic__hits')[:5]
        context['popular_category'] = popular_category
        
        # # test for messages
        # from django.contrib import messages
        # messages.error(self.request, "this test message error")
        # messages.success(self.request, "this test message success")
        # messages.warning(self.request, "this test message warning")
        # messages.info(self.request, "this test message info")
        
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