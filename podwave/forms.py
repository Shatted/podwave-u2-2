"""
Formularios de la app PodWave.

Formulario ModelForm basado en el modelo Track. Migran las validaciones que
en la SPA original (React) vivían en `src/utils/validators.js`:
  - título obligatorio, máx. 120 caracteres
  - artista obligatorio, máx. 80 caracteres
  - género obligatorio (Unidad 2: ahora un <select> con el catálogo de la
    tabla Genre, en lugar del texto libre con sugerencias de la Unidad 1)
  - fuente de audio obligatoria: archivo subido Y/O URL válida
    (solo http:// o https://)

En Django cada formulario se renderiza, valida y guarda de forma segura
(protección CSRF incluida), tal como se explica en la Unidad 2.

Unidad 2, parte 2 (Evaluación Sumativa 3): se añaden los formularios de
las LISTAS DE REPRODUCCIÓN para completar el CRUD de todas las entidades
principales desde las interfaces del propio sitio web:
  - PlaylistForm: crear y editar listas (nombre + descripción).
  - AddToPlaylistForm: selector de las listas del usuario para agregar
    una pista desde su página de detalle.
"""
import os

from django import forms
from django.conf import settings
from urllib.parse import urlsplit

from .models import Genre, Playlist, Track


class TrackForm(forms.ModelForm):
    """Formulario de creación y edición de pistas (Create/Update)."""

    class Meta:
        model = Track
        fields = ['title', 'artist', 'genre', 'audio_file', 'url']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Ej: Entrevista con Ada Lovelace',
                'autofocus': True,
            }),
            'artist': forms.TextInput(attrs={
                'placeholder': 'Ej: Tech & Café Podcast',
            }),
            # genre: al ser ForeignKey, Django genera automáticamente un
            # ModelChoiceField (un <select> con los géneros de la tabla).
            'url': forms.URLInput(attrs={
                'placeholder': 'https://ejemplo.com/podcast/episodio.mp3',
                'inputmode': 'url',
            }),
            'audio_file': forms.ClearableFileInput(attrs={
                'accept': 'audio/*,.mp3,.wav,.ogg,.m4a,.flac',
            }),
        }

    def clean_title(self):
        """Equivalente a la validación de título de validators.js."""
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError('El título es obligatorio.')
        if len(title) > 120:
            raise forms.ValidationError(
                'El título no puede superar los 120 caracteres.')
        return title

    def clean_artist(self):
        """Equivalente a la validación de artista de validators.js."""
        artist = self.cleaned_data.get('artist', '').strip()
        if not artist:
            raise forms.ValidationError('El artista es obligatorio.')
        if len(artist) > 80:
            raise forms.ValidationError(
                'El artista no puede superar los 80 caracteres.')
        return artist

    def clean_genre(self):
        """
        El género es obligatorio (Unidad 2: instancia de Genre del select).
        ModelChoiceField ya valida que exista; aquí solo refuerza el mensaje
        en español para el caso del campo vacío.
        """
        genre = self.cleaned_data.get('genre')
        if not genre:
            raise forms.ValidationError('El género es obligatorio.')
        return genre

    def clean_audio_file(self):
        """
        Validación del archivo subido: extensión de audio permitida y
        tamaño máximo razonable (protege al servidor de subidas abusivas).
        """
        f = self.cleaned_data.get('audio_file')
        if not f or not f.name:
            return f
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in settings.TRACK_ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                'Formato no permitido (%(ext)s). Usa uno de: %(allowed)s.',
                code='invalid_extension',
                params={'ext': ext,
                        'allowed': ', '.join(settings.TRACK_ALLOWED_EXTENSIONS)})
        if f.size and f.size > settings.TRACK_MAX_FILE_BYTES:
            raise forms.ValidationError(
                'El archivo supera el máximo de %(max_mb)d MB.',
                code='too_large',
                params={'max_mb': settings.TRACK_MAX_FILE_BYTES // (1024 * 1024)})
        return f

    def clean_url(self):
        """
        Validación segura de la URL de audio (opcional si se subió archivo).
        Solo se permiten esquemas http:// y https:// (se bloquean
        javascript:, data: y file:), igual que isValidAudioUrl() en React.
        """
        url = (self.cleaned_data.get('url') or '').strip()
        if not url:
            return url
        scheme = urlsplit(url).scheme.lower()
        if scheme not in ('http', 'https'):
            raise forms.ValidationError(
                'La URL no es válida. Debe comenzar con http:// o https:// '
                'y tener un dominio correcto.')
        return url

    def clean(self):
        """Exige al menos una fuente de audio: archivo o URL."""
        cleaned = super().clean()
        has_file = bool(self.cleaned_data.get('audio_file'))
        has_url = bool((self.cleaned_data.get('url') or '').strip())
        if not has_file and not has_url:
            raise forms.ValidationError(
                'Sube un archivo de audio o escribe una URL: al menos una de '
                'las dos opciones es obligatoria.')
        return cleaned


class PlaylistForm(forms.ModelForm):
    """
    Formulario de creación y edición de listas de reproducción (U2-2).

    Solo expone name y description: las pistas de la lista se gestionan
    desde el detalle de la propia lista (agregar / quitar / reordenar),
    porque la relación N:M vive en PlaylistTrack con su campo order.
    El dueño (owner) lo fija la vista a partir de la sesión, nunca el
    formulario: así un usuario no puede crear listas a nombre de otro.
    """

    class Meta:
        model = Playlist
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Ej: Estudiar sin distracciones',
                'autofocus': True,
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Describe el propósito de la lista (opcional).',
                'rows': 3,
            }),
        }

    def clean_name(self):
        """Nombre obligatorio y dentro del máximo del modelo (120)."""
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('El nombre de la lista es obligatorio.')
        if len(name) > 120:
            raise forms.ValidationError(
                'El nombre no puede superar los 120 caracteres.')
        return name


class AddToPlaylistForm(forms.Form):
    """
    Selector de las listas del usuario para agregar una pista (U2-2).

    Se usa en el detalle de una pista: el <select> solo ofrece las listas
    de las que es dueño el usuario autenticado (control de acceso por
    propiedad, criterio 6 de la Rúbrica A).
    """

    playlist = forms.ModelChoiceField(
        queryset=Playlist.objects.none(),
        label='Lista de reproducción',
        empty_label='Elige una de tus listas…',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo las listas PROPIAS del usuario (el queryset se inyecta aquí
        # para que el campo valide también en el lado del servidor).
        if user is not None and user.is_authenticated:
            self.fields['playlist'].queryset = Playlist.objects.filter(
                owner=user).order_by('name')
