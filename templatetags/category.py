from decimal import Decimal
from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def categories():
    from redline.categories.models import Category
    cats = Category.active.order_by('-name')
    data = {}
    for cat in cats:
        data[str(cat.slug)] = str(cat.name)
    return str(data)
