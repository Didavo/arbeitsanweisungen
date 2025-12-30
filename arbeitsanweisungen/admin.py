from django.contrib import admin
from .models import Arbeitsanweisung


@admin.register(Arbeitsanweisung)
class ArbeitsanweisungAdmin(admin.ModelAdmin):
    list_display = ['nummer', 'name', 'get_arbeitsplaetze_anzeige', 'kategorie', 'erstellt_am']
    list_filter = ['kategorie', 'erstellt_am']
    search_fields = ['nummer', 'name']

    def get_arbeitsplaetze_anzeige(self, obj):
        """Zeigt Arbeitsplätze in der Admin-Liste"""
        return obj.get_arbeitsplaetze_display()

    get_arbeitsplaetze_anzeige.short_description = 'Arbeitsplätze'