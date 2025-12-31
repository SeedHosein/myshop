from django import template
# from core.models import ShopInformation

register = template.Library()

@register.simple_tag
def get_shop_information_value(name, ShopInformation):
    """
    e.g: {% get_static_page_slug 'about' ShopInformation %}
    """
    try:
        return ShopInformation[name]
    except:
        return ""