from django import template
from django.utils.html import format_html

from products.models import Category

import re

register = template.Library()

@register.filter(name='embed_youtube_url')
def embed_youtube_url(value):
    if not isinstance(value, str):
        return '' # Return empty string or original value if not a string
    # Converts youtube.com/watch?v=ID to youtube.com/embed/ID
    # Also handles youtu.be/ID and youtube.com/embed/ID (idempotent)
    # Handles URLs with extra parameters like ?t=1s
    
    # Regex to find YouTube ID from various URL formats
    regex_patterns = [
        r"(?:https|http)://(?:www\.)?youtube\.com/(?:embed/|watch\?v=|v/|shorts/|live/)([\w-]+)(?:\?.*)?",
        r"(?:https|http)://(?:www\.)?youtu\.be/([\w-]+)(?:\?.*)?"
    ]
    
    video_id = None
    for pattern in regex_patterns:
        match = re.search(pattern, value)
        if match:
            video_id = match.group(1)
            break
            
    if video_id:
        return f"https://www.youtube.com/embed/{video_id}"
    
    return value # Return original if not a recognized YouTube URL or if ID extraction fails 


@register.simple_tag(name='category_children')
def category_children(category, *args, current_category = None, **kwargs):
    if category.children.exists():
        childs = ""
        for child in category.children.all():
            childs = childs + "" + str(category_children(child, current_category=current_category))
        return format_html(f'''
            <li class="category-item has-children {"open" if "active" in childs else ""}">
                <div class="category-toggle">
                    <a href="{category.get_absolute_url()}" class="filter-link {"active" if current_category and current_category.slug == category.slug else ""}">{category.name}</a>
                    <i class="fas fa-chevron-left category-arrow"></i>
                </div>
                <ul class="subcategory-list category-accordion">
                    {childs}
                </ul>
            </li>
        ''')
    else:
        return format_html(f'''
            <li class="category-item">
                <div class="category-toggle">
                    <a href="{category.get_absolute_url()}" class="filter-link {"active" if current_category and current_category.slug == category.slug else ""}">{category.name}</a>
                </div>
            </li>
        ''')

@register.simple_tag(name='category_parents')
def category_parents(category, *args, parents=[], **kwargs):
    if category.parent:
        parents = category_parents(category.parent, parents=[category.parent, *parents])
    return parents

@register.simple_tag(name='is_in_cart')
def is_in_cart(product_id, request, cart_items_active=[], cart_items_saved_for_later=[]):
    print(product_id)
    for cart_item_info in cart_items_active + cart_items_saved_for_later:
        if cart_item_info['product'].id == product_id:
            return (str(cart_item_info.get('quantity', 1)), cart_item_info)
    
    return ('', {})
    
    