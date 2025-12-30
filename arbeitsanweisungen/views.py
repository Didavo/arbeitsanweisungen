import mimetypes

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpResponse
import os
import zipfile
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from .models import Arbeitsanweisung
from .forms import ArbeitsanweisungCreationForm, ArbeitsanweisungChangeForm, ArbeitsanweisungSearchForm, \
    ArbeitsanweisungImportForm


def arbeitsanweisung_liste(request):
    """
    Listenansicht mit Such- und Filterfunktion
    """
    form = ArbeitsanweisungSearchForm(request.GET)
    queryset = Arbeitsanweisung.objects.all()

    if form.is_valid():
        queryset = form.filter_queryset(queryset)

    # Pagination
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page')
    arbeitsanweisungen = paginator.get_page(page_number)

    context = {
        'form': form,
        'arbeitsanweisungen': arbeitsanweisungen,
    }
    return render(request, 'arbeitsanweisungen/arbeitsanweisung_liste.html', context)


def arbeitsanweisung_detail(request, nummer):
    """
    Detailansicht einer einzelnen Arbeitsanweisung
    """
    arbeitsanweisung = get_object_or_404(Arbeitsanweisung, nummer=nummer)

    context = {
        'arbeitsanweisung': arbeitsanweisung,
    }
    return render(request, 'arbeitsanweisungen/arbeitsanweisung_detail.html', context)


def arbeitsanweisung_erstellen(request):
    """
    Erstellen einer neuen Arbeitsanweisung
    """
    if request.method == 'POST':
        form = ArbeitsanweisungCreationForm(request.POST, request.FILES)
        if form.is_valid():
            arbeitsanweisung = form.save()
            messages.success(request, f'Arbeitsanweisung "{arbeitsanweisung.name}" wurde erfolgreich erstellt!')
            return redirect('arbeitsanweisung_liste')
    else:
        form = ArbeitsanweisungCreationForm()

    context = {
        'form': form,
        'title': 'Neues Dokument erstellen',
    }
    return render(request, 'arbeitsanweisungen/arbeitsanweisung_form.html', context)


def arbeitsanweisung_bearbeiten(request, nummer):
    """
    Bearbeiten einer bestehenden Arbeitsanweisung
    """
    arbeitsanweisung = get_object_or_404(Arbeitsanweisung, nummer=nummer)

    if request.method == 'POST':
        form = ArbeitsanweisungChangeForm(request.POST, request.FILES, instance=arbeitsanweisung)
        if form.is_valid():
            arbeitsanweisung = form.save()
            messages.success(request, f'Arbeitsanweisung "{arbeitsanweisung.name}" wurde erfolgreich aktualisiert!')
            return redirect('arbeitsanweisung_detail', nummer=arbeitsanweisung.nummer)
    else:
        form = ArbeitsanweisungChangeForm(instance=arbeitsanweisung)

    context = {
        'form': form,
        'arbeitsanweisung': arbeitsanweisung,
        'title': f'Arbeitsanweisung {arbeitsanweisung.nummer} bearbeiten',
    }
    return render(request, 'arbeitsanweisungen/arbeitsanweisung_form.html', context)


def arbeitsanweisung_loeschen(request, nummer):
    """
    Löschen einer Arbeitsanweisung
    """
    arbeitsanweisung = get_object_or_404(Arbeitsanweisung, nummer=nummer)

    if request.method == 'POST':
        name = arbeitsanweisung.name
        arbeitsanweisung.delete()
        messages.success(request, f'Arbeitsanweisung "{name}" wurde erfolgreich gelöscht!')
        return redirect('arbeitsanweisung_liste')

    context = {
        'arbeitsanweisung': arbeitsanweisung,
    }
    return render(request, 'arbeitsanweisungen/arbeitsanweisung_confirm_delete.html', context)


def arbeitsanweisung_datei_download(request, nummer):
    """
    Download der Datei einer Arbeitsanweisung
    """
    arbeitsanweisung = get_object_or_404(Arbeitsanweisung, nummer=nummer)

    if not arbeitsanweisung.datei_pfad or not os.path.exists(arbeitsanweisung.datei_pfad):
        raise Http404("Datei nicht gefunden")

    try:
        return FileResponse(
            open(arbeitsanweisung.datei_pfad, 'rb'),
            as_attachment=True,
            filename=arbeitsanweisung.dateiname
        )
    except Exception as e:
        raise Http404(f"Fehler beim Laden der Datei: {str(e)}")


def arbeitsanweisung_datei_preview(request, nummer):
    """Vorschau im Browser (inline)"""
    anweisung = get_object_or_404(Arbeitsanweisung, nummer=nummer)

    if not anweisung.datei_pfad or not anweisung.datei_existiert:
        raise Http404("Datei nicht gefunden")

    content_type, _ = mimetypes.guess_type(anweisung.datei_pfad)
    if content_type is None:
        content_type = 'application/octet-stream'

    with open(anweisung.datei_pfad, 'rb') as f:
        response = HttpResponse(f.read(), content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{anweisung.dateiname}"'
        return response


def arbeitsanweisung_export_all(request):
    """
    Exportiert alle Arbeitsanweisungen als ZIP-Archiv
    """
    # Alle Arbeitsanweisungen abrufen
    arbeitsanweisungen = Arbeitsanweisung.objects.all()

    if not arbeitsanweisungen.exists():
        messages.warning(request, 'Keine Arbeitsanweisungen zum Exportieren vorhanden.')
        return redirect('arbeitsanweisung_liste')

    # Temporäres Verzeichnis erstellen
    temp_dir = tempfile.mkdtemp()

    try:
        # JSON-Datei mit Metadaten erstellen
        metadata = []
        dateien_dir = os.path.join(temp_dir, 'dateien')
        os.makedirs(dateien_dir, exist_ok=True)

        for anweisung in arbeitsanweisungen:
            # Metadaten sammeln
            meta = {
                'nummer': anweisung.nummer,
                'name': anweisung.name,
                'arbeitsplaetze': anweisung.arbeitsplaetze,
                'kategorie': anweisung.kategorie,
                'erstellt_am': anweisung.erstellt_am.isoformat(),
                'datei_name': None,
            }

            # Datei kopieren, wenn vorhanden
            if anweisung.datei_pfad and os.path.exists(anweisung.datei_pfad):
                original_dateiname = os.path.basename(anweisung.datei_pfad)
                ziel_dateiname = f"{original_dateiname}"
                ziel_pfad = os.path.join(dateien_dir, ziel_dateiname)

                shutil.copy2(anweisung.datei_pfad, ziel_pfad)
                meta['datei_name'] = ziel_dateiname

            metadata.append(meta)

        # Metadaten als JSON speichern
        metadata_pfad = os.path.join(temp_dir, 'arbeitsanweisungen.json')
        with open(metadata_pfad, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # README erstellen
        readme_pfad = os.path.join(temp_dir, 'README.txt')
        with open(readme_pfad, 'w', encoding='utf-8') as f:
            f.write('Arbeitsanweisungen Export\n')
            f.write('=' * 50 + '\n\n')
            f.write(f'Export-Datum: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}\n')
            f.write(f'Anzahl Arbeitsanweisungen: {len(metadata)}\n\n')
            f.write('Struktur:\n')
            f.write('- arbeitsanweisungen.json: Metadaten aller Arbeitsanweisungen\n')
            f.write('- dateien/: Alle zugehörigen Dateien\n\n')
            f.write('Import:\n')
            f.write('Verwenden Sie die Import-Funktion in der Arbeitsanweisungen-Verwaltung.\n')

        # ZIP-Archiv erstellen
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_name = f'arbeitsanweisungen_export_{timestamp}.zip'
        zip_pfad = os.path.join(temp_dir, zip_name)

        with zipfile.ZipFile(zip_pfad, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # JSON-Datei hinzufügen
            zipf.write(metadata_pfad, 'arbeitsanweisungen.json')

            # README hinzufügen
            zipf.write(readme_pfad, 'README.txt')

            # Alle Dateien hinzufügen
            if os.path.exists(dateien_dir):
                for datei in os.listdir(dateien_dir):
                    datei_pfad = os.path.join(dateien_dir, datei)
                    zipf.write(datei_pfad, os.path.join('dateien', datei))

        # ZIP-Datei als Response zurückgeben
        with open(zip_pfad, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{zip_name}"'

        messages.success(request, f'{len(metadata)} Arbeitsanweisung(en) erfolgreich exportiert!')
        return response

    except Exception as e:
        messages.error(request, f'Fehler beim Export: {str(e)}')
        return redirect('arbeitsanweisung_liste')

    finally:
        # Temporäres Verzeichnis aufräumen
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def arbeitsanweisung_import(request):
    """
    Importiert Arbeitsanweisungen aus einem ZIP-Archiv
    """
    if request.method == 'POST':
        form = ArbeitsanweisungImportForm(request.POST, request.FILES)

        if form.is_valid():
            zip_datei = form.cleaned_data['zip_datei']
            ueberschreiben = form.cleaned_data['ueberschreiben']

            # Temporäres Verzeichnis erstellen
            temp_dir = tempfile.mkdtemp()

            try:
                # ZIP-Datei entpacken
                zip_pfad = os.path.join(temp_dir, 'upload.zip')
                with open(zip_pfad, 'wb+') as destination:
                    for chunk in zip_datei.chunks():
                        destination.write(chunk)

                # ZIP entpacken
                extract_dir = os.path.join(temp_dir, 'extracted')
                with zipfile.ZipFile(zip_pfad, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                # JSON-Datei lesen
                json_pfad = os.path.join(extract_dir, 'arbeitsanweisungen.json')
                if not os.path.exists(json_pfad):
                    messages.error(request, 'Ungültiges Export-Archiv: arbeitsanweisungen.json fehlt.')
                    return redirect('arbeitsanweisung_import')

                with open(json_pfad, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # Statistiken
                erstellt = 0
                aktualisiert = 0
                uebersprungen = 0
                fehler = 0

                # Arbeitsanweisungen importieren
                dateien_dir = os.path.join(extract_dir, 'dateien')
                data_dir = os.path.join(settings.BASE_DIR, 'data')
                os.makedirs(data_dir, exist_ok=True)

                for meta in metadata:
                    try:
                        # Prüfe ob Arbeitsanweisung existiert
                        existiert = Arbeitsanweisung.objects.filter(nummer=meta['nummer']).exists()

                        if existiert and not ueberschreiben:
                            uebersprungen += 1
                            continue

                        # Datei kopieren, wenn vorhanden
                        neuer_datei_pfad = None
                        if meta.get('datei_name'):
                            quell_datei = os.path.join(dateien_dir, meta['datei_name'])
                            if os.path.exists(quell_datei):
                                # Eindeutigen Dateinamen erstellen
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                dateiname = f"{meta['datei_name']}"
                                neuer_datei_pfad = os.path.join(data_dir, dateiname)
                                shutil.copy2(quell_datei, neuer_datei_pfad)

                        # Arbeitsanweisung erstellen oder aktualisieren
                        if existiert:
                            anweisung = Arbeitsanweisung.objects.get(nummer=meta['nummer'])

                            # Alte Datei löschen
                            if anweisung.datei_pfad and os.path.exists(anweisung.datei_pfad):
                                try:
                                    os.remove(anweisung.datei_pfad)
                                except:
                                    pass

                            anweisung.name = meta['name']
                            anweisung.arbeitsplaetze = meta.get('arbeitsplaetze', [])
                            anweisung.kategorie = meta['kategorie']
                            anweisung.datei_pfad = neuer_datei_pfad
                            anweisung.save()
                            aktualisiert += 1
                        else:
                            anweisung = Arbeitsanweisung.objects.create(
                                nummer=meta['nummer'],
                                name=meta['name'],
                                arbeitsplaetze=meta.get('arbeitsplaetze', []),
                                kategorie=meta['kategorie'],
                                datei_pfad=neuer_datei_pfad
                            )
                            erstellt += 1

                    except Exception as e:
                        fehler += 1
                        print(f"Fehler beim Import von AA {meta['nummer']}: {str(e)}")

                # Erfolgsmeldung
                meldung_teile = []
                if erstellt > 0:
                    meldung_teile.append(f'{erstellt} neu erstellt')
                if aktualisiert > 0:
                    meldung_teile.append(f'{aktualisiert} aktualisiert')
                if uebersprungen > 0:
                    meldung_teile.append(f'{uebersprungen} übersprungen')
                if fehler > 0:
                    meldung_teile.append(f'{fehler} Fehler')

                if erstellt > 0 or aktualisiert > 0:
                    messages.success(request, f'Import abgeschlossen: {", ".join(meldung_teile)}')
                else:
                    messages.warning(request, f'Import abgeschlossen: {", ".join(meldung_teile)}')

                return redirect('arbeitsanweisung_liste')

            except json.JSONDecodeError:
                messages.error(request, 'Ungültiges Export-Archiv: JSON-Datei ist beschädigt.')
            except zipfile.BadZipFile:
                messages.error(request, 'Ungültige ZIP-Datei.')
            except Exception as e:
                messages.error(request, f'Fehler beim Import: {str(e)}')

            finally:
                # Temporäres Verzeichnis aufräumen
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

            return redirect('arbeitsanweisung_import')
    else:
        form = ArbeitsanweisungImportForm()

    context = {
        'form': form,
        'title': 'Arbeitsanweisungen importieren',
    }
    return render(request, 'arbeitsanweisungen/arbeitsanweisung_import.html', context)