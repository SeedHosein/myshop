from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='in_group')
def in_group(user, group_names):
    """
    Checks if a user is a member of any of the given groups.
    Usage: {% if request.user|in_group:"Admin,Editor" %}
    """
    if user.is_authenticated:
        group_list = [name.strip() for name in group_names.split(',')]
        return user.groups.filter(name__in=group_list).exists()
    return False

@register.filter
def mul(value, arg):
    """Multiplies the arg and the value"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        try:
            return float(value) * float(arg)
        except (ValueError, TypeError):
            return ''

@register.filter
def div(value, arg):
    """Divides the value by the arg"""
    try:
        # Attempt to perform division, ensuring floating point for accuracy
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        # Return an empty string or 0 in case of error (e.g., division by zero)
        return ''

@register.filter(name='add_class')
def add_class(value, arg):
    """
    Adds a CSS class to a form field.
    Usage: {{ form.my_field|add_class:"my-class" }}
    """
    css_classes = value.field.widget.attrs.get('class', '')
    if css_classes:
        css_classes = f"{css_classes} {arg}"
    else:
        css_classes = arg
    return value.as_widget(attrs={'class': css_classes}) 