from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Liste und Suche
    path('', views.arbeitsanweisung_liste, name='arbeitsanweisung_liste'),

    # Erstellen
    path('erstellen/', views.arbeitsanweisung_erstellen, name='arbeitsanweisung_erstellen'),

    # Detail, Bearbeiten, Löschen (mit nummer als Parameter)
    path('<int:nummer>/', views.arbeitsanweisung_detail, name='arbeitsanweisung_detail'),
    path('<int:nummer>/bearbeiten/', views.arbeitsanweisung_bearbeiten, name='arbeitsanweisung_bearbeiten'),
    path('<int:nummer>/loeschen/', views.arbeitsanweisung_loeschen, name='arbeitsanweisung_loeschen'),
    path('<int:nummer>/download/', views.arbeitsanweisung_datei_download, name='arbeitsanweisung_datei_download'),

    # Export / Import
    path('export/', views.arbeitsanweisung_export_all, name='arbeitsanweisung_export_all'),
    path('import/', views.arbeitsanweisung_import, name='arbeitsanweisung_import'),

    # Login / Logout
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='arbeitsanweisung_liste'), name='logout'),

    # Preview / Downloads
    path('arbeitsanweisungen/<int:nummer>/preview/', views.arbeitsanweisung_datei_preview, name='arbeitsanweisung_datei_preview'),

]