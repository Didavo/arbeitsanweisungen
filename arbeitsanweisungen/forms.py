import os

from django import forms
from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.db import models
from .models import Arbeitsanweisung


class ArbeitsanweisungCreationForm(forms.ModelForm):
    """
    Form zum Erstellen einer neuen Arbeitsanweisung
    """

    arbeitsplaetze = forms.MultipleChoiceField(
        choices=Arbeitsanweisung.ARBEITSPLATZ_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Arbeitsplätze',
        help_text='Wählen Sie einen oder mehrere Arbeitsplätze aus',
        required=True
    )

    datei = forms.FileField(
        required=False,
        label='Datei',
        help_text='Optional: PDF, Word, Excel oder andere Dokumente hochladen',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png'
        })
    )

    class Meta:
        model = Arbeitsanweisung
        fields = ['nummer', 'name', 'arbeitsplaetze', 'kategorie', 'datei_pfad']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name der Arbeitsanweisung'
            }),
            'nummer': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Wird automatisch generiert (änderbar)'
            }),
            'kategorie': forms.Select(attrs={
                'class': 'form-control'
            }),
            'arbeitsplaetze': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        help_texts = {
            'nummer': 'Leer lassen für automatische Generierung in 10er-Schritten'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nummer-Feld optional machen beim Erstellen
        self.fields['nummer'].required = False


    def clean_datei(self):
        datei = self.cleaned_data.get('datei')
        if datei:
            # Maximale Dateigröße: 10 MB
            if datei.size > 10 * 1024 * 1024:
                raise ValidationError('Die Datei darf maximal 10 MB groß sein.')

            # Erlaubte Dateitypen
            erlaubte_endungen = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt',
                                 '.jpg', '.jpeg', '.png', '.gif', '.zip']
            dateiname = datei.name.lower()
            if not any(dateiname.endswith(endung) for endung in erlaubte_endungen):
                raise ValidationError('Dieser Dateityp ist nicht erlaubt.')

        return datei

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Datei speichern, wenn vorhanden
        datei = self.cleaned_data.get('datei')
        if datei:
            # Sicherstellen, dass das /data Verzeichnis existiert
            data_dir = os.path.join(settings.BASE_DIR, 'data')
            os.makedirs(data_dir, exist_ok=True)

            # Dateinamen bereinigen und eindeutig machen
            dateiname = self._bereinigte_dateiname(datei.name)
            dateipfad = os.path.join(data_dir, dateiname)

            # Datei speichern
            with open(dateipfad, 'wb+') as destination:
                for chunk in datei.chunks():
                    destination.write(chunk)

            instance.datei_pfad = dateipfad

        if commit:
            instance.save()

        return instance

    def _bereinigte_dateiname(self, original_name):
        """Erstellt einen bereinigten, eindeutigen Dateinamen"""
        import re
        from datetime import datetime

        # Dateiendung extrahieren
        name, ext = os.path.splitext(original_name)

        # Sonderzeichen entfernen
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '_', name)

        # Zeitstempel hinzufügen für Eindeutigkeit
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        return f"{name}_{timestamp}{ext}"


class ArbeitsanweisungChangeForm(forms.ModelForm):
    """
    Form zum Ändern einer bestehenden Arbeitsanweisung
    """

    arbeitsplaetze = forms.MultipleChoiceField(
        choices=Arbeitsanweisung.ARBEITSPLATZ_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Arbeitsplätze',
        help_text='Wählen Sie einen oder mehrere Arbeitsplätze aus',
        required=True
    )

    datei = forms.FileField(
        required=False,
        label='Neue Datei hochladen',
        help_text='Optional: Neue Datei hochladen (ersetzt die alte Datei)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png'
        })
    )

    datei_loeschen = forms.BooleanField(
        required=False,
        label='Vorhandene Datei löschen',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = Arbeitsanweisung
        fields = ['nummer', 'name', 'arbeitsplaetze', 'kategorie']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'nummer': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'arbeitsplaetze': forms.Select(attrs={
                'class': 'form-control'
            }),
            'kategorie': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def clean_datei(self):
        datei = self.cleaned_data.get('datei')
        if datei:
            # Maximale Dateigröße: 10 MB
            if datei.size > 10 * 1024 * 1024:
                raise ValidationError('Die Datei darf maximal 10 MB groß sein.')

            # Erlaubte Dateitypen
            erlaubte_endungen = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt',
                                 '.jpg', '.jpeg', '.png', '.gif', '.zip']
            dateiname = datei.name.lower()
            if not any(dateiname.endswith(endung) for endung in erlaubte_endungen):
                raise ValidationError('Dieser Dateityp ist nicht erlaubt.')

        return datei

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Alte Datei löschen, wenn gewünscht
        if self.cleaned_data.get('datei_loeschen') and instance.datei_pfad:
            if os.path.exists(instance.datei_pfad):
                try:
                    os.remove(instance.datei_pfad)
                except Exception as e:
                    print(f"Fehler beim Löschen der alten Datei: {e}")
            instance.datei_pfad = None

        # Neue Datei speichern, wenn vorhanden
        datei = self.cleaned_data.get('datei')
        if datei:
            # Alte Datei erst löschen
            if instance.datei_pfad and os.path.exists(instance.datei_pfad):
                try:
                    os.remove(instance.datei_pfad)
                except Exception as e:
                    print(f"Fehler beim Löschen der alten Datei: {e}")

            # Sicherstellen, dass das /data Verzeichnis existiert
            data_dir = os.path.join(settings.BASE_DIR, 'data')
            os.makedirs(data_dir, exist_ok=True)

            # Dateinamen bereinigen und eindeutig machen
            dateiname = self._bereinigte_dateiname(datei.name, instance.nummer)
            dateipfad = os.path.join(data_dir, dateiname)

            # Datei speichern
            with open(dateipfad, 'wb+') as destination:
                for chunk in datei.chunks():
                    destination.write(chunk)

            instance.datei_pfad = dateipfad

        if commit:
            instance.save()

        return instance

    def _bereinigte_dateiname(self, original_name, nummer):
        """Erstellt einen bereinigten, eindeutigen Dateinamen"""
        import re
        from datetime import datetime

        # Dateiendung extrahieren
        name, ext = os.path.splitext(original_name)

        # Sonderzeichen entfernen
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '_', name)

        # Zeitstempel hinzufügen für Eindeutigkeit
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        return f"AA_{nummer}_{name}_{timestamp}{ext}"


class ArbeitsanweisungSearchForm(forms.Form):
    """
    Form zum Suchen und Filtern von Arbeitsanweisungen
    """
    suchbegriff = forms.CharField(
        required=False,
        label='Suche',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name oder Nummer suchen...'
        })
    )

    arbeitsplatz = forms.ChoiceField(
        required=False,
        label='Arbeitsplatz',
        choices=[('', 'Alle Abteilungen')] + list(Arbeitsanweisung.ARBEITSPLATZ_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    kategorie = forms.ChoiceField(
        required=False,
        label='Kategorie',
        choices=[('', 'Alle Kategorien')] + list(Arbeitsanweisung.KATEGORIE_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    sortierung = forms.ChoiceField(
        required=False,
        label='Sortierung',
        choices=[
            ('nummer', 'Nummer aufsteigend'),
            ('-nummer', 'Nummer absteigend'),
            ('name', 'Name A-Z'),
            ('-name', 'Name Z-A'),
            ('-erstellt_am', 'Neueste zuerst'),
            ('erstellt_am', 'Älteste zuerst'),
        ],
        initial='nummer',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    def filter_queryset(self, queryset):
        """
        Hilfsmethode zum Filtern eines QuerySets basierend auf den Form-Daten
        """

        if not self.is_valid():
            return queryset

        data = self.cleaned_data

        # Suche nach Name oder Nummer
        if data.get('suchbegriff'):

            queryset = queryset.filter(
                Q(name__icontains=data['suchbegriff']) |
                Q(nummer__icontains=data['suchbegriff'])
            )

        # Filter nach Arbeitsplätzen

        # Filter nach Kategorie
        if data.get('kategorie'):
            queryset = queryset.filter(kategorie=data['kategorie'])

        # Sortierung
        if data.get('sortierung'):
            queryset = queryset.order_by(data['sortierung'])
        print(queryset)

        # Filterung nach Arbeitsplätzen
        # MUSS am Ende stehen
        arbeitsplatz = data.get('arbeitsplatz')
        if arbeitsplatz:
            queryset = [obj for obj in queryset if arbeitsplatz in (obj.arbeitsplaetze or [])]

        return queryset


class ArbeitsanweisungImportForm(forms.Form):
    """
    Form zum Importieren von Arbeitsanweisungen aus einem ZIP-Archiv
    """
    zip_datei = forms.FileField(
        label='ZIP-Archiv',
        help_text='Wählen Sie ein zuvor exportiertes ZIP-Archiv aus',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.zip'
        })
    )

    ueberschreiben = forms.BooleanField(
        required=False,
        initial=False,
        label='Bestehende Arbeitsanweisungen überschreiben',
        help_text='Wenn aktiviert, werden Arbeitsanweisungen mit gleicher Nummer überschrieben',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean_zip_datei(self):
        datei = self.cleaned_data.get('zip_datei')
        if datei:
            # Prüfe ob es wirklich eine ZIP-Datei ist
            if not datei.name.endswith('.zip'):
                raise ValidationError('Bitte laden Sie eine ZIP-Datei hoch.')

            # Maximale Größe: 100 MB
            if datei.size > 100 * 1024 * 1024:
                raise ValidationError('Die ZIP-Datei darf maximal 100 MB groß sein.')

        return datei