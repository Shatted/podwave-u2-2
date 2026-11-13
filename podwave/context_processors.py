"""
Context processor de PodWave.

Inyecta el contador de pistas en TODAS las plantillas del proyecto (disponible
como {{ total_tracks }}), de modo que el navbar pueda mostrar la cantidad de
pistas en cualquier página, no solo en las vistas que calculan estadísticas.
Es el patrón recomendado de Django para datos globales de plantilla.
"""
from .models import Track


def track_counter(request):
    """Contador global de pistas para el navbar."""
    return {'total_tracks': Track.objects.count()}
