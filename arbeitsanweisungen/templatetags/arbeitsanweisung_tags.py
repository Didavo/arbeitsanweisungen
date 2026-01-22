from django import template
from ..models import Arbeitsanweisung

register = template.Library()


@register.filter
def get_kategorie_label(key):
    """Gibt das Label einer Kategorie zurück"""
    kategorie_dict = dict(Arbeitsanweisung.KATEGORIE_CHOICES)
    return kategorie_dict.get(key, key)


@register.filter
def get_item(dictionary, key):
    """
    Ermöglicht Dictionary-Zugriff in Templates
    Verwendung: {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key, 0)
# ========================================================