"""
Vistas de la app PodWave.

CRUD completo sobre la base de datos usando Vistas Genéricas Basadas en
Clases (GCBV), tal como se estudia en la Unidad 2 (sistema de blog):

  PISTAS (entidad principal, Unidad 2 parte 1):
  - ListView   -> biblioteca de pistas (pública)
  - DetailView -> detalle + reproductor (pública)
  - CreateView -> agregar pista (requiere sesión iniciada)
  - UpdateView -> editar pista (requiere sesión iniciada + ser el dueño)
  - DeleteView -> eliminar pista (requiere sesión iniciada + ser el dueño)

  LISTAS DE REPRODUCCIÓN (entidad principal, Unidad 2 parte 2 / Evaluación
  Sumativa 3): CRUD completo desde el sitio web, sin depender de Django
  Admin:
  - PlaylistListView   -> consultar todas las listas (pública)
  - PlaylistDetailView -> consultar una lista y sus pistas ordenadas (pública)
  - PlaylistCreateView -> crear lista (requiere sesión iniciada)
  - PlaylistUpdateView -> editar nombre/descripción (dueño de la lista)
  - PlaylistDeleteView -> eliminar lista (dueño de la lista)
  - track_add_to_playlist    -> agregar una pista a una lista propia (C de
    PlaylistTrack, con orden automático al final)
  - playlist_remove_track    -> quitar una pista de la lista (D de
    PlaylistTrack, renumerando el orden)
  - playlist_move_track       -> subir/bajar una pista dentro de la lista
    (U del orden de PlaylistTrack)

LoginRequiredMixin + control de propiedad responden al aprendizaje esperado
de la Unidad 2 y a la instrucción 7 de la Evaluación Sumativa 3: restringir
el acceso a las funcionalidades según los usuarios o roles definidos. Los
mensajes del framework `messages` dan la retroalimentación de cada
operación (instrucción 6: mensajes de confirmación o error).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .datos_simulados import resumen_por_genero
from .forms import AddToPlaylistForm, PlaylistForm, TrackForm
from .models import Genre, Playlist, PlaylistTrack, Track


# ---------------------------------------------------------------------------
# PISTAS (Track): CRUD desde el sitio (Unidad 2 parte 1, mantenido)
# ---------------------------------------------------------------------------

class TrackListView(ListView):
    """Biblioteca pública de pistas (Read del CRUD).

    Incluye un FILTRO POR GÉNERO construido sobre la tabla Genre (Unidad
    2: catálogo normalizado): el parámetro ?genero=<slug> se lee desde la
    URL (variable), se valida con una decisión y viaja al Template
    mediante el contexto de la View.
    """
    model = Track
    template_name = 'podwave/track_list.html'
    context_object_name = 'tracks'
    paginate_by = 6

    def get_queryset(self):
        queryset = super().get_queryset().select_related('genre')
        genero = (self.request.GET.get('genero') or '').strip()  # variable
        if genero:                                              # decisión
            queryset = queryset.filter(genre__slug=genero)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Estadísticas para la portada de la biblioteca (equivale al
        # contador de pistas del Navbar de la SPA original).
        context['total_tracks'] = Track.objects.count()
        context['total_genres'] = Genre.objects.count()
        context['latest_tracks'] = Track.objects.order_by('-created_at')[:4]
        # Filtro por género: el catálogo ahora vive en la tabla Genre y
        # llega al Template mediante el contexto (separación MVT).
        context['generos'] = Genre.objects.all()
        context['genero_activo'] = (self.request.GET.get('genero') or '').strip()
        # Resumen por género calculado con la función del módulo de datos
        # simulados (iteraciones y decisiones sobre una lista de dicts).
        pistas = list(
            Track.objects.values('title', 'artist')
                         .annotate(genero_nombre=F('genre__name')))
        for pista in pistas:
            pista['genre'] = pista.pop('genero_nombre')
        context['resumen_generos'] = resumen_por_genero(pistas)
        return context


class TrackDetailView(DetailView):
    """Detalle de una pista con su reproductor (Read del CRUD)."""
    model = Track
    template_name = 'podwave/track_detail.html'
    context_object_name = 'track'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        track = self.object
        if self.request.user.is_authenticated:
            # U2-2: formulario para agregar la pista a una lista propia y
            # listas propias que ya la contienen (para quitarla directo).
            context['add_to_playlist_form'] = AddToPlaylistForm(
                user=self.request.user)
            context['listas_propias'] = Playlist.objects.filter(
                owner=self.request.user).order_by('name')
            context['listas_propias_con_pista'] = track.listas.filter(
                owner=self.request.user).order_by('name')
        return context


class TrackCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Agregar una nueva pista (Create del CRUD). Requiere sesión iniciada.

    SuccessMessageMixin (U2-2): confirma la operación con un mensaje que
    muestra el framework `messages` tras el redirect.
    """
    model = Track
    form_class = TrackForm
    template_name = 'podwave/track_form.html'
    success_message = 'Pista «%(title)s» agregada a la biblioteca.'

    def form_valid(self, form):
        # Asocia la pista al usuario autenticado (sesión de validación).
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class TrackUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Editar una pista existente (Update del CRUD). Requiere sesión.

    U2-2 — CONTROL DE ACCESO POR PROPIEDAD: get_queryset() solo devuelve
    las pistas creadas por el usuario autenticado. Si intenta editar la
    pista de otro usuario (p.ej. /tracks/7/editar/), la vista responde
    404 en lugar de mostrar el formulario (instrucción 7 de la
    evaluación). El superusuario mantiene acceso total, coherente con su
    rol definido en el proyecto.
    """
    model = Track
    form_class = TrackForm
    template_name = 'podwave/track_form.html'
    success_message = 'Pista «%(title)s» actualizada correctamente.'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Track.objects.all()
        return Track.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True  # cambia textos del template (crear/editar)
        return context


class TrackDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """Eliminar una pista con confirmación (Delete del CRUD).

    En Django 5.2 BaseDeleteView.post() pasa por form_valid(), así que
    SuccessMessageMixin funciona también en DeleteView: el mensaje se
    agrega justo antes de borrar y se muestra tras el redirect.
    Solo el dueño de la pista (o un superusuario) puede eliminarla.
    """
    model = Track
    template_name = 'podwave/track_confirm_delete.html'
    success_url = reverse_lazy('track_list')
    success_message = 'Pista eliminada de la biblioteca.'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Track.objects.all()
        return Track.objects.filter(created_by=self.request.user)


# ---------------------------------------------------------------------------
# LISTAS DE REPRODUCCIÓN (Playlist): CRUD completo desde el sitio (U2-2)
# ---------------------------------------------------------------------------

class PlaylistListView(ListView):
    """Índice público de listas de reproducción (Read del CRUD)."""
    model = Playlist
    template_name = 'podwave/playlist_list.html'
    context_object_name = 'playlists'
    paginate_by = 6

    def get_queryset(self):
        # num_pistas por lista en la misma consulta (sin N+1).
        return (Playlist.objects.select_related('owner')
                                .annotate(num_pistas=Count('pistas'))
                                .order_by('-created_at'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_playlists'] = Playlist.objects.count()
        return context


class PlaylistDetailView(DetailView):
    """Detalle de una lista: pistas en orden + gestión para el dueño.

    Pública (cualquiera puede consultar), pero los botones de gestión
    (reordenar / quitar / editar / eliminar) solo se renderizan para el
    dueño de la lista (es_dueno en el contexto) y las vistas de acción
    vuelven a verificar la propiedad en el servidor.
    """
    model = Playlist
    template_name = 'podwave/playlist_detail.html'
    context_object_name = 'playlist'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enlaces'] = (
            self.object.pistas.select_related('track', 'track__genre'))
        context['es_dueno'] = (
            self.request.user.is_authenticated
            and self.request.user == self.object.owner)
        return context


class PlaylistCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Crear una lista de reproducción (Create del CRUD). Requiere sesión."""
    model = Playlist
    form_class = PlaylistForm
    template_name = 'podwave/playlist_form.html'
    success_message = ('Lista «%(name)s» creada: agrégale pistas desde su '
                      'detalle o desde la página de cada pista.')

    def form_valid(self, form):
        # El dueño sale de la SESIÓN, nunca del formulario: un usuario no
        # puede crear listas a nombre de otro (control de acceso).
        form.instance.owner = self.request.user
        return super().form_valid(form)


class PlaylistUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Editar una lista (Update del CRUD). Solo su dueño."""
    model = Playlist
    form_class = PlaylistForm
    template_name = 'podwave/playlist_form.html'
    success_message = 'Lista «%(name)s» actualizada correctamente.'

    def get_queryset(self):
        return Playlist.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context


class PlaylistDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """Eliminar una lista (Delete del CRUD). Solo su dueño.

    Al eliminar la Playlist, el CASCADE de la FK borra también sus filas
    de PlaylistTrack (la tabla intermedia); las PISTAS no se tocan.
    """
    model = Playlist
    template_name = 'podwave/playlist_confirm_delete.html'
    success_url = reverse_lazy('playlist_list')
    success_message = 'Lista eliminada (las pistas siguen en la biblioteca).'

    def get_queryset(self):
        return Playlist.objects.filter(owner=self.request.user)


# ---------------------------------------------------------------------------
# Gestión de las pistas DENTRO de una lista (tabla intermedia N:M, U2-2)
# ---------------------------------------------------------------------------

@login_required
@require_POST
def track_add_to_playlist(request, pk):
    """Agregar la pista <pk> a una de las listas propias del usuario.

    Create de PlaylistTrack: el orden se asigna automáticamente al final
    (máximo actual + 1, ver Playlist.siguiente_orden). El formulario
    valida en el servidor que la lista elegida pertenezca al usuario.
    """
    track = get_object_or_404(Track, pk=pk)
    form = AddToPlaylistForm(request.POST, user=request.user)
    if form.is_valid():
        playlist = form.cleaned_data['playlist']
        enlace, creado = PlaylistTrack.objects.get_or_create(
            playlist=playlist, track=track,
            defaults={'order': playlist.siguiente_orden()},
        )
        if creado:
            messages.success(
                request,
                f'Pista «{track.title}» agregada a la lista '
                f'«{playlist.name}» (posición {enlace.order}).')
        else:
            messages.info(
                request,
                f'La pista «{track.title}» ya estaba en la lista '
                f'«{playlist.name}».')
    else:
        messages.error(
            request,
            'No se pudo agregar la pista: elige una lista válida de las '
            'que administras.')
    return redirect(track)


@login_required
@require_POST
def playlist_remove_track(request, pk, track_pk):
    """Quitar la pista <track_pk> de la lista <pk> (solo el dueño).

    Delete de PlaylistTrack: tras quitarla se renumeran las posiciones
    (1..n) para que no queden huecos en el orden.
    """
    playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
    enlace = get_object_or_404(
        PlaylistTrack, playlist=playlist, track_id=track_pk)
    titulo = enlace.track.title
    enlace.delete()
    playlist.renumerar_pistas()
    messages.success(
        request,
        f'Pista «{titulo}» quitada de la lista «{playlist.name}». Las '
        'posiciones fueron renumeradas.')
    return redirect(playlist)


@login_required
@require_POST
def playlist_move_track(request, pk, track_pk, direccion):
    """Subir o bajar una pista dentro de la lista <pk> (solo el dueño).

    Update del orden de PlaylistTrack: intercambia posiciones con la
    pista vecina de forma segura (PlaylistTrack.mover).
    """
    if direccion not in ('arriba', 'abajo'):
        raise Http404('Dirección inválida.')
    playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
    enlace = get_object_or_404(
        PlaylistTrack, playlist=playlist, track_id=track_pk)
    if enlace.mover(direccion):
        messages.success(
            request,
            f'«{enlace.track.title}» ahora está en la posición '
            f'{enlace.order} de la lista «{playlist.name}».')
    else:
        messages.info(
            request,
            f'«{enlace.track.title}» ya está en el extremo de la lista: '
            'no hay más pistas en esa dirección.')
    return redirect(playlist)
