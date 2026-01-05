from django import template
from django.utils.html import format_html

from ..models import BlogCategory

register = template.Library()

@register.simple_tag(name='blog_category_children')
def blog_category_children(category, *args, current_category = None, **kwargs):
    if category.get_children():
        childs = ""
        for child in category.get_children():
            childs = childs + "" + str(blog_category_children(child, current_category=current_category))
        return format_html(f'''
            <li class="category-item has-children{" open" if "active" in childs else ""}">
                <div class="category-toggle flex items-center justify-between">
                    <a href="{category.get_absolute_url()}" class="filter-link{" active" if current_category and current_category.slug == category.slug else ""}">{category.name}</a>
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
                <div class="category-toggle flex items-center justify-between">
                    <a href="{category.get_absolute_url()}" class="filter-link{" active" if current_category and current_category.slug == category.slug else ""}">{category.name}</a>
                </div>
            </li>
        ''')

@register.simple_tag
def blog_category_parents(category):
    """
    Returns a list of parent categories for the given category,
    from top-level parent down to the immediate parent, using MPTT's get_ancestors.
    """
    if category:
        return category.get_ancestors(include_self=False)
    return []
