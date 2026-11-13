"""
Vistas de la app pages (páginas estáticas del proyecto).

HomePageView muestra la portada de PodWave con estadísticas de la
biblioteca (portada estilo hero, equivalente al hero de la SPA original).
AboutPageView explica la migración React -> Django y la evolución del
proyecto a MySQL en la Unidad 2, incluida la etapa final (U2-2): CRUD de
pistas y listas desde el propio sitio.
"""
from django.views.generic import TemplateView

from podwave.models import Genre, Track


class HomePageView(TemplateView):
    """Portada de PodWave con estadísticas de la biblioteca.

    Unidad 2, parte 1: los géneros distintos se cuentan sobre la tabla
    normalizada Genre (antes: values('genre').distinct() sobre CharField).
    """
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_tracks'] = Track.objects.count()
        context['total_genres'] = Genre.objects.count()
        context['latest_tracks'] = Track.objects.order_by('-created_at')[:3]
        return context


class AboutPageView(TemplateView):
    """Página 'Acerca de' del proyecto."""
    template_name = 'about.html'
