from django.shortcuts import render
from django.views.generic import TemplateView
from django.conf import settings

# Create your views here.
class HomePageView(TemplateView):
    template_name = "home.html" # Or 'core/home.html' if you prefer to keep app templates namespaced

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context
