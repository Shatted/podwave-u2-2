"""
Registro de los modelos en el administrador de Django — Unidad 2, parte 1.

Los cuatro modelos (Genre, Track, Playlist, PlaylistTrack) quedan
gestionables desde /admin/ sin escribir SQL, con:
  - list_display / list_filter / search_fields en todos los modelos
  - prepopulated_fields (slug del género)
  - date_hierarchy en Track y Playlist
  - fieldsets en Track
  - inline de PlaylistTrack dentro de Playlist (la relación N:M es
    `through`, por lo que NO se puede usar filter_horizontal: Django
    lanza admin.E013; el inline cumple el mismo rol y además permite
    editar el orden de cada pista).
"""
from django.contrib import admin

from .models import Genre, Playlist, PlaylistTrack, Track

# Encabezados del panel en español (evidencia visual para la defensa).
admin.site.site_header = 'Administración PodWave'
admin.site.site_title = 'PodWave Admin'
admin.site.index_title = 'Gestión de la plataforma de podcasts'


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    """Catálogo de géneros: pequeño y con el slug pre-poblado."""
    list_display = ('name', 'slug', 'total_pistas')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}   # se completa al escribir

    @admin.display(description='Nº de pistas')
    def total_pistas(self, obj):
        """Cuantas pistas usan este género (related_name='tracks')."""
        return obj.tracks.count()


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    """Pistas de la biblioteca: el modelo principal del CRUD."""
    list_display = ('title', 'artist', 'genre', 'has_audio_file',
                    'created_by', 'created_at')
    list_filter = ('genre', 'created_at', 'created_by')
    search_fields = ('title', 'artist', 'genre__name')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Datos de la pista', {
            'fields': ('title', 'artist', 'genre', 'audio_file', 'url'),
        }),
        ('Auditoría', {
            'fields': ('slug', 'created_by', 'created_at', 'updated_at'),
        }),
    )

    @admin.display(boolean=True, description='Archivo local')
    def has_audio_file(self, obj):
        return bool(obj.audio_file)


class PlaylistTrackInline(admin.TabularInline):
    """
    Pistas dentro de una lista, con su orden (tabla intermedia N:M).

    Se usa inline y NO filter_horizontal en PlaylistAdmin porque la
    relación usa through=PlaylistTrack y Django lanza admin.E013.
    """
    model = PlaylistTrack
    extra = 1
    fields = ('track', 'order')


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    """Listas de reproducción con sus pistas (inline) y dueño."""
    list_display = ('name', 'owner', 'total_pistas', 'created_at')
    list_filter = ('owner',)
    search_fields = ('name', 'owner__username')
    date_hierarchy = 'created_at'
    inlines = (PlaylistTrackInline,)

    @admin.display(description='Nº de pistas')
    def total_pistas(self, obj):
        """Cuantas pistas hay en la lista (related_name='pistas')."""
        return obj.pistas.count()


@admin.register(PlaylistTrack)
class PlaylistTrackAdmin(admin.ModelAdmin):
    """
    Tabla intermedia N:M, también gestionable de forma directa.

    El camino principal para editarla es el inline dentro de Playlist;
    este registro permite ver y buscar TODOS los enlaces pista-lista de
    la base de datos de una sola vez (evidencia de la relación N:M).
    """
    list_display = ('playlist', 'track', 'order')
    list_filter = ('playlist',)
    search_fields = ('playlist__name', 'track__title')
    ordering = ('playlist__name', 'order')
