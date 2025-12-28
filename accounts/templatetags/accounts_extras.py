from django import template

register = template.Library()

@register.filter
def translate_password_error(error):
    """translate password error"""
    translate_error_list = {
        "This password is too short. It must contain at least 8 characters.": "این رمز عبور خیلی کوتاه است. باید حداقل ۸ کاراکتر داشته باشد.",
        "This password is entirely numeric.": "رمز عبور نباید کاملاً عددی باشد.",
        "This password is too common.": "این رمز عبور خیلی رایج است.",
        "": "",
        "": "",
        "": "",
    }
    try:
        return translate_error_list.get(error, error)
    except (KeyError):
        return error
    