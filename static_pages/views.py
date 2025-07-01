from django.shortcuts import render
from django.views.generic import DetailView
from django.http import Http404
from django.conf import settings
from .models import StaticPage

class StaticPageView(DetailView):
    model = StaticPage
    template_name = 'static_pages/static_page_detail.html'
    context_object_name = 'page'
    slug_url_kwarg = 'slug' # Matches the slug parameter in your urls.py

    def get_queryset(self):
        # Only show published pages to non-staff users
        # Staff users might be able to preview unpublished pages if you add that logic
        if self.request.user.is_staff:
            return StaticPage.objects.all() # Staff can see all
        return StaticPage.objects.filter(is_published=True)

    def get_object(self, queryset=None):
        # Override get_object to ensure only published pages are shown to the public,
        # unless the user is staff (handled by get_queryset).
        obj = super().get_object(queryset)
        if not obj.is_published and not self.request.user.is_staff:
            raise Http404("This page is not currently available.")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

# You might also want a simple template for the static page display.
# templates/static_pages/static_page_detail.html:
"""
{% extends "base.html" %}

{% block title %}{{ page.title }}{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="row">
        <div class="col-lg-10 offset-lg-1">
            <h1 class="mb-4">{{ page.title }}</h1>
            <div>
                {{ page.content|safe }}
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
