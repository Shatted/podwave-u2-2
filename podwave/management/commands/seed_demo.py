"""
Comando de gestión: seed_demo — Unidad 2, parte 1.

Transforma los DATOS SIMULADOS de la Unidad 1 (estructuras de Python del
módulo podwave/datos_simulados.py) en REGISTROS PERSISTENTES de MySQL
(evidencia 8 de la rúbrica: "los datos simulados de la Unidad 1 comienzan
a transformarse en datos persistentes"):

  - GENEROS_SUGERIDOS (lista de tuplas)  ->  filas de la tabla Genre.
  - PISTAS_DEMO (lista de diccionarios)  ->  filas de la tabla Track
    (con su ForeignKey a Genre; usa el archivo local de media/audio/ si
    existe y si no cae a la URL pública).
  - LISTAS_DEMO (lista de diccionarios)  ->  filas de Playlist y de la
    tabla intermedia PlaylistTrack (relación N:M con campo order).

Uso:
    python manage.py seed_demo
    python manage.py seed_demo --password MiClaveDemo     # clave del user demo
    DJANGO_DEMO_PASSWORD=MiClaveDemo python manage.py seed_demo

El comando es IDEMPOTENTE: se puede ejecutar varias veces sin duplicar
datos (get_or_create en todos los pasos). Reemplaza al script seed_demo.py
de la raíz del proyecto (Unidad 1).

USUARIO DE PRUEBA (Unidad 2, parte 2): por omisión el usuario `demo` queda
con la contraseña FIJA `demo1234`, documentada en el README (credencial
EXCLUSIVAMENTE de prueba para que el docente evalúe el sistema; nunca una
clave personal). La clave se vuelve a fijar en cada corrida, así el
acceso de prueba siempre es reproducible. Se puede cambiar con
--password o DJANGO_DEMO_PASSWORD.
"""
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from podwave.datos_simulados import (
    GENEROS_SUGERIDOS, LISTAS_DEMO, PISTAS_DEMO,
)
from podwave.models import Genre, Playlist, PlaylistTrack, Track

# Contraseña por omisión del usuario de prueba `demo` (U2-2).
# Es una credencial de PRUEBA exclusivamente para la evaluación, no una
# clave real: se documenta abiertamente en el README.md (instrucción 9
# de la evaluación: proporcionar datos de acceso de un usuario de prueba).
PASSWORD_DEMO_POR_DEFECTO = 'demo1234'


class Command(BaseCommand):
    help = ('Puebla MySQL con los datos simulados de la Unidad 1: géneros, '
            'pistas y listas de reproducción (idempotente).')

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            help='Contraseña del usuario de prueba "demo" (por omisión: '
                 'demo1234, documentada en el README; también puede fijarse '
                 'con la variable DJANGO_DEMO_PASSWORD).')

    # --- Pasos del seed ---------------------------------------------------

    def _asegurar_usuario_demo(self, password):
        """Crea el usuario demo si no existe (dueño de los datos demo).

        U2-2: la contraseña se vuelve a fijar en CADA corrida. Así el
        acceso de prueba del docente es determinista (demo / demo1234 por
        omisión), sin importar en qué estado haya quedado la base.
        """
        user, creado = User.objects.get_or_create(
            username='demo',
            defaults={'first_name': 'Usuario', 'last_name': 'Demo'},
        )
        user.set_password(password)
        user.save(update_fields=['password'])
        return user, creado

    def _asegurar_generos(self):
        """GENEROS_SUGERIDOS (U1) -> tabla Genre."""
        creados = 0
        for valor, _etiqueta in GENEROS_SUGERIDOS:   # iteración sobre tuplas
            genre, creado = Genre.objects.get_or_create(name=valor)
            # save() del modelo genera el slug automáticamente si va vacío.
            if creado:
                genre.save()
                creados += 1
        return creados

    def _asegurar_pistas(self, demo_user):
        """PISTAS_DEMO (U1) -> tabla Track con ForeignKey a Genre."""
        creadas, locales = 0, 0
        for pista in PISTAS_DEMO:          # iteración sobre lista de dicts
            if Track.objects.filter(title=pista['title']).exists():
                continue
            # El género de la U1 se resuelve contra la tabla normalizada.
            genre, _creado = Genre.objects.get_or_create(name=pista['genre'])
            track = Track.objects.create(
                title=pista['title'],
                artist=pista['artist'],
                genre=genre,
                created_by=demo_user,
            )
            # Archivo local (media/audio/) si está disponible; si no, URL.
            existe_local = os.path.exists(os.path.join(
                str(settings.MEDIA_ROOT), 'audio', pista['filename']))
            if existe_local:
                track.audio_file.name = os.path.join(
                    'audio', pista['filename'])
                locales += 1
            else:
                track.url = pista['url']
            track.save()
            creadas += 1
        return creadas, locales

    def _asegurar_listas(self, demo_user):
        """LISTAS_DEMO (U2 sobre datos U1) -> Playlist + PlaylistTrack."""
        creadas, enlaces = 0, 0
        for lista in LISTAS_DEMO:
            playlist, creado = Playlist.objects.get_or_create(
                owner=demo_user, name=lista['name'],
                defaults={'description': lista.get('description', '')},
            )
            if creado:
                creadas += 1
            # Pistas de la lista en orden (1, 2, 3…): tabla intermedia N:M.
            for orden, title in enumerate(lista['tracks'], start=1):
                track = Track.objects.filter(title=title).first()
                if track is None:
                    continue
                _pt, creado = PlaylistTrack.objects.get_or_create(
                    playlist=playlist, track=track,
                    defaults={'order': orden},
                )
                if creado:
                    enlaces += 1
        return creadas, enlaces

    # --- Ejecución --------------------------------------------------------

    def handle(self, *args, **options):
        # Contraseña del usuario demo: flag > variable de entorno > fija
        # de prueba demo1234 (documentada en el README para el docente).
        password = (options['password']
                    or os.environ.get('DJANGO_DEMO_PASSWORD')
                    or PASSWORD_DEMO_POR_DEFECTO)
        clave_por_defecto = not (
            options['password'] or os.environ.get('DJANGO_DEMO_PASSWORD'))

        demo_user, usuario_creado = self._asegurar_usuario_demo(password)
        generos_creados = self._asegurar_generos()
        pistas_creadas, locales = self._asegurar_pistas(demo_user)
        listas_creadas, enlaces = self._asegurar_listas(demo_user)

        # Resumen para el operador (evidencia en consola del seed).
        self.stdout.write(self.style.SUCCESS(
            f'[+] Géneros: {Genre.objects.count()} en BD '
            f'({generos_creados} nuevos desde GENEROS_SUGERIDOS).'))
        self.stdout.write(self.style.SUCCESS(
            f'[+] Pistas: {Track.objects.count()} en BD '
            f'({pistas_creadas} nuevas desde PISTAS_DEMO; '
            f'{locales} con archivo local).'))
        self.stdout.write(self.style.SUCCESS(
            f'[+] Listas: {Playlist.objects.count()} en BD '
            f'({listas_creadas} nuevas) con {enlaces} pistas enlazadas '
            'vía PlaylistTrack.'))
        if usuario_creado:
            self.stdout.write('[i] Usuario de prueba "demo" creado.')
        else:
            self.stdout.write('[i] Usuario de prueba "demo" ya existía '
                              '(contraseña restaurada).')
        # La credencial de prueba se muestra abiertamente: no es una clave
        # personal sino el acceso de evaluación exigido por la instrucción 9.
        if clave_por_defecto:
            self.stdout.write(self.style.SUCCESS(
                '[i] Usuario de prueba: demo / demo1234 (documentado en '
                'el README.md).'))
        else:
            self.stdout.write('[i] Usuario de prueba: demo / (la contraseña '
                            'indicada con --password o DJANGO_DEMO_PASSWORD).')
        self.stdout.write(self.style.SUCCESS(
            '[+] Listo: los datos simulados de la Unidad 1 ya son registros '
            'persistentes en MySQL.'))


# Nombres de usuario/clave de demostración: la clave de PRUEBA por omisión
# (demo1234) vive aquí porque es una credencial de evaluación pública, no
# un secreto. Las credenciales REALES (MySQL, SECRET_KEY) siguen solo en
# variables de entorno (instrucción 9 de la evaluación).
