from django import template

register = template.Library()

@register.filter
def split(value, separator=','):
    """Split a string by the given separator."""
    if not value:
        return []
    return [item.strip() for item in value.split(separator) if item.strip()]

@register.filter
def strip(value):
    """Strip whitespace from a string."""
    if not value:
        return ''
    return value.strip()
