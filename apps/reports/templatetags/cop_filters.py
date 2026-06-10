from django import template

register = template.Library()


@register.filter
def cop(value):
    """Formato peso colombiano: 1.500.000"""
    try:
        return "{:,.0f}".format(float(value)).replace(",", ".")
    except (ValueError, TypeError):
        return value


@register.filter
def biz_color(name):
    if not name:
        return "#6c757d"
    n = name.lower()
    if "mercatodo" in n:
        return "#E53935"
    if "supermercado" in n:
        return "#3949AB"
    if "maná" in n or "mana" in n:
        return "#3949AB"
    if "primavera" in n:
        return "#00897B"
    if "panadería" in n or "panaderia" in n or "delipan" in n:
        return "#F4511E"
    if "otros" in n:
        return "#8E24AA"
    return "#6c757d"
