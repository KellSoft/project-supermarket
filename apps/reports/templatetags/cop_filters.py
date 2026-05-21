from django import template

register = template.Library()


@register.filter
def cop(value):
    """Formato peso colombiano: 1.500.000"""
    try:
        return "{:,.0f}".format(float(value)).replace(",", ".")
    except (ValueError, TypeError):
        return value
