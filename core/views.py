from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.
class HomePageView(TemplateView):
    template_name = "home.html" # Or 'core/home.html' if you prefer to keep app templates namespaced
