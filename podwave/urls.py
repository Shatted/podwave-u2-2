"""
URLs de la app PodWave.

Patrones de URL al estilo de la Unidad 2: cada vista genérica se conecta
a su ruta con as_view() y recibe un nombre para usar con la etiqueta
{% url 'nombre' %} en las plantillas.

Unidad 2, parte 2 (Evaluación Sumativa 3): se añade el CRUD COMPLETO de
las listas de reproducción desde el propio sitio web, sin depender de
Django Admin (criterio 3 de la Rúbrica A).
"""
from django.urls import path

from . import views

urlpatterns = [
    # --- PISTAS -----------------------------------------------------------
    # Read: biblioteca y detalle (públicas).
    path('tracks/', views.TrackListView.as_view(), name='track_list'),
    path('tracks/<int:pk>/', views.TrackDetailView.as_view(), name='track_detail'),
    # Create / Update / Delete (sesión iniciada + dueño de la pista).
    path('tracks/nueva/', views.TrackCreateView.as_view(), name='track_create'),
    path('tracks/<int:pk>/editar/', views.TrackUpdateView.as_view(), name='track_update'),
    path('tracks/<int:pk>/eliminar/', views.TrackDeleteView.as_view(), name='track_delete'),

    # --- LISTAS DE REPRODUCCIÓN (U2-2) ------------------------------------
    # Read: índice y detalle (públicos: consultar cualquier lista).
    path('playlists/', views.PlaylistListView.as_view(), name='playlist_list'),
    path('playlists/nueva/', views.PlaylistCreateView.as_view(), name='playlist_create'),
    path('playlists/<int:pk>/', views.PlaylistDetailView.as_view(), name='playlist_detail'),
    # Create / Update / Delete de la lista (sesión iniciada + dueño).
    path('playlists/<int:pk>/editar/', views.PlaylistUpdateView.as_view(), name='playlist_update'),
    path('playlists/<int:pk>/eliminar/', views.PlaylistDeleteView.as_view(), name='playlist_delete'),

    # Gestión de las pistas DENTRO de una lista (tabla intermedia N:M).
    # Acciones POST: crear enlace (agregar), eliminar (quitar) y actualizar
    # el orden (subir/bajar una posición).
    path('playlists/<int:pk>/quitar/<int:track_pk>/',
         views.playlist_remove_track, name='playlist_remove_track'),
    path('playlists/<int:pk>/mover/<int:track_pk>/<str:direccion>/',
         views.playlist_move_track, name='playlist_move_track'),
    # Agregar la pista <pk> a una de las listas del usuario (desde el
    # detalle de la pista, con select de las listas propias).
    path('tracks/<int:pk>/a-lista/', views.track_add_to_playlist,
         name='track_add_to_playlist'),
]
