"""
Modelos de la app PodWave — Unidad 2, parte 1 (MySQL).

Normalización de la persistencia sobre MySQL 8:

  - Genre: catálogo de géneros como TABLA propia. En la Unidad 1 el género
    era un CharField con choices; ahora es una ForeignKey (se evita
    repetir texto en cada fila y se puede gestionar desde el admin).
  - Track: pista de audio. Cambios respecto de U1: genre pasa a ser
    ForeignKey (on_delete=PROTECT: no se puede borrar un género con
    pistas asociadas) y se añade un slug único generado automáticamente.
  - Playlist: lista de reproducción por usuario (relación N:M con Track
    A TRAVÉS de PlaylistTrack, que añade el ORDEN de cada pista).
  - PlaylistTrack: tabla intermedia explícita de la relación N:M.

Migración de datos: podwave/migrations/0004_normaliza_genero_pistas.py
convierte los géneros que existían como texto (choices de la Unidad 1) en
filas de Genre y re-apunta cada pista a su género, sin perder datos.
"""
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Genre(models.Model):
    """
    Catálogo de géneros (tabla normalizada, Unidad 2).

    Reemplaza a los choices del CharField Track.genre de la Unidad 1:
    los mismos ocho géneros sugeridos viven ahora como filas de esta
    tabla (ver la migración de datos 0004 y el comando seed_demo).
    """
    name = models.CharField('nombre', max_length=40, unique=True)
    slug = models.SlugField('slug', max_length=50, unique=True)

    class Meta:
        ordering = ['name']           # orden alfabético en admin y plantillas
        verbose_name = 'género'
        verbose_name_plural = 'géneros'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # El slug se genera a partir del nombre si viene vacío: así lo
        # rellenan el admin (prepopulated_fields) y el comando seed_demo.
        if not self.slug:
            self.slug = slugify(self.name)[:50] or 'genero'
        super().save(*args, **kwargs)


class Track(models.Model):
    """
    Pista de audio de la biblioteca PodWave.

    Idéntica a la Unidad 1 salvo dos cambios de la Unidad 2:
      - genre es ahora una ForeignKey a Genre (on_delete=PROTECT).
      - slug: identificador legible único, generado automáticamente.

    Campos equivalentes a los de la SPA original (title, artist, url, genre),
    más auditoría (creado por / fecha) gracias al sistema de usuarios de
    Django (aprendizaje esperado U2: usuarios, roles y medidas básicas
    de seguridad).

    Fuente del audio (dos opciones, al menos una obligatoria):
      - audio_file: archivo subido por el usuario (se guarda en media/,
        se sirve localmente → reproducción inmediata)
      - url: enlace externo http(s):// directo al archivo de audio
    """
    title = models.CharField(
        'título', max_length=120, help_text='Ej: Entrevista con Ada Lovelace')
    artist = models.CharField(
        'artista / autor', max_length=80, help_text='Ej: Tech & Café Podcast')
    genre = models.ForeignKey(
        Genre,
        verbose_name='género',
        on_delete=models.PROTECT,     # no se borra un género con pistas
        related_name='tracks',        # genero.tracks -> pistas de ese género
    )
    slug = models.SlugField(
        'slug', max_length=140, unique=True, editable=False)

    # --- Fuente del audio: archivo subido Y/O enlace externo ---
    audio_file = models.FileField(
        'archivo de audio', upload_to='audio/', null=True, blank=True,
        help_text='Sube un archivo .mp3, .wav, .ogg, .m4a o .flac desde tu '
                  'computador (se reproduce localmente, sin demora).')
    url = models.URLField(
        'URL del audio', blank=True,
        help_text='Como alternativa: enlace http(s):// directo a un archivo '
                  'de audio (.mp3) alojado en internet.')

    # Auditoría: quién creó la pista y cuándo.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='creada por',
        on_delete=models.SET_NULL,   # si se elimina el usuario, la pista queda huérfana pero no se borra
        null=True, blank=True,
        related_name='pistas_creadas',
    )
    created_at = models.DateTimeField('creada el', auto_now_add=True)
    updated_at = models.DateTimeField('actualizada el', auto_now=True)

    class Meta:
        ordering = ['-created_at']   # las más recientes primero (como en la SPA)
        verbose_name = 'pista'
        verbose_name_plural = 'pistas'

    def __str__(self):
        return f'{self.title} — {self.artist}'

    def get_absolute_url(self):
        """URL canónica de la pista (DetailView)."""
        return reverse('track_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        # Slug único generado a partir del título (editable=False: nadie
        # lo escribe a mano). Si el título se repite, se numeran: -2, -3…
        if not self.slug:
            base = slugify(self.title)[:120] or 'pista'
            slug, sufijo = base, 2
            while Track.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{sufijo}'
                sufijo += 1
            self.slug = slug
        super().save(*args, **kwargs)

    # --- Utilidades para plantillas y reproductor ---

    @property
    def audio_url(self):
        """URL que reproduce el reproductor: prioriza el archivo local."""
        if self.audio_file:
            return self.audio_file.url
        return self.url or ''

    @property
    def is_local(self):
        """¿El audio se sirve desde media/ (local) o desde un enlace externo?"""
        return bool(self.audio_file)

    def clean(self):
        """Validación a nivel de modelo: exige al menos una fuente de audio."""
        super().clean()
        if not self.audio_file and not (self.url or '').strip():
            raise ValidationError(
                'Debes subir un archivo de audio o indicar una URL (al menos '
                'una de las dos opciones).')
        if self.audio_file:
            ext = os.path.splitext(self.audio_file.name)[1].lower()
            if ext not in settings.TRACK_ALLOWED_EXTENSIONS:
                raise ValidationError({
                    'audio_file': 'Formato no permitido. Usa uno de: %s.' % (
                        ', '.join(settings.TRACK_ALLOWED_EXTENSIONS))})


class Playlist(models.Model):
    """
    Lista de reproducción creada por un usuario (Unidad 2).

    La relación con las pistas es N:M (una lista tiene varias pistas y una
    pista puede estar en varias listas) A TRAVÉS de la tabla intermedia
    PlaylistTrack, que añade el ORDEN de cada pista dentro de la lista.
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='dueña / dueño',
        on_delete=models.CASCADE,    # sin dueño no tiene sentido la lista
        related_name='playlists',    # usuario.playlists -> sus listas
    )
    name = models.CharField('nombre', max_length=120)
    description = models.TextField('descripción', blank=True)
    tracks = models.ManyToManyField(
        Track,
        verbose_name='pistas',
        through='PlaylistTrack',     # tabla intermedia con campo "order"
        related_name='listas',       # pista.listas -> listas que la incluyen
        blank=True,
    )
    created_at = models.DateTimeField('creada el', auto_now_add=True)
    updated_at = models.DateTimeField('actualizada el', auto_now=True)

    class Meta:
        ordering = ['-created_at']   # las más recientes primero
        constraints = [
            # Un mismo usuario no puede repetir el nombre de una lista.
            models.UniqueConstraint(
                fields=['owner', 'name'],
                name='lista_unica_por_usuario',
            ),
        ]
        verbose_name = 'lista de reproducción'
        verbose_name_plural = 'listas de reproducción'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """URL canónica de la lista (DetailView, U2-2).

        CreateView y UpdateView redirigen aquí tras guardar, así el flujo
        queda en el detalle de la lista recién creada o editada.
        """
        return reverse('playlist_detail', kwargs={'pk': self.pk})

    def siguiente_orden(self):
        """Order que corresponde a una nueva pista: máximo actual + 1."""
        maximo = self.pistas.aggregate(maximo=models.Max('order'))['maximo']
        return (maximo or 0) + 1

    def renumerar_pistas(self):
        """
        Renumerar las pistas de la lista como 1..n sin huecos (U2-2).

        Se usa tras quitar una pista: los órdenes quedan consecutivos y las
        posiciones mostradas coinciden siempre con la realidad. Devuelve la
        cantidad de pistas de la lista.
        """
        posicion = 0
        for enlace in self.pistas.all():            # Meta.ordering = ['order']
            posicion += 1
            if enlace.order != posicion:
                PlaylistTrack.objects.filter(pk=enlace.pk).update(
                    order=posicion)
        return posicion


class PlaylistTrack(models.Model):
    """
    Tabla intermedia de la relación N:M Playlist ↔ Track (Unidad 2).

    Además de las dos claves foráneas, guarda el ORDEN de la pista dentro
    de la lista (1, 2, 3…), algo imposible con una M2M automática.
    """
    playlist = models.ForeignKey(
        Playlist,
        verbose_name='lista',
        on_delete=models.CASCADE,
        related_name='pistas',       # lista.pistas -> filas intermedias
    )
    track = models.ForeignKey(
        Track,
        verbose_name='pista',
        on_delete=models.CASCADE,
        related_name='enlaces',      # pista.enlaces -> listas que la incluyen
    )
    order = models.PositiveIntegerField('orden', default=1)

    class Meta:
        ordering = ['order']         # la lista se recorre en su orden
        constraints = [
            # La misma pista no se repite dentro de una lista…
            models.UniqueConstraint(
                fields=['playlist', 'track'],
                name='pista_unica_por_lista',
            ),
            # …y no hay dos pistas en la misma posición.
            models.UniqueConstraint(
                fields=['playlist', 'order'],
                name='orden_unico_por_lista',
            ),
        ]
        verbose_name = 'pista de la lista'
        verbose_name_plural = 'pistas de la lista'

    def __str__(self):
        return f'{self.order}. {self.track.title}'

    # --- Utilidades de orden (U2-2: gestión desde el sitio web) ---

    def mover(self, direccion):
        """
        Intercambia el orden de esta pista con su vecina (U2-2).

        direccion: 'arriba' (sube una posición) o 'abajo' (baja una).

        Devuelve True si hubo intercambio y False si ya estaba en el
        extremo de la lista (primera o última pista).

        El intercambio se hace en tres pasos (0 -> hueco temporal) para no
        violar el constraint `orden_unico_por_lista`: si se guardara la
        pista vecina con el orden de esta antes de liberarlo, MySQL
        rechazaría la fila duplicada.
        """
        if direccion == 'arriba':
            vecino = PlaylistTrack.objects.filter(
                playlist_id=self.playlist_id, order__lt=self.order,
            ).order_by('-order').first()
        elif direccion == 'abajo':
            vecino = PlaylistTrack.objects.filter(
                playlist_id=self.playlist_id, order__gt=self.order,
            ).order_by('order').first()
        else:
            raise ValueError("direccion debe ser 'arriba' o 'abajo'")
        if vecino is None:
            return False
        viejo, nuevo = self.order, vecino.order
        PlaylistTrack.objects.filter(pk=self.pk).update(order=0)      # hueco
        PlaylistTrack.objects.filter(pk=vecino.pk).update(order=viejo)
        PlaylistTrack.objects.filter(pk=self.pk).update(order=nuevo)
        self.order, vecino.order = nuevo, viejo
        return True
