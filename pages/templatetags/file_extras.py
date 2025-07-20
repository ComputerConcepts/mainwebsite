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

@register.filter
def mul(value, multiplier):
    """Multiply a value by the given multiplier."""
    try:
        return float(value) * float(multiplier)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, divisor):
    """Divide a value by the given divisor."""
    try:
        divisor_val = float(divisor)
        if divisor_val == 0:
            return 0
        return float(value) / divisor_val
    except (ValueError, TypeError):
        return 0
