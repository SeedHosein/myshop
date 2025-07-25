from django import template
from core.models import ShopInformation

register = template.Library()

@register.simple_tag
def get_shop_information_value(name):
    """
    e.g: {% get_static_page_slug 'about' %}
    """
    try:
        page = ShopInformation.objects.get(name=name)
        return page.value
    except ShopInformation.DoesNotExist:
        return ""