"""
App de configuración de PodWave.

App encargada del CRUD de pistas de audio (podcasts) sobre la base
de datos, según el patrón MVT de Django (Unidad 1 y Unidad 2).
"""
from django.apps import AppConfig


class PodwaveConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'podwave'
    verbose_name = 'PodWave — Biblioteca de podcasts'
