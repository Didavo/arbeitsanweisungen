from django.db import models
from django.core.validators import MinValueValidator

import os


class Arbeitsanweisung(models.Model):
    """
    Model für Arbeitsanweisungen
    """

    # Vordefinierte Arbeitsplätze
    ARBEITSPLATZ_CHOICES = [

        ('kalkulation', 'Kalkulation'),
        ('fertigung', 'Fertigung'),
        ('lager_versand_wareneingang', 'Lager / Versand / Wareneingang'),
        ('lasern_stanzen_entgraten', 'Lasern / Stanzen / Entgraten'),
        ('montage_zerspanen', 'Montage / Zerspanen'),
        ('qualitaetssicherung', 'Qualitätssicherung'),
        ('schweissen', 'Schweißen'),
        ('sonst_handarbeitsplaetze', 'Sonst. Handarbeitsplätze'),
        ('zerspanen_saegen', 'Zerspanen / Sägen'),
        ('programmieren', 'Programmieren'),
        ('konstruktion', 'Konstruktion'),

        # Weitere Arbeitsplätze hier hinzufügen
    ]

    # Kategorien
    KATEGORIE_CHOICES = [
        ('prozessbeschreibung', 'Prozessbeschreibung'),
        ('arbeitsanweisung', 'Arbeitsanweisung'),
        ('betriebsanweisung', 'Betriebsanweisung'),
        ('stellenbeschreibung', 'Stellenbeschreibung'),
        ('formblaetter', 'Formblätter'),
    ]

    nummer = models.IntegerField(
        unique=True,
        validators=[MinValueValidator(1)],
        verbose_name="Nummer",
        help_text="Automatisch generiert in 10er-Schritten, aber änderbar"
    )

    name = models.CharField(
        max_length=255,
        verbose_name="Name",
        help_text="Name der Arbeitsanweisung"
    )

    arbeitsplaetze = models.JSONField(
        default=list,
        verbose_name="Arbeitsplätze",
        help_text="Wählen Sie einen oder mehrere Arbeitsplätze"
    )

    kategorie = models.CharField(
        max_length=50,
        choices=KATEGORIE_CHOICES,
        default='arbeitsanweisung',
        verbose_name="Kategorie",
        help_text="Art der Anweisung"
    )

    revision = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Revision",
        help_text="Revisionsstand"
    )

    datei_pfad = models.CharField(
        max_length=500,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Dateipfad",
        help_text="Pfad zur Datei im Filesystem"
    )

    erstellt_am = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")

    class Meta:
        verbose_name = "Arbeitsanweisung"
        verbose_name_plural = "Arbeitsanweisungen"
        ordering = ['nummer']

    def __str__(self):
        return f"{self.nummer} - {self.name}"

    def save(self, *args, **kwargs):
        # Automatische Nummerngenerierung nur bei neuen Objekten
        if not self.pk and not self.nummer:
            letzte_anweisung = Arbeitsanweisung.objects.order_by('-nummer').first()
            if letzte_anweisung:
                self.nummer = letzte_anweisung.nummer + 10
            else:
                self.nummer = 10  # Startwert
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Datei löschen, wenn Arbeitsanweisung gelöscht wird
        if self.datei_pfad and os.path.exists(self.datei_pfad):
            try:
                os.remove(self.datei_pfad)
            except Exception as e:
                print(f"Fehler beim Löschen der Datei: {e}")
        super().delete(*args, **kwargs)

    @property
    def dateiname(self):
        """Gibt nur den Dateinamen ohne Pfad zurück"""
        if self.datei_pfad:
            return os.path.basename(self.datei_pfad)
        return None

    @property
    def datei_existiert(self):
        """Prüft ob die Datei noch existiert"""
        if self.datei_pfad:
            return os.path.exists(self.datei_pfad)
        return False

    @property
    def kategorie_badge_farbe(self):
        """Gibt Bootstrap-Farbe für Kategorie-Badge zurück"""
        farben = {
            'alle': 'secondary',
            'prozessbeschreibung': 'info',
            'arbeitsanweisung': 'primary',
            'betriebsanweisung': 'warning',
            'stellenbeschreibung': 'success',
            'formblaetter': 'secondary'
        }
        return farben.get(self.kategorie, 'secondary')

    @property
    def kategorie_icon(self):
        """Gibt passendes Icon für Kategorie zurück"""
        icons = {
            'alle': 'bi-collection',
            'prozessbeschreibung': 'bi-diagram-3',
            'arbeitsanweisung': 'bi-file-text',
            'betriebsanweisung': 'bi-shield-check',
            'stellenbeschreibung': 'bi-file-text',
            'formblaetter': 'bi-file-text',
        }
        return icons.get(self.kategorie, 'bi-file-text')

    def get_arbeitsplaetze_display(self):
        """Gibt lesbare Namen der Arbeitsplätze zurück"""
        if not self.arbeitsplaetze:
            return "Keine Arbeitsplätze zugewiesen"

        arbeitsplatz_dict = dict(self.ARBEITSPLATZ_CHOICES)
        return ", ".join([arbeitsplatz_dict.get(ap, ap) for ap in self.arbeitsplaetze])

    def get_arbeitsplaetze_badges(self):
        """Gibt Liste von Arbeitsplätzen für Badge-Darstellung zurück"""
        if not self.arbeitsplaetze:
            return []

        arbeitsplatz_dict = dict(self.ARBEITSPLATZ_CHOICES)
        return [arbeitsplatz_dict.get(ap, ap) for ap in self.arbeitsplaetze]